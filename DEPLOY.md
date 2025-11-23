# 🚀 Guía de Despliegue - Cotizador TDV

## Estructura de Despliegue

El proyecto utiliza **Docker Compose** para desplegar frontend (Next.js) y backend (FastAPI/Python) juntos.

### 📁 Archivos importantes:
- `.env` - Variables de entorno (NO se sube a Git)
- `.env.example` - Template de variables
- `docker-compose.yml` - Configuración de servicios
- `validate-env.sh` - Script para validar .env
- `deploy.sh` - Script automatizado de despliegue
- `frontend/Dockerfile` - Imagen del frontend
- `backend/Dockerfile` - Imagen del backend

---

## 🔧 Pasos para Desplegar

### 1️⃣ Preparar el Archivo .env

```bash
# Copiar template a .env
cp .env.example .env

# Editar con tus valores reales
nano .env  # o tu editor preferido
```

**Variables REQUERIDAS en .env:**
```env
# Backend
API_HOST=0.0.0.0
API_PORT=8000
DB_HOST=tu-db-host.rds.amazonaws.com
DB_PORT=5432
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña
DB_NAME=cotizador_db
DB_SCHEMA=public
SSLMODE=require

# Frontend
INTERNAL_API_URL=http://backend:8000
```

### 2️⃣ Validar Variables de Entorno

```bash
# Este script verifica que el .env existe y tiene todas las variables necesarias
bash validate-env.sh
```

**Salida esperada:**
```
✅ Archivo .env encontrado
✅ API_HOST configurada
✅ API_PORT configurada
✅ DB_HOST configurada
...
✅ Validación completada exitosamente
```

### 3️⃣ Desplegar con Docker Compose

**Opción A: Despliegue Automatizado** (Recomendado)
```bash
bash deploy.sh
```

Este script automáticamente:
- ✅ Valida el .env
- ✅ Detiene despliegues anteriores
- ✅ Construye las imágenes Docker
- ✅ Inicia los contenedores
- ✅ Muestra el estado de los servicios

**Opción B: Despliegue Manual**
```bash
# Validar primero
bash validate-env.sh

# Construir e iniciar
docker-compose up -d --build

# Ver estado
docker-compose ps
```

---

## 🐛 Solucionar Problemas

### Error: "Resource not found 404"

**Causa:** Probablemente falta el archivo `.env`

**Solución:**
```bash
# 1. Verificar que .env existe
ls -la .env

# 2. Si no existe, crearlo
cp .env.example .env

# 3. Editar con valores reales
nano .env

# 4. Validar
bash validate-env.sh

# 5. Redesplegaer
bash deploy.sh
```

### Error: "Service unhealthy"

```bash
# Ver logs del frontend
docker-compose logs frontend

# Ver logs del backend
docker-compose logs backend

# Reintentar
docker-compose restart
```

### Error de Conexión a BD

```bash
# Verificar que las variables de BD son correctas
grep "DB_" .env

# Verificar conectividad a BD desde contenedor
docker-compose exec backend psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1"
```

---

## 📊 Monitoreo

### Ver estado de servicios:
```bash
docker-compose ps
```

### Ver logs en tiempo real:
```bash
# Todos los servicios
docker-compose logs -f

# Solo frontend
docker-compose logs -f frontend

# Solo backend
docker-compose logs -f backend
```

### Acceder a contenedores:
```bash
# Bash en frontend
docker-compose exec frontend bash

# Python en backend
docker-compose exec backend bash
```

---

## 🛑 Detener la Aplicación

```bash
# Detener todo
docker-compose down

# Detener y eliminar datos
docker-compose down -v

# Solo detener (sin eliminar)
docker-compose stop
```

---

## 🔑 Seguridad

⚠️ **NUNCA**:
- ❌ Commits el archivo `.env` a Git
- ❌ Compartas contraseñas en .env
- ❌ Uses credenciales de desarrollo en producción

✅ **SIEMPRE**:
- ✅ Usa secrets seguros en producción (AWS Secrets Manager, etc.)
- ✅ Valida .env antes de desplegar
- ✅ Rota contraseñas regularmente

---

## 📝 Logs en EC2

Si desplegas en EC2 y necesitas revisar logs después:

```bash
# Ver logs de docker-compose
docker-compose logs --tail=100 frontend
docker-compose logs --tail=100 backend

# Ver logs del sistema
journalctl -u docker.service -f

# Ver si el proceso está corriendo
ps aux | grep docker-compose
```

---

## ✅ Checklist de Despliegue

- [ ] Archivo `.env` creado y editado con valores reales
- [ ] `bash validate-env.sh` ejecutado exitosamente
- [ ] `bash deploy.sh` completado sin errores
- [ ] `docker-compose ps` muestra 2 servicios "Up"
- [ ] Frontend accesible en http://tu-ip:3000/cotizador
- [ ] Backend accesible en http://tu-ip:8000/health
- [ ] Logs no muestran errores
