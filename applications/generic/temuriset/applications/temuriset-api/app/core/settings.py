"""Application settings, validated at startup."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings read from the environment and an optional local ``.env`` file.

    Attributes:
        service_name (str): Name recorded with every failure.
        environment (str): Deployment environment.
        log_level (str): Root log level.
        database_url (SecretStr): Async SQLAlchemy connection URL. Required.
        cors_allowed_origins (list[str]): Browser origins allowed to call the API. Native clients need none.
        composition (str): Supported product composition; an unknown value stops startup.
        composition_overrides (dict[str, bool]): Capabilities switched on or off on top of the composition.
        file_scanner (str): Upload scanner adapter; ``development-accept`` is refused outside development.
    """

    # A rejected value never appears in the startup error, so a secret pasted into the wrong setting stays out of logs.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    service_name: str = "temuriset-api"
    environment: str = "development"
    log_level: str = "INFO"
    database_url: SecretStr
    cors_allowed_origins: list[str] = []
    composition: str = "generic-base"
    composition_overrides: dict[str, bool] = {}
    file_scanner: Literal["clamav", "development-accept"] = "development-accept"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings.

    Returns:
        Settings: The validated settings.
    """
    return Settings()
