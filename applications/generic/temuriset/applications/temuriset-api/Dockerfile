FROM ghcr.io/astral-sh/uv:0.11.3@sha256:90bbb3c16635e9627f49eec6539f956d70746c409209041800a0280b93152823 AS uv

FROM python:3.13-alpine@sha256:7984cf56ceaddebe4fefeb75d64000b9f45d8b77b11a09b24524da6cdc3af0c8 AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy
WORKDIR /srv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.13-alpine@sha256:7984cf56ceaddebe4fefeb75d64000b9f45d8b77b11a09b24524da6cdc3af0c8 AS runtime
RUN python -m pip uninstall --yes pip && adduser -S -D -H -u 1000 appuser
WORKDIR /srv
COPY --from=build /srv/.venv .venv
COPY alembic.ini entrypoint.sh ./
COPY migrations migrations
COPY app app
COPY benchmarks/fixtures/retrieval.json benchmarks/fixtures/retrieval.json
ENV PATH="/srv/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER appuser
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
