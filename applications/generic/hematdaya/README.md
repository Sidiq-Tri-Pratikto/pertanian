# HematDaya

Electricity monitoring and evidence-based advice for household, business and industrial sites. Monitoring only: it never switches anything.

This is the base release: real navigation, design tokens and the API contract, with "Segera hadir" for every planned feature. The roadmap in [`docs/roadmap/`](docs/roadmap/README.md) adds the features one pull request at a time.

## Quick start

You need [uv](https://docs.astral.sh/uv/getting-started/installation/), [Docker](https://docs.docker.com/get-started/get-docker/) (running) and [nvm](https://github.com/nvm-sh/nvm) or Node 24.

From the root of the pertanian repository:

```bash
cd applications/generic/hematdaya
./local-start.sh
```

Every command below runs from this folder.

This installs everything, starts Postgres, applies migrations, and runs the API and the app. The first run takes a few minutes. Press `Ctrl+C` to stop it all.

| Open | For |
|---|---|
| http://localhost:8081 | The app |
| http://localhost:8000/docs | API reference |
| http://localhost:8000/health/ready | API and database health |
| http://localhost:8000/api/v1/capabilities | What this deployment supports |

To confirm it works, the Beranda tab in the app shows the service status, or from another terminal:

```bash
curl http://localhost:8000/health/ready
```

### On a phone

Install Expo Go, connect the phone to the same Wi-Fi as your computer, then scan the QR code:

```bash
./local-start.sh phone
```

Expo Go must support Expo SDK 58. If yours does not, use the web app until native builds arrive in specs 003 and 042.

### Run each part yourself

Use two terminals when you want to restart one side without the other. The script does exactly this.

```bash
cd applications/hematdaya-api
make install
make run-dependencies
make migrate
make run
```

```bash
cd applications/hematdaya-mobile
nvm use
make install
make web
```

## Run the tests

Install once, from the repository root:

```bash
nvm use
make setup
```

Then pick what you need:

| Command | Runs | Needs |
|---|---|---|
| `make test` | API unit tests and mobile tests, about 20 seconds | Nothing else |
| `make check` | Everything a pull request must pass: lint, types, all tests, coverage gates, roadmap traceability | Docker |
| `make stop` | Stops the Postgres that `make check` leaves running | |

To run one test while you work:

```bash
cd applications/hematdaya-api
uv run pytest tests/unit/health/test_health.py -v
uv run pytest tests -k capabilities
```

```bash
cd applications/hematdaya-mobile
npx jest tests/navigation.test.tsx
npx jest --watch
```

Each application README lists what its tests cover: [API](applications/hematdaya-api/README.md#testing), [mobile](applications/hematdaya-mobile/README.md#testing).

## Troubleshooting

| You see | Do this |
|---|---|
| `Docker is not running` | Start Docker, then run the script again |
| `Port 8000 is in use` | `API_PORT=8010 ./local-start.sh` |
| `Port 8081 is in use` | `WEB_PORT=8082 ./local-start.sh` |
| `Postgres did not start` | Something else holds port 5432. Stop it, then run the script again |
| `Node 24 is required` | Install nvm, or Node 24 directly |
| Beranda shows `Layanan belum tersedia` | Check `curl http://localhost:8000/health/ready`. If you run the parts yourself, set `EXPO_PUBLIC_API_URL` when the API is not on port 8000 |
| A phone cannot reach the service | Use the same Wi-Fi, and allow the API port through your firewall. If the wrong address was picked: `LAN_IP=192.168.1.20 ./local-start.sh phone` |
| A changed `.env` has no effect | Restart. Expo reads `EXPO_PUBLIC_*` values when it builds the bundle |
| `make check` fails on an Alembic or connection error | Run it from the repository root, which starts Postgres first |

## Project layout

| Path | Purpose |
|---|---|
| `applications/hematdaya-api/` | FastAPI service. [README](applications/hematdaya-api/README.md) |
| `applications/hematdaya-mobile/` | Expo app for Android, iOS and web. [README](applications/hematdaya-mobile/README.md) |
| `contracts/` | Generated API contract |
| `.github/workflows/hematdaya-*.yml` | CI, at the root of the pertanian repository because GitHub reads workflows only there |
| `specs/` | One spec and plan per pull request, 001 to 046 |
| `docs/roadmap/` | Milestones, dependencies, architecture decisions, traceability. **Start here for the next PR** |
| `docs/product/` | PRD in English and Indonesian, design handoff |
| `docs/design/` | Design system reference |
| `docs/reference/prototype/` | Browser prototype: behaviour reference and oracle source |
| `.specify/memory/constitution.md` | Project standards |
| `AGENTS.md` | Entry point for coding agents. Open your agent in this folder so its rules and Spec Kit resolve |
