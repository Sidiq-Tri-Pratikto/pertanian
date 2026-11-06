"""Build a synthetic-only dataset through TemuRiset services and issue one session per actor."""

import argparse
import asyncio
import json
import os
import re
import stat
from contextlib import suppress
from pathlib import Path
from typing import TextIO
from urllib.parse import urlsplit
from uuid import UUID

import httpx
from pydantic import BaseModel, SecretStr
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import clock
from app.core.database import get_engine, get_session_factory, seeded_ids
from app.core.settings import get_settings
from app.demo.service import data
from app.demo.service.fixtures import demo_email
from app.discovery.repository.sqlalchemy.models import SearchDocumentRecord
from app.identity.model.models import Principal
from app.identity.repository.sqlalchemy.models import AccountRecord, SessionRecord
from app.identity.service.service import create_demo_account, start_demo_session
from app.intake.model.schema import CreateOpportunityRequest, OpportunityTransitionRequest, SavePartnerProfileRequest
from app.intake.repository.sqlalchemy.models import OpportunityRecord
from app.intake.service.service import IntakeService
from app.needs.model.schema import CreateSupportRequest, TransitionRequest
from app.needs.service.service import NeedsService
from app.platform.repository.sqlalchemy.models import OutboxEventRecord
from app.portfolio.model.schema import CreateInventionRequest, DraftRequest, VersionedActionRequest
from app.portfolio.repository.sqlalchemy.models import InventionRecord
from app.portfolio.service.service import PortfolioService

LOOPBACK = {"localhost", "127.0.0.1", "::1"}
PREFIX = "Benchmark sintetis"
VISIBILITY_TERM = "temurisetprobe"


class BenchmarkError(RuntimeError):
    """A target, dataset or workload failed benchmark validation."""


class Actor(BaseModel):
    """Cookie and the expected identity and owned portfolio for one virtual user."""

    token: SecretStr
    account_id: UUID
    party_id: UUID
    inventions: list[UUID]


class Dataset(BaseModel):
    """Private handoff between the generator and HTTP runner."""

    origin: str
    database: str
    actors: list[Actor]
    opportunity_ids: set[UUID]
    partner_ids: set[UUID]
    source_id: UUID


def target(origin: str, *, staging: bool) -> str:
    """Require a selected isolated database and origin before using either target."""
    settings = get_settings()
    parsed = urlsplit(origin)
    expected_scheme = "https" if staging else "http"
    database = make_url(settings.database_url.get_secret_value())
    if (
        origin != os.environ.get("BENCHMARK_ORIGIN")
        or origin != settings.web_origin
        or parsed.scheme != expected_scheme
        or not parsed.hostname
        or parsed.username is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
        or origin != f"{parsed.scheme}://{parsed.netloc}"
        or not re.fullmatch(r"temuriset_benchmark(?:_[a-z0-9_]+)?", database.database or "")
        or database.drivername != "postgresql+asyncpg"
        or database.query
        or (not staging and (parsed.hostname not in LOOPBACK or parsed.port is None or database.host not in LOOPBACK))
    ):
        raise BenchmarkError("Select the approved isolated benchmark origin, WEB_ORIGIN and benchmark-only database.")
    return database.database


def private_path(path: Path) -> Path:
    """Resolve a handoff path outside the repository, in a directory owned by this user."""
    root = Path(__file__).resolve().parents[6]
    parent = path.parent.resolve(strict=True)
    directory = parent.stat()
    if (
        parent.is_relative_to(root)
        or directory.st_uid != os.getuid()
        or stat.S_IMODE(directory.st_mode) & 0o077
        or path.is_symlink()
    ):
        raise BenchmarkError("Place the session handoff in an owner-only directory outside the source tree.")
    return parent / path.name


async def require_target_database(session: AsyncSession, database: str) -> None:
    """Verify the identity of the connected database before accessing fixtures."""
    if await session.scalar(select(func.current_database())) != database:
        raise BenchmarkError("Connected database differs from the selected benchmark database.")


async def verify_dataset(session: AsyncSession, dataset: Dataset) -> bool:
    """Verify the catalog and session counts, returning whether the worker projection is ready."""
    await require_target_database(session, dataset.database)
    invention_ids = {item for actor in dataset.actors for item in actor.inventions}
    actors = {actor.account_id for actor in dataset.actors}
    valid_sessions = set(
        await session.scalars(
            select(SessionRecord.account_id).where(
                SessionRecord.revoked_at.is_(None), SessionRecord.expires_at > clock.now()
            )
        )
    )
    accounts = set(
        await session.scalars(
            select(AccountRecord.id).where(AccountRecord.kind == "demo", AccountRecord.email.like("benchmark-%"))
        )
    )
    published = set(
        await session.scalars(
            select(InventionRecord.id).where(
                InventionRecord.status == "PUBLISHED", InventionRecord.published_version_id.is_not(None)
            )
        )
    )
    active_rows = (
        await session.execute(
            select(OpportunityRecord.id, OpportunityRecord.partner_party_id).where(OpportunityRecord.status == "ACTIVE")
        )
    ).all()
    active = {opportunity_id for opportunity_id, _ in active_rows}
    owners = {party_id for _, party_id in active_rows}
    if (
        not actors
        or not invention_ids
        or not dataset.opportunity_ids
        or actors != accounts
        or actors != valid_sessions
        or len(actors) != len(dataset.actors)
        or published != invention_ids
        or active != dataset.opportunity_ids
        or owners != dataset.partner_ids
    ):
        raise BenchmarkError("Synthetic catalog or live-session counts differ from the handoff.")
    rows = (await session.scalars(select(SearchDocumentRecord))).all()
    inventions = {row.subject_id for row in rows if row.subject_type == "INVENTION"}
    partners = {row.subject_id for row in rows if row.subject_type == "PARTNER"}
    opportunities = {
        UUID(item["id"]) for row in rows if row.subject_type == "PARTNER" for item in row.card["opportunities"]
    }
    pending_event = await session.scalar(
        select(OutboxEventRecord.id).where(OutboxEventRecord.dispatched_at.is_(None)).limit(1)
    )
    return (
        pending_event is None
        and inventions == invention_ids
        and partners == dataset.partner_ids
        and opportunities == active
        and len(rows) == len(inventions) + len(partners)
    )


async def add_invention(session: AsyncSession, principal: Principal, index: int) -> UUID:
    """Publish a labelled variant of one of the demo inventions."""
    fixture = list(data.INVENTIONS.values())[index % len(data.INVENTIONS)]["content"]
    title = f"{PREFIX} {index:04d} · {fixture['title']}"
    if index == 0:
        title = f"{title} {VISIBILITY_TERM}"
    content = {**fixture, "title": title, "claims": [], "private_notes": f"{PREFIX} · catatan internal"}
    portfolio = PortfolioService(session)
    party = principal.active_party_id
    draft = await portfolio.create(principal, CreateInventionRequest(acting_party_id=party))
    saved = await portfolio.save_draft(
        principal, draft.id, DraftRequest(acting_party_id=party, expected_version=draft.version, **content)
    )
    await portfolio.publish(
        principal, draft.id, VersionedActionRequest(acting_party_id=party, expected_version=saved.version)
    )
    return draft.id


async def add_opportunity(session: AsyncSession, principal: Principal, index: int) -> UUID:
    """Activate a demo-shaped specific opportunity with a uniquely labelled title."""
    template = data.OPPORTUNITIES[("A1", "A2", "B1", "C1")[index % 4]]["content"]
    content = {**template, "title": f"{PREFIX} {index:04d} · {template['title']}", "closes_at": None}
    intake = IntakeService(session)
    party = principal.active_party_id
    draft = await intake.create(principal, CreateOpportunityRequest(acting_party_id=party, **content))
    await intake.transition(
        principal,
        draft.id,
        "activate",
        OpportunityTransitionRequest(acting_party_id=party, expected_version=draft.version),
    )
    return draft.id


async def seed(session: AsyncSession, args: argparse.Namespace, database: str) -> Dataset:
    """Create every fixture atomically in a blank benchmark database."""
    await require_target_database(session, database)
    for model in (AccountRecord, InventionRecord, OpportunityRecord, SearchDocumentRecord):
        if await session.scalar(select(model.id).limit(1)) is not None:
            raise BenchmarkError("Use a fresh migrated benchmark database with no existing fixture or account data.")
    actors, principals = [], []
    partner_count = min(args.users // 2, args.opportunities)
    partner_start = args.users - partner_count
    for index in range(args.users):
        email = demo_email(f"benchmark-{index:02d}")
        await create_demo_account(
            session,
            email=email,
            display_name=f"{PREFIX} · akun {index:02d}",
            persona="mitra" if index >= partner_start else "inovator",
            time_zone="Asia/Jakarta",
        )
        token, principal = await start_demo_session(session, get_settings(), email)
        actors.append(
            Actor(
                token=SecretStr(token),
                account_id=principal.account_id,
                party_id=principal.active_party_id,
                inventions=[],
            )
        )
        principals.append(principal)
    for index in range(args.inventions):
        owner = index % args.users
        actors[owner].inventions.append(await add_invention(session, principals[owner], index))

    partners = principals[partner_start:]
    for principal in partners:
        party = principal.active_party_id
        await IntakeService(session).save_profile(
            principal,
            party,
            SavePartnerProfileRequest(acting_party_id=party, expected_version=None, **data.PROFILES["A"]["content"]),
        )
    opportunities = {
        await add_opportunity(session, partners[index % partner_count], index) for index in range(args.opportunities)
    }
    needs = NeedsService(session)
    inventor = principals[0]
    party = inventor.active_party_id
    source = await needs.create(
        inventor,
        CreateSupportRequest(
            acting_party_id=party, invention_id=actors[0].inventions[0], **data.SUPPORT_REQUESTS["F01"]
        ),
    )
    await needs.transition(
        inventor, source.id, "activate", TransitionRequest(acting_party_id=party, expected_version=source.version)
    )
    return Dataset(
        origin=args.origin,
        database=database,
        actors=actors,
        opportunity_ids=opportunities,
        partner_ids={partner.active_party_id for partner in partners},
        source_id=source.id,
    )


def write_handoff(file: TextIO, dataset: Dataset) -> None:
    """Write the cookie only to the private handoff, never to stdout or the benchmark report."""
    content = dataset.model_dump(mode="json")
    for serialized, actor in zip(content["actors"], dataset.actors, strict=True):
        serialized["token"] = actor.token.get_secret_value()
    json.dump(content, file)


async def seed_ready_target(args: argparse.Namespace, database: str, file: TextIO) -> None:
    """Check API readiness and write the handoff before committing the seed."""
    async with httpx.AsyncClient(base_url=args.origin, trust_env=False) as client:
        if (await client.get("/health/ready")).status_code != 200:
            raise BenchmarkError("The selected benchmark API is not ready.")
    try:
        with seeded_ids("benchmarks-039"):
            async with get_session_factory()() as session, session.begin():
                dataset = await seed(session, args, database)
                await asyncio.to_thread(write_handoff, file, dataset)
                # Closing flushes buffered credentials while a failure can still roll back the seed.
                await asyncio.to_thread(file.close)
    finally:
        await get_engine().dispose()


def generate(args: argparse.Namespace) -> None:
    """Guard, seed and hand off a private dataset for the benchmark runner."""
    database = target(args.origin, staging=args.staging)
    handoff = private_path(args.handoff)
    if not 2 <= args.users <= 100 or not args.users <= args.inventions or not 1 <= args.opportunities <= 500:
        raise BenchmarkError("Require 2–100 users, at least one invention per user, and 1–500 opportunities.")
    descriptor = os.open(handoff, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w") as file:
            asyncio.run(seed_ready_target(args, database, file))
    except BaseException:
        # Release the reservation while preserving the original failure if cleanup fails.
        with suppress(OSError):
            handoff.unlink()
        raise
    print(
        f"Seeded {args.inventions} inventions, {args.opportunities} opportunities and {args.users} synthetic sessions."
    )


def main() -> None:
    """Run from the API directory with its locked dependencies."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--handoff", required=True, type=Path)
    parser.add_argument("--staging", action="store_true")
    parser.add_argument("--inventions", type=int, default=1000)
    parser.add_argument("--opportunities", type=int, default=100)
    parser.add_argument("--users", type=int, default=20)
    args = parser.parse_args()
    try:
        generate(args)
    except BenchmarkError as error:
        parser.exit(1, f"Benchmark seed failed: {error}\n")
    except httpx.HTTPError:
        parser.exit(1, "Benchmark seed failed: the selected API request failed.\n")
    except FileExistsError:
        parser.exit(1, "Benchmark seed failed: the private handoff already exists.\n")
    except OSError:
        parser.exit(1, "Benchmark seed failed: could not access the private handoff or database.\n")


if __name__ == "__main__":
    main()
