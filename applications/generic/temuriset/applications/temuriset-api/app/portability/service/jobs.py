"""Register independently retried stages and expiry cleanup with the platform worker."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.portability.service.exports import ExportService
from app.portability.service.imports import ImportService
from app.worker.registry import registry


@registry.job("portability.import_validation")
async def validate(session: AsyncSession, job_input: dict[str, str]) -> dict[str, str]:
    """Validate only the staged upload referenced by the job."""
    await ImportService(session).validate_file(UUID(job_input["id"]))
    return job_input


@registry.job("portability.import_preview")
async def preview(session: AsyncSession, job_input: dict[str, str]) -> dict[str, str]:
    """Build the next durable preview checkpoint."""
    await ImportService(session).preview_batch(UUID(job_input["id"]))
    return job_input


@registry.job("portability.import_apply")
async def apply(session: AsyncSession, job_input: dict[str, str]) -> dict[str, str]:
    """Apply the next authorized import checkpoint."""
    await ImportService(session).apply_batch(UUID(job_input["id"]))
    return job_input


@registry.job("portability.generate_export")
async def export(session: AsyncSession, job_input: dict[str, str]) -> dict[str, str]:
    """Generate or expire one queued result."""
    await ExportService(session).generate(UUID(job_input["id"]))
    return job_input


@registry.job("portability.cleanup_import")
async def cleanup_import(session: AsyncSession, job_input: dict[str, str]) -> dict[str, str]:
    """Remove expired import staging data."""
    await ImportService(session).cleanup(UUID(job_input["id"]))
    return job_input


@registry.job("portability.cleanup_export")
async def cleanup_export(session: AsyncSession, job_input: dict[str, str]) -> dict[str, str]:
    """Remove an expired export artifact."""
    await ExportService(session).cleanup(UUID(job_input["id"]))
    return job_input
