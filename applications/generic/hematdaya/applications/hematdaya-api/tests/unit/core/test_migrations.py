"""Migration history stays linear while two people add migrations in parallel."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

API_ROOT = Path(__file__).resolve().parents[3]


def test_single_migration_head() -> None:
    """
    Condition:
    - Two branches each added a migration on the same parent and both merged.

    Expected:
    - This fails until the second one re-points its down_revision, so main never has two heads.
    """
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "migrations"))

    heads = ScriptDirectory.from_config(config).get_heads()

    assert len(heads) <= 1, f"Multiple Alembic heads: {sorted(heads)}. Re-point the later migration's down_revision."
