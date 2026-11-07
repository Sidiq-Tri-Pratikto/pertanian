FROM python:3.13-slim AS build

ENV UV_PYTHON_DOWNLOADS=never
RUN pip install --no-cache-dir uv
WORKDIR /srv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project


FROM python:3.13-slim AS runtime

# Pick up DSA-6613-1 while the slim image still carries the older zlib.
RUN apt-get update \
    && apt-get install -y --no-install-recommends --only-upgrade zlib1g \
    && rm -rf /var/lib/apt/lists/*

# The app runs from .venv and never needs pip, whose vendored packages fail the image scan.
RUN python -m pip uninstall --yes pip
RUN useradd --system --uid 1000 --no-create-home appuser
WORKDIR /srv
COPY --from=build /srv/.venv .venv
COPY alembic.ini entrypoint.sh ./
COPY migrations migrations
COPY app app

ENV PATH="/srv/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER appuser
EXPOSE 8000
HEALTHCHECK --start-period=30s CMD ["python", "-c", "import urllib.request as u; u.urlopen('http://localhost:8000/health/live', timeout=3)"]
ENTRYPOINT ["./entrypoint.sh"]
