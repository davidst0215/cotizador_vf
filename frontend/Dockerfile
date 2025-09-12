# ---- Build stage ----
ARG NODE_BASE_IMAGE=node:20-alpine
ARG APP_USER=appuser
ARG APP_UID=1001
ARG PORT=3000
FROM ${NODE_BASE_IMAGE} AS builder

WORKDIR /app
# Disable Next telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund

COPY . .
RUN set -eux; \
    npm run build


# ---- Final stage (runtime) ----
FROM ${NODE_BASE_IMAGE}
ARG APP_USER
ARG APP_UID

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

# Install only production dependencies
WORKDIR /app
# Create non-root user and minimal runtime packages
# hadolint ignore=DL3018
RUN set -eux; \
    addgroup -S ${APP_USER}; \
    adduser  -S -G ${APP_USER} -u ${APP_UID} ${APP_USER}; \
    apk add --no-cache ca-certificates; \
    mkdir -p /var/log && chown -R ${APP_USER}:${APP_USER} /var/log

# Copy build output
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

USER ${APP_USER}
EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- --timeout=2 http://127.0.0.1:${PORT}/_next/static/ || exit 1

CMD ["node", "server.js"]
