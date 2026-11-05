"""Wait for the configured private bucket using its runtime identity."""

import asyncio

from app.capabilities.service.configuration import validate_configuration
from app.core.settings import get_settings
from app.documents.service.s3_storage_service import s3_storage
from app.documents.service.storage_service import StorageUnavailableError


async def main() -> None:
    """Exit with failure unless the configured identity can reach the bucket."""
    settings = get_settings()
    validate_configuration(settings)
    storage = s3_storage(settings)
    async with asyncio.timeout(90):
        while True:
            try:
                await storage.check_bucket()
                return
            except StorageUnavailableError:
                await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
