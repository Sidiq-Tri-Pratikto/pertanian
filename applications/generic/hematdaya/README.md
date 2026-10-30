# hematdaya

Electricity monitoring and evidence-based advice for household, business and industrial sites. Monitoring only: it never switches anything.

## Structure

| Path | Purpose |
|---|---|
| `applications/` | Deployable applications, each with its own README |
| `contracts/` | Generated API contract |
| `.specify/memory/constitution.md` | Project standards |
| `AGENTS.md` | Entry point for coding agents |
| `specs/` | Feature specs |
| `docs/` | Project documentation |

## Getting started

```bash
cd applications/hematdaya-api
make install
make run-dependencies
make migrate
make run
```

See [the service README](applications/hematdaya-api/README.md).

```bash
cd applications/hematdaya-mobile
nvm use
make install
make run
```

See [the mobile README](applications/hematdaya-mobile/README.md).
