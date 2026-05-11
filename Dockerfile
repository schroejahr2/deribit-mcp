FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

COPY pyproject.toml README.md ./
COPY src ./src
COPY dashboard ./dashboard

# Install dependencies, create a non-root user, and prepare the data dir
# (the compose file mounts a host volume here; the host directory must be
# writable by UID 10001, e.g. `chown -R 10001:10001 ./data`).
RUN pip install -e . \
 && useradd --system --uid 10001 --create-home --home-dir /home/appuser appuser \
 && mkdir -p /data \
 && chown -R appuser:appuser /app /data

USER appuser

CMD ["python", "-m", "src"]
