# Quickstart: API base

```bash
cd applications/hematdaya-api
make install
make run-dependencies
make migrate
make run
curl localhost:8000/health/live
curl localhost:8000/health/ready
curl localhost:8000/api/v1/capabilities
make check
```

Use `make run PORT=8010` if port 8000 is taken.
