---
description: SOLID, scalability, memory, and performance guidance. Use for architecture or performance decisions.
globs: "applications/**/app/**/service/**"
alwaysApply: false
trigger: model_decision
paths:
  - "applications/**/app/**/service/**"
---
# Architecture Principles

## SOLID

- **SRP:** services hold business logic, repositories data access, routers HTTP.
- **OCP:** extend through new implementations and injected dependencies.
- **LSP:** a repository implementation honors its full interface.
- **ISP:** interfaces stay narrow; services depend only on what they use.
- **DIP:** services depend on `BaseRepository`, not SQLAlchemy.

## Patterns

- **Repository:** abstract data access so services test without a database.
- **Service layer:** business rules with no HTTP or SQL.
- **Dependency injection:** `Depends()` in routers, constructor injection in services.

Add an abstraction when it has a second implementation or makes testing possible. Otherwise skip it.

## Scalability

- **Stateless:** no session state in process memory; shared state goes to a database or cache.
- **Connection pooling:** size pools to instance count and database limits.
- **Timeouts:** every external call has one.
- **Bounded work:** paginate lists, limit payload sizes, cap concurrency and retries.

## Concurrency

- `await` all I/O. Never block the event loop; push CPU-heavy work to a worker or `asyncio.to_thread`.
- `asyncio.gather()` for independent operations, with a concurrency limit when fan-out is unbounded.
- Long-running work belongs in a background worker, not a request.

## Performance

- Measure first. Profile before optimizing.
- Avoid N+1 queries; index fields used in filters and joins.
- Cache only what a measurement justifies, with a TTL and a namespaced key.

## Memory and resources

- Stream or chunk large data; use generators instead of loading everything.
- Close files, connections, and clients with context managers.
- Set limits on long-running processes and monitor them.
- Use `tracemalloc` to track allocation growth.
