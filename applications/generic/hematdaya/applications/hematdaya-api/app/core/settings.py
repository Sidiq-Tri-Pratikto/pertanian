"""Application settings, validated at startup."""

import logging
import secrets
from functools import lru_cache
from typing import Self

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_EPHEMERAL_KEY_ENVIRONMENTS = ("development", "test")


class Settings(BaseSettings):
    """Settings read from the environment and an optional local ``.env`` file.

    Attributes:
        service_name (str): Name recorded with every failure.
        environment (str): Deployment environment.
        log_level (str): Root log level.
        database_url (SecretStr): Async SQLAlchemy connection URL. Required.
        cors_allowed_origins (list[str]): Browser origins allowed to call the API. Native clients need none.
        composition (str): Supported product composition; an unknown value stops startup.
        demo_session_ttl_hours (int): How long an anonymous demo workspace lives.
        demo_max_active_sessions (int): Active demo sessions across all instances.
        demo_create_max_per_minute (int): New demo seeds admitted per wall-clock minute.
        demo_create_replay_seconds (int): How long a lost create response can be recovered.
        demo_token_keys (dict[str, SecretStr]): HMAC keys by version. Keep the previous key until its replay
            windows close. Development and test generate an ephemeral key when none is set.
        demo_token_key_version (str): The key version new sessions use.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "hematdaya-api"
    environment: str = "development"
    log_level: str = "INFO"
    database_url: SecretStr
    cors_allowed_origins: list[str] = []
    composition: str = "core-plus-optional"
    demo_session_ttl_hours: int = 72
    demo_max_active_sessions: int = 200
    demo_create_max_per_minute: int = 30
    demo_create_replay_seconds: int = 300
    demo_token_keys: dict[str, SecretStr] = {}
    demo_token_key_version: str = "v1"

    @model_validator(mode="after")
    def _check_demo(self) -> Self:
        if self.demo_create_replay_seconds >= self.demo_session_ttl_hours * 3600:
            raise ValueError("DEMO_CREATE_REPLAY_SECONDS must be shorter than the session TTL.")
        if not self.demo_token_keys:
            if self.environment not in _EPHEMERAL_KEY_ENVIRONMENTS:
                raise ValueError("DEMO_TOKEN_KEYS is required outside development and test.")
            # Bearer checks need no key; only replay of a lost create response breaks across restarts.
            logging.getLogger(__name__).warning("DEMO_TOKEN_KEYS is not set; using an ephemeral key.")
            self.demo_token_keys = {self.demo_token_key_version: SecretStr(secrets.token_urlsafe(32))}
        if self.demo_token_key_version not in self.demo_token_keys:
            raise ValueError("DEMO_TOKEN_KEY_VERSION must name one of DEMO_TOKEN_KEYS.")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings.

    Returns:
        Settings: The validated settings.
    """
    return Settings()
