"""Demo sessions: atomic admission, proven replay, scoped reset and purge."""

import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from app.assets.service.service import AssetService
from app.core.clock import wall_now
from app.core.errors.base import NotFoundError, RequestInvalidError
from app.core.settings import Settings
from app.demo.model.models import CreateOperationModel, DemoSessionModel
from app.demo.repository.base_repository import DemoRepository
from app.demo.scenarios import SCENARIOS, Scenario, ScenarioPlan, build_scenario
from app.demo.service.errors import (
    DemoCapacityError,
    ReplayConflictError,
    ReplayProofMismatchError,
    ScenarioUnknownError,
    SessionExpiredError,
)
from app.demo.service.seed import seed
from app.demo.service.tokens import OPERATION_ID, REPLAY_PROOF, derive_token, digest
from app.identity.model.models import PrincipalKind, PrincipalModel
from app.identity.service.service import PrincipalService
from app.measurements.service.service import IngestService
from app.scope.service.selection import SelectionService
from app.sites.model.models import SiteKind
from app.sites.service.service import SiteService

_KEY_FORMAT = "Kunci permintaan demo tidak valid. Buat kunci acak baru lalu coba lagi."


@dataclass(frozen=True)
class DemoSessionResult:
    """A created or replayed session and its token."""

    token: str
    response: dict[str, Any]
    replayed: bool


def _scenario(scenario_id: str) -> ScenarioPlan:
    try:
        return build_scenario(scenario_id)
    except NotFoundError as error:
        raise ScenarioUnknownError(error=error) from error


class DemoService:
    """Turns scenarios into isolated, expiring demo workspaces."""

    def __init__(
        self,
        repository: DemoRepository,
        *,
        sites: SiteService,
        principals: PrincipalService,
        assets: AssetService,
        ingest: IngestService,
        selections: SelectionService,
        settings: Settings,
    ) -> None:
        """Bind to storage and the services a workspace spans.

        Args:
            repository (DemoRepository): Demo storage.
            sites (SiteService): Sites, locks and revisions.
            principals (PrincipalService): Principal lifecycle.
            assets (AssetService): Asset model.
            ingest (IngestService): Shared ingestion.
            selections (SelectionService): Confirmed scope.
            settings (Settings): Limits, TTL and keys.
        """
        self.repository = repository
        self.sites = sites
        self.principals = principals
        self.assets = assets
        self.ingest = ingest
        self.selections = selections
        self.settings = settings

    @staticmethod
    def scenarios() -> tuple[Scenario, ...]:
        """Return the catalog.

        Returns:
            tuple[Scenario, ...]: Every scenario.
        """
        return SCENARIOS

    async def create(self, scenario_id: str, operation_id: str, replay_proof: str) -> DemoSessionResult:
        """Admit and seed a new session, or recover one whose response was lost.

        Args:
            scenario_id (str): The scenario.
            operation_id (str): The client's ``Idempotency-Key``.
            replay_proof (str): The client's separate replay proof.

        Returns:
            DemoSessionResult: Token and response, flagged when replayed.

        Raises:
            RequestInvalidError: When the key or proof is too short to be random.
            ScenarioUnknownError: For an unknown scenario.
            ReplayProofMismatchError: For a known operation without its proof.
            ReplayConflictError: For a proven replay that cannot be honoured.
            DemoCapacityError: When no slot or budget remains.
        """
        if not OPERATION_ID.fullmatch(operation_id) or not REPLAY_PROOF.fullmatch(replay_proof):
            raise RequestInvalidError(_KEY_FORMAT)
        plan = _scenario(scenario_id)
        now = wall_now()
        await self.repository.lock_admission()

        existing = await self.repository.get_operation(operation_id)
        if existing is not None:
            return await self._replay(existing, scenario_id, operation_id, replay_proof, now)

        await self._purge(now)
        if await self.repository.count_active(now) >= self.settings.demo_max_active_sessions:
            raise DemoCapacityError()
        if (
            await self.repository.count_created_since(now - timedelta(minutes=1))
            >= self.settings.demo_create_max_per_minute
        ):
            raise DemoCapacityError()

        principal = await self.principals.create(PrincipalKind.DEMO)
        site = await self.sites.create(
            principal,
            kind=SiteKind.DEMO,
            name=plan.site_name,
            context=plan.context,
            timezone=plan.timezone,
            virtual_now=plan.virtual_now,
        )
        site = await self.sites.lock(site.id)
        await seed(plan, site, sites=self.sites, assets=self.assets, ingest=self.ingest, received_at=now)
        session = DemoSessionModel(
            id=uuid4(),
            principal_id=principal.id,
            site_id=site.id,
            scenario_id=scenario_id,
            key_version=self.settings.demo_token_key_version,
            expires_at=now + timedelta(hours=self.settings.demo_session_ttl_hours),
        )
        token = self._token(session.key_version, session.id, operation_id, replay_proof)
        await self.repository.add_session(session, digest(token))
        response = self._workspace(session, plan)
        await self.repository.add_operation(
            CreateOperationModel(
                operation_id=operation_id,
                session_id=session.id,
                scenario_id=scenario_id,
                replay_proof_hash=digest(replay_proof),
                key_version=session.key_version,
                response=response,
                replay_expires_at=now + timedelta(seconds=self.settings.demo_create_replay_seconds),
                retain_until=session.expires_at,  # A late retry can never recreate an ended session.
            )
        )
        return DemoSessionResult(token=token, response=response, replayed=False)

    async def current(self, principal: PrincipalModel) -> DemoSessionModel:
        """Return the caller's live session.

        Args:
            principal (PrincipalModel): The acting principal.

        Returns:
            DemoSessionModel: The session.

        Raises:
            NotFoundError: When the principal has no demo session.
            SessionExpiredError: When it has expired.
        """
        session = await self.repository.session_for_principal(principal.id)
        if session is None:
            raise NotFoundError()
        if session.expires_at <= wall_now():
            raise SessionExpiredError()
        return session

    async def reset(self, principal: PrincipalModel) -> dict[str, Any]:
        """Return the caller's workspace to its scenario start, keeping token, site and expiry.

        Args:
            principal (PrincipalModel): The acting principal.

        Returns:
            dict[str, Any]: The workspace description.
        """
        session = await self.current(principal)
        site = await self.sites.lock_owned(session.site_id, principal)
        session = await self.current(principal)  # Revalidate under the lock.
        plan = _scenario(session.scenario_id)
        await self.selections.clear(site.id)
        await self.assets.clear(site)
        site = await self.sites.restore(
            site, name=plan.site_name, context=plan.context.value, timezone=plan.timezone, virtual_now=plan.virtual_now
        )
        await seed(plan, site, sites=self.sites, assets=self.assets, ingest=self.ingest, received_at=wall_now())
        if not plan.assets:
            await self.sites.advance_binding_revision(site)
            await self.sites.advance_measurement_revision(site)
        return self._workspace(session, plan)

    async def end(self, principal: PrincipalModel) -> None:
        """End the caller's session and delete its workspace and principal. The operation record stays.

        Args:
            principal (PrincipalModel): The acting principal.
        """
        session = await self.repository.session_for_principal(principal.id)
        if session is None:
            raise NotFoundError()
        await self.sites.lock_owned(session.site_id, principal)
        await self.sites.delete([session.site_id])
        await self.principals.delete([session.principal_id])

    async def resolve(self, token: str) -> PrincipalModel | None:
        """Map a demo bearer token to its principal.

        Args:
            token (str): The bearer token.

        Returns:
            PrincipalModel | None: The principal, or None when the token is unknown or purged.

        Raises:
            SessionExpiredError: When the token's session is known but expired.
        """
        session = await self.repository.session_for_token(digest(token))
        if session is None:
            return None
        if session.expires_at <= wall_now():
            raise SessionExpiredError()
        return PrincipalModel(id=session.principal_id, kind=PrincipalKind.DEMO)

    async def _replay(
        self, operation: CreateOperationModel, scenario_id: str, operation_id: str, replay_proof: str, now: datetime
    ) -> DemoSessionResult:
        if not hmac.compare_digest(operation.replay_proof_hash, digest(replay_proof)):
            raise ReplayProofMismatchError()
        if operation.scenario_id != scenario_id or operation.session_id is None or now > operation.replay_expires_at:
            raise ReplayConflictError()
        session = await self.repository.get_session(operation.session_id)
        if session is None or session.expires_at <= now or operation.key_version not in self.settings.demo_token_keys:
            raise ReplayConflictError()
        token = self._token(operation.key_version, session.id, operation_id, replay_proof)
        return DemoSessionResult(token=token, response=operation.response, replayed=True)

    async def _purge(self, now: datetime) -> None:
        expired = await self.repository.expired_sessions(now)
        if expired:
            await self.sites.delete([session.site_id for session in expired])
            await self.principals.delete([session.principal_id for session in expired])
        await self.repository.delete_operations_retained_until(now)

    def _token(self, key_version: str, session_id: UUID, operation_id: str, replay_proof: str) -> str:
        key = self.settings.demo_token_keys[key_version].get_secret_value().encode()
        return derive_token(key, key_version, session_id, operation_id, replay_proof)

    @staticmethod
    def _workspace(session: DemoSessionModel, plan: ScenarioPlan) -> dict[str, Any]:
        return {
            "site_id": str(session.site_id),
            "scenario_id": session.scenario_id,
            "expires_at": session.expires_at.isoformat(),
            "initial_period": dict(plan.initial_period),
        }
