#!/bin/sh
set -eux

# Create /tmp/secrets directory with proper permissions
mkdir -p /tmp/secrets
chmod 0700 /tmp/secrets

# Copy certificates to /tmp/secrets with correct permissions
if [ -f /.secrets/cotizador.crt ]; then
    cat /.secrets/cotizador.crt > /tmp/secrets/cotizador.crt
    chmod 0644 /tmp/secrets/cotizador.crt
fi

if [ -f /.secrets/cotizador.pk8 ] || [ -f /.secrets/cotizador.key ]; then
    if [ -f /.secrets/cotizador.pk8 ] && [ ! -f /tmp/secrets/cotizador.key ]; then
        # Convert pk8 to key if needed
        openssl pkcs8 -in /.secrets/cotizador.pk8 -out /tmp/secrets/cotizador.key -nocrypt
    elif [ -f /.secrets/cotizador.key ]; then
        # Copy existing key
        cat /.secrets/cotizador.key > /tmp/secrets/cotizador.key
    fi
    chmod 0600 /tmp/secrets/cotizador.key
fi

# Update environment to use /tmp/secrets
export PGSSLCERT=/tmp/secrets/cotizador.crt
export PGSSLKEY=/tmp/secrets/cotizador.key

exec uvicorn ${APP_MODULE:-smp}.main:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8000} --proxy-headers
