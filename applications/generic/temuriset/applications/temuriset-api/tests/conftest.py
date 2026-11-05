"""Shared test configuration. Settings must exist before any ``app`` import."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://app:app@localhost:5442/app")
