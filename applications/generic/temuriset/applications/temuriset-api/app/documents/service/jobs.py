"""Worker jobs: scan quarantined files, then read their text. Registered on import by the worker."""

from typing import Any
from uuid import UUID

import anyio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.documents.repository.sqlalchemy.repository import SqlAlchemyDocumentRepository
from app.documents.service.extraction import extract_text
from app.documents.service.scanner_service import scanner_for
from app.documents.service.storage_service import LocalStorage
from app.platform.service.outbox import enqueue_job
from app.worker.registry import registry


@registry.job("documents.scan")
async def scan(session: AsyncSession, job_input: dict[str, Any]) -> dict[str, Any]:
    """Scan a quarantined version; only a clean file becomes available, then its text is read.

    Args:
        session (AsyncSession): The worker's session.
        job_input (dict[str, Any]): ``version_id``.

    Returns:
        dict[str, Any]: The version and its new file state.
    """
    settings = get_settings()
    repository = SqlAlchemyDocumentRepository(session)
    version = await repository.version(version_id=UUID(job_input["version_id"]))
    if version is None or version.file_state != "QUARANTINED":
        return {"type": "document_version", "id": job_input["version_id"]}
    path = LocalStorage(settings.storage_path).local_path(version.storage_key)
    clean = await scanner_for(settings).is_clean(path)
    await repository.update_version(
        version.id,
        file_state="AVAILABLE" if clean else "REJECTED",
        extraction_state="PENDING" if clean else "NOT_REQUESTED",
    )
    if clean:
        await enqueue_job(session, "documents.extract", {"version_id": str(version.id)})
    return {"type": "document_version", "id": str(version.id), "file_state": "AVAILABLE" if clean else "REJECTED"}


@registry.job("documents.extract")
async def extract(session: AsyncSession, job_input: dict[str, Any]) -> dict[str, Any]:
    """Read an available file's text; images and scans need a person, and no fact is ever invented (AC15).

    Args:
        session (AsyncSession): The worker's session.
        job_input (dict[str, Any]): ``version_id``.

    Returns:
        dict[str, Any]: The version and its extraction state.
    """
    repository = SqlAlchemyDocumentRepository(session)
    version = await repository.version(version_id=UUID(job_input["version_id"]))
    if version is None or version.file_state != "AVAILABLE":
        return {"type": "document_version", "id": job_input["version_id"]}
    path = LocalStorage(get_settings().storage_path).local_path(version.storage_key)
    try:
        text = await anyio.to_thread.run_sync(extract_text, path, version.media_type)
    except ValueError:
        state, characters = "FAILED", None
    else:
        state, characters = ("SUCCEEDED", len(text)) if text else ("NEEDS_MANUAL_INPUT", None)
    await repository.update_version(version.id, extraction_state=state, extracted_characters=characters)
    return {"type": "document_version", "id": str(version.id), "extraction_state": state}
