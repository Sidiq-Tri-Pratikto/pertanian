"""Measure API reads and matching using verified synthetic cookie sessions."""

import argparse
import asyncio
import json
import math
import os
import stat
from collections import Counter
from collections.abc import Callable, Sequence
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import UUID, uuid4

import httpx
from pydantic import TypeAdapter, ValidationError

from app.capabilities.model.schema import CapabilityManifestResponse
from app.core.database import get_engine, get_session_factory
from app.core.security import SESSION_COOKIE
from app.discovery.model.schema import DiscoveryResponse
from app.identity.model.schema import MeResponse
from app.matching.model.schema import MatchRunResponse
from app.portfolio.model.schema import InventionResponse, InventionSummaryResponse
from benchmarks.generate import VISIBILITY_TERM, Actor, BenchmarkError, Dataset, private_path, target, verify_dataset

DISCOVERY = "/api/v1/discovery?type=inventions&limit=20"
ME = "/api/v1/me"
INVENTIONS = "/api/v1/inventions"
DETAIL = f"{INVENTIONS}/{{id}}"
VISIBILITY = f"{DISCOVERY}&q={VISIBILITY_TERM}"
TARGET_MS = {ME: 500, INVENTIONS: 500, DETAIL: 500, DISCOVERY: 2000}
MATCH_BUDGET_MS = 2000
LIST = TypeAdapter(list[InventionSummaryResponse])


@dataclass
class Samples:
    """HTTP and payload failures are separate from successful request latency."""

    latency: list[float] = field(default_factory=list)
    http: Counter[int] = field(default_factory=Counter)
    timeouts: int = 0
    transport: int = 0
    invalid_payloads: int = 0

    def report(self, route: str) -> dict:
        """Summarize successful latency at the nearest-rank p95 and count all failures."""
        if not self.latency:
            raise BenchmarkError(
                f"No successful samples for {route}. HTTP failures: {dict(self.http)}, "
                f"timeouts: {self.timeouts}, transport: {self.transport}, invalid payloads: {self.invalid_payloads}."
            )
        successes = len(self.latency)
        attempted = successes + sum(self.http.values()) + self.timeouts + self.transport + self.invalid_payloads
        p95 = sorted(self.latency)[math.ceil(0.95 * successes) - 1]
        return {
            "attempted": attempted,
            "successful": successes,
            "http_failures": dict(self.http),
            "timeouts": self.timeouts,
            "transport_failures": self.transport,
            "invalid_payloads": self.invalid_payloads,
            "p95_ms": round(p95, 3),
            "target_ms": TARGET_MS[route],
            "passed": attempted == successes and p95 <= TARGET_MS[route],
        }


@dataclass(frozen=True)
class Request:
    """One endpoint and the shape and identity invariants expected from its payload."""

    route: str
    path: str
    valid: Callable[[bytes], bool]


def load_dataset(path: Path, origin: str, database: str) -> Dataset:
    """Load a private handoff, validating its scope and distinct synthetic actors."""
    handoff = private_path(path)
    with handoff.open("rb") as file:
        metadata = os.fstat(file.fileno())
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            raise BenchmarkError("The handoff must be a regular, owner-only mode 0600 file.")
        try:
            dataset = Dataset.model_validate_json(file.read())
        except ValidationError:
            raise BenchmarkError("The private handoff is invalid.") from None
    actors = dataset.actors
    if (
        dataset.origin != origin
        or dataset.database != database
        or not 2 <= len(actors) <= 100
        or any(not actor.inventions or not actor.token.get_secret_value() for actor in actors)
        or len({actor.party_id for actor in actors}) != len(actors)
        or len({actor.token.get_secret_value() for actor in actors}) != len(actors)
        or not dataset.partner_ids
        or not dataset.opportunity_ids
        or actors[0].party_id in dataset.partner_ids
    ):
        raise BenchmarkError(
            "The handoff differs from the selected target or has absent synthetic sessions or catalog."
        )
    return dataset


def valid_me(content: bytes, actor: Actor) -> bool:
    """Check that the API resolved the exact seeded account and acting party."""
    payload = MeResponse.model_validate_json(content)
    return (
        payload.account.id == actor.account_id
        and payload.account.kind == "demo"
        and payload.account.email.startswith("benchmark-")
        and payload.account.email.endswith("@demo.invalid")
        and payload.active_party_id == actor.party_id
    )


def invention_items(payload: DiscoveryResponse) -> set[UUID]:
    """Return the invention IDs across all sections of a discovery page."""
    return {
        item.subject_id for section in payload.sections for item in section.items if item.subject_type == "INVENTION"
    }


def standard_requests(actor: Actor) -> tuple[Request, ...]:
    """Construct the same three-request cycle for each actor's own portfolio."""
    owned_ids = set(actor.inventions)
    detail_id = actor.inventions[0]

    def valid_list(content: bytes) -> bool:
        items = LIST.validate_json(content)
        return len(items) == len(owned_ids) and {item.id for item in items} == owned_ids

    def valid_detail(content: bytes) -> bool:
        item = InventionResponse.model_validate_json(content)
        return (
            item.id == detail_id
            and item.managing_party_id == actor.party_id
            and item.status == "PUBLISHED"
            and item.published is not None
        )

    return (
        Request(ME, ME, lambda content: valid_me(content, actor)),
        Request(INVENTIONS, INVENTIONS, valid_list),
        Request(DETAIL, DETAIL.format(id=detail_id), valid_detail),
    )


def discovery_request(invention_ids: set[UUID]) -> Request:
    """Check the first page against the seeded catalog."""

    def valid_page(content: bytes) -> bool:
        payload = DiscoveryResponse.model_validate_json(content)
        ids = invention_items(payload)
        return (
            payload.type == "inventions"
            and payload.total_estimate == len(invention_ids)
            and len(ids) == min(20, len(invention_ids))
            and ids <= invention_ids
        )

    return Request(DISCOVERY, DISCOVERY, valid_page)


async def sample(client: httpx.AsyncClient, request: Request, samples: Samples) -> None:
    """Measure body receipt and separately verify the status and response payload."""
    start = perf_counter()
    try:
        response = await client.get(request.path)
    except httpx.TimeoutException:
        samples.timeouts += 1
        return
    except httpx.RequestError:
        samples.transport += 1
        return
    elapsed_ms = (perf_counter() - start) * 1000
    if response.status_code != 200:
        samples.http[response.status_code] += 1
        return
    try:
        valid = request.valid(response.content)
    except ValidationError:
        valid = False
    if valid:
        samples.latency.append(elapsed_ms)
    else:
        samples.invalid_payloads += 1


async def phase(
    clients: Sequence[httpx.AsyncClient], requests: Sequence[tuple[Request, ...]], seconds: float | None
) -> dict:
    """Start virtual users together and run one cycle or a fixed-duration closed loop."""
    samples = {request.route: Samples() for request in requests[0]}
    start = perf_counter()
    deadline = start + seconds if seconds is not None else None

    async def user(client: httpx.AsyncClient, cycle: tuple[Request, ...]) -> None:
        while True:
            for request in cycle:
                if deadline is not None and perf_counter() >= deadline:
                    return
                await sample(client, request, samples[request.route])
            if deadline is None:
                return

    await asyncio.gather(*(user(client, cycle) for client, cycle in zip(clients, requests, strict=True)))
    elapsed = perf_counter() - start
    return {
        "wall_seconds": round(elapsed, 3),
        "endpoints": {route: outcome.report(route) for route, outcome in samples.items()},
    }


def verify_match(payload: MatchRunResponse, dataset: Dataset) -> None:
    """Require the current source and every expected candidate exactly once."""
    candidates = [*payload.results, *payload.excluded]
    expected = dataset.opportunity_ids
    if (
        payload.source.id != dataset.source_id
        or payload.source.type != "SUPPORT_REQUEST"
        or payload.operation_id is None
        or len(candidates) != len(expected)
        or {item.opportunity_id for item in candidates} != expected
        or any(item.partner_party_id not in dataset.partner_ids for item in candidates)
    ):
        raise BenchmarkError("The match did not evaluate exactly the expected opportunities and source.")


async def measure_match(client: httpx.AsyncClient, dataset: Dataset) -> dict:
    """Time a fresh idempotent API request against the full catalog."""
    key = str(uuid4())
    body = {
        "acting_party_id": str(dataset.actors[0].party_id),
        "source_type": "SUPPORT_REQUEST",
        "source_id": str(dataset.source_id),
    }
    start = perf_counter()
    response = await client.post("/api/v1/matches", headers={"Idempotency-Key": key}, json=body)
    elapsed = (perf_counter() - start) * 1000
    if response.status_code != 201:
        raise BenchmarkError(f"Match returned HTTP {response.status_code} after {elapsed:.3f} ms.")
    payload = MatchRunResponse.model_validate_json(response.content)
    verify_match(payload, dataset)
    return {
        "ranked": len(payload.results),
        "excluded": len(payload.excluded),
        "candidates": len(dataset.opportunity_ids),
        "elapsed_ms": round(elapsed, 3),
        "budget_ms": MATCH_BUDGET_MS,
        "passed": elapsed <= MATCH_BUDGET_MS,
        "fallback": "not triggered" if elapsed <= MATCH_BUDGET_MS else "open: request exceeded job fallback budget",
        "engine": payload.engine,
    }


async def visibility(clients: list[httpx.AsyncClient], anonymous: httpx.AsyncClient, actor: Actor) -> dict:
    """Show that discovery requires authorization and the worker removes an archived listing."""
    denial = await anonymous.get(DISCOVERY)
    if denial.status_code != 401:
        raise BenchmarkError(f"Anonymous discovery returned HTTP {denial.status_code}, expected 401.")
    owner, viewer = clients[:2]
    subject = actor.inventions[0]

    async def find() -> set[UUID]:
        response = await viewer.get(VISIBILITY)
        response.raise_for_status()
        return invention_items(DiscoveryResponse.model_validate_json(response.content))

    if await find() != {subject}:
        raise BenchmarkError("The authorized viewer did not see the published visibility fixture.")
    detail = await owner.get(DETAIL.format(id=subject))
    detail.raise_for_status()
    item = InventionResponse.model_validate_json(detail.content)
    start = perf_counter()
    response = await owner.post(
        f"{INVENTIONS}/{subject}/archive",
        headers={"Idempotency-Key": str(uuid4())},
        json={"acting_party_id": str(actor.party_id), "expected_version": item.version},
    )
    if response.status_code != 200 or InventionResponse.model_validate_json(response.content).status != "ARCHIVED":
        raise BenchmarkError(f"The visibility fixture could not be archived (HTTP {response.status_code}).")
    deadline = start + 30
    while await find():
        if perf_counter() >= deadline:
            raise BenchmarkError("The worker did not remove the archived discovery item in 30 seconds.")
        await asyncio.sleep(0.25)
    return {
        "anonymous_http": denial.status_code,
        "visible_to_other_party_before": True,
        "visible_to_other_party_after": False,
        "worker_visibility_change_seconds": round(perf_counter() - start, 3),
    }


async def run(args: argparse.Namespace) -> dict:
    """Verify readiness, run timing phases, and perform the untimed visibility control."""
    database = target(args.origin, staging=args.staging)
    dataset = load_dataset(args.handoff, args.origin, database)
    start = perf_counter()
    while True:
        async with get_session_factory()() as session:
            if await verify_dataset(session, dataset):
                break
        if perf_counter() - start >= args.readiness_seconds:
            raise BenchmarkError("Discovery projection did not reach the seeded catalog before the readiness deadline.")
        await asyncio.sleep(0.5)

    started_at = datetime.now(UTC).isoformat()
    async with AsyncExitStack() as stack:
        anonymous = await stack.enter_async_context(
            httpx.AsyncClient(base_url=args.origin, trust_env=False, timeout=10)
        )
        manifest = await anonymous.get("/api/v1/capabilities")
        manifest.raise_for_status()
        capability = CapabilityManifestResponse.model_validate_json(manifest.content)

        clients = [
            await stack.enter_async_context(
                httpx.AsyncClient(
                    base_url=args.origin,
                    headers={"Origin": args.origin, "Cookie": f"{SESSION_COOKIE}={actor.token.get_secret_value()}"},
                    trust_env=False,
                    timeout=10,
                )
            )
            for actor in dataset.actors
        ]
        me = await asyncio.gather(*(client.get(ME) for client in clients))
        if not all(
            response.status_code == 200 and valid_me(response.content, actor)
            for response, actor in zip(me, dataset.actors, strict=True)
        ):
            raise BenchmarkError("The API target did not authenticate every expected synthetic session.")

        inventions = {item for actor in dataset.actors for item in actor.inventions}
        standard = [standard_requests(actor) for actor in dataset.actors]
        discovery = [(discovery_request(inventions.difference(actor.inventions)),) for actor in dataset.actors]
        phases = {
            "standard_first_pass": await phase(clients, standard, None),
            "discovery_first_pass": await phase(clients, discovery, None),
        }
        for label, workload in (("standard", standard), ("discovery", discovery)):
            phases[f"{label}_warmup"] = await phase(clients, workload, args.warmup_seconds)
            phases[f"{label}_warmed"] = await phase(clients, workload, args.seconds)
        match = await measure_match(clients[0], dataset)
        control = await visibility(clients, anonymous, dataset.actors[0])
    return {
        "started_at_utc": started_at,
        "target": "staging" if args.staging else "local",
        "dataset": {
            "published_inventions": len(inventions),
            "active_opportunities": len(dataset.opportunity_ids),
            "partner_projections": len(dataset.partner_ids),
            "users": len(clients),
        },
        "measurement_window_seconds": args.seconds,
        "warmup_window_seconds": args.warmup_seconds,
        "cache_state": "first-pass then warmed; no flush; no discovery response cache; reused connections",
        "capability_manifest": capability.model_dump(mode="json"),
        "phases": phases,
        "matching": match,
        "visibility": control,
    }


async def run_with_cleanup(args: argparse.Namespace) -> dict:
    """Dispose the process-owned PostgreSQL connections after the benchmark."""
    try:
        return await run(args)
    finally:
        if get_engine.cache_info().currsize:
            await get_engine().dispose()


def main() -> None:
    """Run the benchmark and print a credential-free JSON result."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--handoff", required=True, type=Path)
    parser.add_argument("--staging", action="store_true")
    parser.add_argument("--seconds", type=float, default=10)
    parser.add_argument("--warmup-seconds", type=float, default=2)
    parser.add_argument("--readiness-seconds", type=float, default=120)
    args = parser.parse_args()
    if not all(
        math.isfinite(value) and value > 0 for value in (args.seconds, args.warmup_seconds, args.readiness_seconds)
    ):
        parser.error("Timing windows must be finite positive numbers.")
    try:
        result = asyncio.run(run_with_cleanup(args))
    except (BenchmarkError, httpx.HTTPError, OSError) as error:
        parser.exit(1, f"Benchmark failed: {error}\n")
    except ValidationError:
        parser.exit(1, "Benchmark failed: the API returned an invalid response payload.\n")
    print(json.dumps(result, indent=2))
    if not result["matching"]["passed"] or not all(
        endpoint["passed"]
        for phase_result in result["phases"].values()
        for endpoint in phase_result["endpoints"].values()
    ):
        parser.exit(1, "Benchmark recorded a failed request or missed latency target.\n")


if __name__ == "__main__":
    main()
