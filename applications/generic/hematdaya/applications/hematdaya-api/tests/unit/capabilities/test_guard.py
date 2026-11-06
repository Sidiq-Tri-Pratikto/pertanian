"""Composition guard at the service layer (FR-21, partial AT-53)."""

from uuid import UUID, uuid4

import pytest

from app.capabilities.service.guard import (
    CAPABILITY_DISABLED_REASON,
    CapabilityDisabledError,
    CapabilityGuard,
)
from app.core.errors.base import NotFoundError
from app.core.errors.public import public_error_for_code


class GuardedUseCase:
    """A stand-in optional use case: ownership first, then the capability, then the work."""

    def __init__(self, guard: CapabilityGuard, owners: dict[UUID, UUID]) -> None:
        self.guard = guard
        self.owners = owners
        self.computed = 0

    def run(self, site_id: UUID, principal_id: UUID) -> str:
        if self.owners.get(site_id) != principal_id:
            raise NotFoundError()
        self.guard.require("cost")
        self.computed += 1
        return "computed"


def test_core_only_refuses_the_use_case_without_any_route() -> None:
    """
    Condition:
    - core-only, and an owned site's guarded use case called directly.

    Expected:
    - CAPABILITY_DISABLED naming the capability, and nothing is computed.
    """
    site, owner = uuid4(), uuid4()
    use_case = GuardedUseCase(CapabilityGuard("core-only"), {site: owner})

    with pytest.raises(CapabilityDisabledError) as error:
        use_case.run(site, owner)

    assert error.value.capability == "cost"
    assert "biaya" in error.value.message
    assert public_error_for_code(error.value.code).code == "CAPABILITY_DISABLED"
    assert public_error_for_code(error.value.code).http_status == 403
    assert use_case.computed == 0


def test_full_composition_passes_the_guard_but_not_ownership() -> None:
    """
    Condition:
    - core-plus-optional: the owner, then someone else, run the use case.

    Expected:
    - The owner computes; the other principal is refused by ownership before any capability lookup.
    """
    site, owner = uuid4(), uuid4()
    use_case = GuardedUseCase(CapabilityGuard("core-plus-optional"), {site: owner})

    assert use_case.run(site, owner) == "computed"
    with pytest.raises(NotFoundError):
        use_case.run(site, uuid4())


def test_ownership_is_checked_before_the_capability() -> None:
    """
    Condition:
    - core-only and a foreign site.

    Expected:
    - NOT_FOUND, not CAPABILITY_DISABLED: composition never reveals or grants anything.
    """
    use_case = GuardedUseCase(CapabilityGuard("core-only"), {uuid4(): uuid4()})

    with pytest.raises(NotFoundError):
        use_case.run(uuid4(), uuid4())


def test_compositions_and_capabilities_are_validated() -> None:
    """
    Condition:
    - An unknown composition, and an unknown capability.

    Expected:
    - Both are programming errors; the shared disabled reason is stable.
    """
    with pytest.raises(ValueError, match="Unsupported composition"):
        CapabilityGuard("everything")
    with pytest.raises(ValueError, match="Unknown capability"):
        CapabilityGuard("core-only").require("ai")
    assert CapabilityGuard("core-only").enabled("core")
    assert CAPABILITY_DISABLED_REASON == "capability_disabled"
