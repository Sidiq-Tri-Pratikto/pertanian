---
description: Feature module folder structure and naming. Use when creating or organizing a feature module.
globs: "applications/**/app/**/*.py"
alwaysApply: false
trigger: glob
paths:
  - "applications/**/app/**/*.py"
---
# Module Structure

## Application layout

```
applications/<app>/
├── app/
│   ├── main.py          # create_app: lifespan, handlers, routers
│   ├── core/            # settings, logging, database, errors
│   ├── health/          # liveness and readiness
│   └── {feature}/       # one folder per feature
├── migrations/          # Alembic
└── tests/{unit,integration}/
```

The package is always `app`, whatever the application is called.

## Feature layout

```
{feature}/
├── __init__.py
├── router.py                  # HTTP only; in the feature root, not a subfolder
├── model/
│   ├── models.py              # domain models (Pydantic)
│   └── schema.py              # request and response schemas
├── repository/
│   ├── base_repository.py     # abstract interface
│   └── sqlalchemy/
│       ├── models.py          # ORM models
│       └── repository.py      # implementation
├── service/
│   ├── service.py             # business logic
│   └── {external}_service.py  # external integration, if any
└── helper/                    # optional
```

Reference implementation: `app/items/`. Create only the files a feature needs: a feature with no storage has no `repository/`.

## Layers

| Layer | May import | Must not |
|---|---|---|
| `router.py` | service, schemas, `app.core` | touch the database or hold business rules |
| `service/` | repository interface, models, `app.core.errors` | know HTTP or SQLAlchemy |
| `repository/` | ORM, domain models | hold business rules or return ORM objects |

Dependencies point inward: router to service to repository interface. Features do not import each other's repositories.

## Transactions

One request is one transaction. Inject the session with `SessionDep` from `app.core.database`: it commits after the route returns and before the response is sent, and rolls back when the route raises. Repositories call `flush()` when they need generated values and never `commit()`, so a service can write through several repositories atomically.

## Naming

| Type | Convention | Example |
|---|---|---|
| Module | snake_case | `order_history` |
| Service | PascalCase + `Service` | `OrderHistoryService` |
| Repository | `SqlAlchemy` + PascalCase + `Repository` | `SqlAlchemyOrderRepository` |
| Domain model | PascalCase + `Model` | `OrderModel` |
| ORM model | PascalCase + `Record` | `OrderRecord` |
| Schema | PascalCase + `Request` or `Response` | `CreateOrderRequest` |
| External integration | `{name}_service.py`, `{name}_schema.py` | `payment_service.py` |

## Wiring

Register the router in `app/main.py`. Import the ORM module in `migrations/env.py` so autogenerate sees it.
