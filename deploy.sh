#!/bin/bash

# 🚀 Script de despliegue para Cotizador TDV
# Uso: ./deploy.sh

set -e

echo "🚀 Iniciando despliegue de Cotizador TDV..."
echo ""

# ✨ Paso 1: Validar variables de entorno
echo "📋 Paso 1/4: Validando variables de entorno..."
if [ ! -f validate-env.sh ]; then
    echo "❌ ERROR: validate-env.sh no encontrado"
    exit 1
fi

bash validate-env.sh
echo ""

# ✨ Paso 2: Detener contenedores anteriores (si existen)
echo "📋 Paso 2/4: Limpiando despliegues anteriores..."
docker-compose down || true
echo "✅ Despliegue anterior detenido"
echo ""

# ✨ Paso 3: Construir e iniciar los contenedores
echo "📋 Paso 3/4: Construyendo e iniciando contenedores..."
docker-compose up -d --build
echo "✅ Contenedores iniciados"
echo ""

# ✨ Paso 4: Mostrar estado
echo "📋 Paso 4/4: Verificando estado de servicios..."
sleep 5
docker-compose ps
echo ""

echo "✅ Despliegue completado exitosamente!"
echo ""
echo "📍 Acceso a la aplicación:"
echo "   Frontend: http://localhost:3000/cotizador"
echo "   Backend API: http://localhost:8000"
echo ""
echo "📊 Ver logs:"
echo "   Frontend: docker-compose logs -f frontend"
echo "   Backend: docker-compose logs -f backend"
echo ""
echo "⛔ Detener aplicación:"
echo "   docker-compose down"
