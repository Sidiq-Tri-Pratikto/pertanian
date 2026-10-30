# hematdaya

Electricity monitoring and evidence-based advice for household, business and industrial sites. Monitoring only: it never switches anything.

## Structure

| Path | Purpose |
|---|---|
| `applications/` | Deployable applications, each with its own README |
| `contracts/` | Generated API contract |
| `.specify/memory/constitution.md` | Project standards |
| `AGENTS.md` | Entry point for coding agents |
| `specs/` | One spec and plan per pull request, 001 to 046 |
| `docs/roadmap/` | Milestones, dependency graph, architecture decisions, traceability. **Start here for the next PR** |
| `docs/product/` | PRD in English and Indonesian, design handoff |
| `docs/design/` | Design system reference |
| `docs/reference/prototype/` | Browser prototype: behaviour reference and oracle source |

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
