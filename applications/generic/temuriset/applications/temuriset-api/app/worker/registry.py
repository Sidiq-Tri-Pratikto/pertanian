"""Which code runs for each outbox topic and job kind. Features register here as they ship (027, 028, 036)."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

# A consumer gets the worker's session, so its database writes commit with its delivery record.
ConsumerHandler = Callable[[AsyncSession, dict[str, Any]], Awaitable[None]]
# A job handler returns a reference to its result, such as {"type": "export", "id": "..."}.
JobHandler = Callable[[AsyncSession, dict[str, Any]], Awaitable[dict[str, Any] | None]]


@dataclass
class Registry:
    """Consumers per topic and handlers per job kind.

    Attributes:
        consumers (dict[str, dict[str, ConsumerHandler]]): Topic to consumer name to handler.
        jobs (dict[str, JobHandler]): Job kind to handler.
    """

    consumers: dict[str, dict[str, ConsumerHandler]] = field(default_factory=dict)
    jobs: dict[str, JobHandler] = field(default_factory=dict)

    def consumer(self, topic: str, name: str) -> Callable[[ConsumerHandler], ConsumerHandler]:
        """Register a consumer. Its name is recorded per delivery, so never rename a deployed consumer.

        Args:
            topic (str): The topic.
            name (str): Stable consumer name.

        Returns:
            Callable[[ConsumerHandler], ConsumerHandler]: Decorator.
        """

        def register(handler: ConsumerHandler) -> ConsumerHandler:
            self.consumers.setdefault(topic, {})[name] = handler
            return handler

        return register

    def job(self, kind: str) -> Callable[[JobHandler], JobHandler]:
        """Register a job handler.

        Args:
            kind (str): The job kind.

        Returns:
            Callable[[JobHandler], JobHandler]: Decorator.
        """

        def register(handler: JobHandler) -> JobHandler:
            self.jobs[kind] = handler
            return handler

        return register


registry = Registry()
