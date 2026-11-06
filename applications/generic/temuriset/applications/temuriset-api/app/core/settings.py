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
        web_origin (str): The web client's origin. Unsafe requests carrying a session must come from it.
        session_cookie_secure (bool | None): ``Secure`` flag on the session cookie; None means outside development.
        mailbox_adapter (str): Email delivery; ``development`` writes to a table and is refused outside development.
        calendar_adapter (str): Calendar integration; the loopback profile is development-only.
        calendar_authorize_url (str): Loopback authorization endpoint.
        calendar_callback_origin (str): Direct loopback API origin for the fixed OAuth callback.
        calendar_token_url (str): Loopback token endpoint.
        calendar_freebusy_url (str): Loopback free/busy endpoint.
        calendar_revoke_url (str): Loopback revocation endpoint.
        calendar_client_id (str): Synthetic OAuth client identifier.
        calendar_scope (str): The exact free/busy scope granted by the local double.
        calendar_envelope_key (SecretStr | None): Calendar-only encryption key.
        code_requests_per_email_per_hour (int): Sign-in code requests allowed per email in an hour.
        code_requests_per_address_per_hour (int): Sign-in code requests allowed per client address in an hour.
        storage_path (str): Folder of the local storage adapter; bytes never get a public URL.
        clamav_host (str): ClamAV daemon host for ``FILE_SCANNER=clamav``.
        clamav_port (int): ClamAV daemon port.
        demo_mode (bool): Offer labelled demo accounts and their reset (spec 021).
        demo_deployment (bool): This deployment is a demonstration; required for ``demo_mode`` outside development.
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
    web_origin: str = "http://localhost:3020"
    session_cookie_secure: bool | None = None
    mailbox_adapter: Literal["development", "disabled"] = "development"
    calendar_adapter: Literal["off", "loopback-oauth"] = "off"
    calendar_authorize_url: str = ""
    calendar_callback_origin: str = "http://localhost:8020"
    calendar_token_url: str = ""
    calendar_freebusy_url: str = ""
    calendar_revoke_url: str = ""
    calendar_client_id: str = ""
    calendar_scope: Literal["freebusy.read"] = "freebusy.read"
    calendar_envelope_key: SecretStr | None = None
    code_requests_per_email_per_hour: int = 5
    code_requests_per_address_per_hour: int = 20
    storage_adapter: Literal["local", "s3"] = "local"
    storage_path: str = ".storage"
    s3_endpoint_url: SecretStr | None = None
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    s3_access_key: SecretStr | None = None
    s3_secret_key: SecretStr | None = None
    clamav_host: str = "localhost"
    clamav_port: int = 3310
    demo_mode: bool = False
    demo_deployment: bool = False

    @property
    def calendar_enabled(self) -> bool:
        """Whether startup selected the development-only calendar profile."""
        return self.environment == "development" and self.calendar_adapter == "loopback-oauth"

    @property
    def cookie_secure(self) -> bool:
        """Whether the session cookie is ``Secure``.

        Returns:
            bool: The explicit setting, or True outside development.
        """
        return (
            self.session_cookie_secure if self.session_cookie_secure is not None else self.environment != "development"
        )


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings.

    Returns:
        Settings: The validated settings.
    """
    return Settings()
