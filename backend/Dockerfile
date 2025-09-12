# ---- Build stage ----
ARG PYTHON_BASE_IMAGE=python:3.12-alpine3.22
ARG APP_USER=appuser
ARG APP_UID=1001
ARG UV_VERSION=0.8.17
ARG APP_MODULE=smp
FROM ${PYTHON_BASE_IMAGE} AS builder

# meta
ARG UV_VERSION
ENV PIP_NO_CACHE_DIR=1 \
    VENV_PATH=/opt/venv \
    PATH=/opt/venv/bin:$PATH

# Install build dependencies and uv
# hadolint ignore=DL4006,DL3018
RUN set -eux pipefail; \
    apk add --no-cache build-base curl jq; \
    \
    UV_REPO=astral-sh/uv; \
    UV_URL="https://api.github.com/repos/$UV_REPO/releases/latest"; \
    UV_VERSION=$(curl -s "$UV_URL" | jq -r .tag_name || echo "${UV_VERSION}"); \
    curl -fsSL -o /tmp/uv-alpine.tar.gz \
        "https://github.com/$UV_REPO/releases/download/${UV_VERSION}/uv-${UV_VERSION}-x86_64-unknown-linux-musl.tar.gz" \
    && tar -xzf /tmp/uv-alpine.tar.gz -C /tmp && mv /tmp/uv /usr/local/bin/uv \
    && chmod +x /usr/local/bin/uv; \
    # create virtual env (using stdlib venv for smaller, reproducible venv)
    python -m venv ${VENV_PATH}; \
    ${VENV_PATH}/bin/pip install -U pip setuptools wheel; \
    # cleanup downloaded files
    rm -f /tmp/uv-alpine.tar.gz || true

# odbc deps
# hadolint ignore=DL3018
RUN set -eux; \
    apk add --no-cache python3-dev freetds freetds-dev \
        libpq postgresql-dev psqlodbc \
        unixodbc unixodbc-dev

WORKDIR /src
COPY pyproject.toml pyproject.lock* uv.lock* src/ ./

# uv produce a concrete requirements file from pyproject (uv.lock based)
# Then pip-install into venv
# hadolint ignore=DL3013
RUN set -eux; \
    # produce requirements.txt
    if command -v uv >/dev/null 2>&1; then \
        uv pip compile pyproject.toml -o requirements.txt; \
    else \
        # if uv missing, fallback to pip-compile (if present) or install from pyproject directly
        python -m pip install pip-tools && pip-compile pyproject.toml -o requirements.txt; \
    fi; \
    ${VENV_PATH}/bin/pip install --no-deps --no-cache-dir -r requirements.txt; \
    # install your package into the venv (editable not needed)
    ${VENV_PATH}/bin/pip install --no-cache-dir .; \
    # remove build-time caches that may remain
    find ${VENV_PATH} -name '*.pyc' -delete


# ---- Final stage (runtime) ----
FROM ${PYTHON_BASE_IMAGE}
ARG APP_USER
ARG APP_UID
ARG APP_MODULE
ENV VENV_PATH=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# create unprivileged user and minimal runtime packages (ca-certificates)
# hadolint ignore=DL3018
RUN set -eux; \
    adduser -D -u ${APP_UID} ${APP_USER}; \
    apk add --no-cache ca-certificates; \
    mkdir -p /app /var/log /tmp; \
    chown -R ${APP_USER}:${APP_USER} /app /var/log /tmp

# hadolint ignore=DL3018
RUN set -eux; \
    apk add --no-cache freetds libpq psqlodbc libstdc++ unixodbc

# copy only the venv and application; preserve ownership for security
COPY --from=builder --chown=${APP_USER}:${APP_USER} /opt/venv /opt/venv
COPY --from=builder --chown=${APP_USER}:${APP_USER} /src /app

WORKDIR /app
USER ${APP_USER}

# Lightweight healthcheck implemented with the bundled python binary (no extra packages required).
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import sys,urllib.request as u; \
try: \
  r=u.urlopen('http://127.0.0.1:8000/health', timeout=2); \
  sys.exit(0 if r.getcode()==200 else 1); \
except: sys.exit(1)"

EXPOSE 8000

# Use exec form; user can override CMD at runtime.
CMD ["uvicorn", "${APP_MODULE}.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
