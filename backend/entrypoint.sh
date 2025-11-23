#!/bin/sh
set -eux

# Create /tmp/secrets directory with proper permissions
mkdir -p /tmp/secrets
chmod 0700 /tmp/secrets

echo "📋 Configurando certificados SSL para PostgreSQL..."

# Check if SSL is required
PGSSLMODE="${PGSSLMODE:-prefer}"
if [ "$PGSSLMODE" = "require" ]; then
    echo "🔐 PGSSLMODE=require detected - certificados son OBLIGATORIOS"
    REQUIRE_CERTS=true
else
    echo "ℹ️  PGSSLMODE=$PGSSLMODE - certificados opcionales"
    REQUIRE_CERTS=false
fi

CERTS_FOUND=false

# Copy certificates to /tmp/secrets with correct permissions
if [ -f /.secrets/cotizador.crt ]; then
    echo "✅ Encontrado: cotizador.crt"
    cat /.secrets/cotizador.crt > /tmp/secrets/cotizador.crt
    chmod 0644 /tmp/secrets/cotizador.crt
    CERTS_FOUND=true
else
    if [ "$REQUIRE_CERTS" = true ]; then
        echo "❌ ERROR: Certificado cotizador.crt no encontrado en /.secrets/"
        echo "   PGSSLMODE=require requiere que los certificados estén disponibles"
        echo "   Asegúrate de montar ./.secrets en /.secrets en docker-compose.yml"
        exit 1
    else
        echo "⚠️  Certificado cotizador.crt no encontrado en /.secrets/ (opcional)"
    fi
fi

if [ -f /.secrets/cotizador.pk8 ] || [ -f /.secrets/cotizador.key ]; then
    if [ -f /.secrets/cotizador.pk8 ] && [ ! -f /tmp/secrets/cotizador.key ]; then
        echo "✅ Encontrado: cotizador.pk8 (convirtiendo a .key)"
        # Convert pk8 to key if needed
        openssl pkcs8 -in /.secrets/cotizador.pk8 -out /tmp/secrets/cotizador.key -nocrypt
        CERTS_FOUND=true
    elif [ -f /.secrets/cotizador.key ]; then
        echo "✅ Encontrado: cotizador.key"
        # Copy existing key
        cat /.secrets/cotizador.key > /tmp/secrets/cotizador.key
        CERTS_FOUND=true
    fi
    chmod 0600 /tmp/secrets/cotizador.key
else
    if [ "$REQUIRE_CERTS" = true ]; then
        echo "❌ ERROR: Certificado de clave no encontrado (cotizador.key o cotizador.pk8)"
        echo "   PGSSLMODE=require requiere que los certificados estén disponibles"
        exit 1
    else
        echo "⚠️  Certificado de clave no encontrado (opcional)"
    fi
fi

# Verify certificates if required
if [ "$REQUIRE_CERTS" = true ] && [ "$CERTS_FOUND" = false ]; then
    echo "❌ ERROR: Certificados requeridos pero no encontrados"
    exit 1
fi

# Update environment to use /tmp/secrets if certificates exist
if [ "$CERTS_FOUND" = true ]; then
    export PGSSLCERT=/tmp/secrets/cotizador.crt
    export PGSSLKEY=/tmp/secrets/cotizador.key
    echo "✅ Certificados SSL configurados correctamente"
else
    echo "ℹ️  Ejecutando sin certificados SSL (PGSSLMODE=$PGSSLMODE)"
fi

echo "🚀 Iniciando uvicorn..."
exec uvicorn ${APP_MODULE:-smp}.main:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8000} --proxy-headers
