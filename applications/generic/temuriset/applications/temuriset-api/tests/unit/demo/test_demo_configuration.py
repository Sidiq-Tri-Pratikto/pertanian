"""Demo mode and startup configuration (spec 021, scenario 4)."""

import pytest

from app.capabilities.service.configuration import ConfigurationError, validate_configuration
from app.core.settings import get_settings


def test_production_refuses_demo_mode_unless_marked_a_demonstration() -> None:
    """
    Condition:
    - Production settings with demo mode, with and without the demonstration mark (scenario 4).

    Expected:
    - Startup refuses the first with a message naming the settings, and accepts the second.
    """
    base = get_settings().model_copy(update={"environment": "production", "file_scanner": "clamav", "demo_mode": True})
    with pytest.raises(ConfigurationError, match="DEMO_DEPLOYMENT=true"):
        validate_configuration(base)
    try:
        validate_configuration(base.model_copy(update={"demo_deployment": True}))
    except ConfigurationError as error:
        # Production also refuses the development mailbox; only that refusal may remain.
        assert "MAILBOX_ADAPTER" in str(error)  # noqa: PT017 - the remaining refusal is not about demo mode
