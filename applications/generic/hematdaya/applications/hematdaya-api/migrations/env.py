"""Alembic environment: runs migrations through the application's async engine settings."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.assets.repository.sqlalchemy import models as assets_models  # noqa: F401
from app.audit.repository.sqlalchemy import models as audit_models  # noqa: F401
from app.core.database import Base
from app.core.settings import get_settings
from app.demo.repository.sqlalchemy import models as demo_models  # noqa: F401
from app.feedback.repository.sqlalchemy import models as feedback_models  # noqa: F401
from app.identity.repository.sqlalchemy import models as identity_models  # noqa: F401
from app.imports.repository.sqlalchemy import models as imports_models  # noqa: F401
from app.insights.repository.sqlalchemy import models as insights_models  # noqa: F401
from app.measurements.repository.sqlalchemy import models as measurements_models  # noqa: F401
from app.meter_pilot.repository.sqlalchemy import models as meter_pilot_models  # noqa: F401
from app.scope.repository.sqlalchemy import models as scope_models  # noqa: F401
from app.sites.repository.sqlalchemy import models as sites_models  # noqa: F401

if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL without a database connection."""
    url = get_settings().database_url.get_secret_value()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def _run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Apply migrations over an async connection."""
    engine = create_async_engine(get_settings().database_url.get_secret_value())
    async with engine.connect() as connection:
        await connection.run_sync(_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
