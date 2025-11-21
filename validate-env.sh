#!/bin/bash

# ✨ Script para validar variables de entorno antes de desplegar

set -e

echo "🔍 Validando configuración de variables de entorno..."

# Verificar que existe el archivo .env
if [ ! -f .env ]; then
    echo "❌ ERROR: Archivo .env no encontrado"
    echo ""
    echo "📋 Solución:"
    echo "   1. Copia .env.example a .env:"
    echo "      cp .env.example .env"
    echo "   2. Edita .env y reemplaza los valores placeholder con tus valores reales"
    echo ""
    exit 1
fi

echo "✅ Archivo .env encontrado"
echo ""

# Variables requeridas para docker-compose
REQUIRED_VARS=(
    "API_HOST"
    "API_PORT"
    "DB_HOST"
    "DB_PORT"
    "DB_USER"
    "DB_PASSWORD"
    "DB_NAME"
    "DB_SCHEMA"
    "SSLMODE"
)

# Variables recomendadas
RECOMMENDED_VARS=(
    "INTERNAL_API_URL"
)

echo "🔐 Verificando variables REQUERIDAS..."
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=" .env; then
        MISSING_VARS+=("$var")
        echo "   ❌ $var no encontrada"
    else
        echo "   ✅ $var configurada"
    fi
done

echo ""

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "❌ ERROR: Faltan las siguientes variables requeridas:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "📋 Edita .env y asegúrate de que estas variables estén presentes"
    exit 1
fi

echo "⚠️  Verificando variables RECOMENDADAS..."
for var in "${RECOMMENDED_VARS[@]}"; do
    if ! grep -q "^${var}=" .env; then
        echo "   ⚠️  $var no encontrada (recomendada)"
    else
        echo "   ✅ $var configurada"
    fi
done

echo ""
echo "✅ Validación completada exitosamente"
echo "📦 Listo para desplegar con: docker-compose up -d"
