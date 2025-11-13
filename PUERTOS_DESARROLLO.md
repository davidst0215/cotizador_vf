# Puertos de Desarrollo - Cotizador TDV

## Configuracion Estable de Puertos

Este documento establece los puertos fijos para desarrollo local del sistema cotizador TDV.

### Puertos Asignados

| Servicio | Puerto | URL de Acceso |
|----------|--------|---------------|
| **Backend (FastAPI)** | 8000 | http://localhost:8000 |
| **Frontend (Next.js)** | 3000 | http://localhost:3000 |

---

## Archivos de Configuracion

### 1. Backend - Puerto 8000

#### `.env` (raiz del proyecto)
```env
API_HOST=0.0.0.0
API_PORT=8000
NEXT_PUBLIC_API_URL=http://localhost:8000
INTERNAL_API_URL=http://backend:8000
```

#### `backend/.env`
```env
API_HOST=0.0.0.0
API_PORT=8000
```

#### `backend/src/smp/config.py`
```python
api_host: str = "0.0.0.0"
api_port: int = 8000
```

#### `backend/src/smp/main.py`
El servidor se inicia usando los valores de configuracion:
```python
uvicorn.run(
    "smp.main:app",
    host=settings.api_host,  # 0.0.0.0
    port=settings.api_port,  # 8000
    reload=settings.debug,
    log_level=settings.log_level.lower(),
)
```

---

### 2. Frontend - Puerto 3000

#### `frontend/.env.local`
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### `frontend/package.json`
```json
"scripts": {
  "dev": "next dev",
  "start": "next start -p 3000",
  "preview": "next start --port 3000"
}
```

#### `frontend/src/libs/api.ts`
La API del frontend determina automaticamente la URL base:
- **Lado cliente (navegador)**: Usa `NEXT_PUBLIC_API_URL` -> http://localhost:8000
- **Lado servidor (SSR)**: Usa `INTERNAL_API_URL` -> http://backend:8000 (para Docker)

---

### 3. Docker Compose

#### `docker-compose.yml`
```yaml
services:
  backend:
    ports:
      - "8000:8000"
    environment:
      - API_PORT=8000

  frontend:
    ports:
      - "3000:3000"
    environment:
      - INTERNAL_API_URL=http://backend:8000
```

---

## Como Iniciar los Servicios

### Opcion 1: Desarrollo Local (Sin Docker)

#### Backend
```bash
cd backend
python -m uvicorn src.smp.main:app --host 0.0.0.0 --port 8000 --reload
```

Endpoints disponibles:
- API: http://localhost:8000
- Documentacion Swagger: http://localhost:8000/docs
- Documentacion ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

#### Frontend
```bash
cd frontend
npm run dev
```

Aplicacion disponible en:
- Frontend: http://localhost:3000

---

### Opcion 2: Docker Compose

```bash
docker-compose up --build
```

Servicios disponibles:
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000

---

## Verificacion de Estado

### Backend (Puerto 8000)
```bash
curl http://localhost:8000/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "database": "connected",
  "tablas": { ... },
  "timestamp": "2025-11-12T..."
}
```

### Frontend (Puerto 3000)
```bash
curl http://localhost:3000
```

Deberia retornar el HTML de la aplicacion Next.js.

---

## Resolucion de Problemas

### Puerto ya en uso

Si un puerto esta ocupado, identifica el proceso:

**Windows:**
```bash
netstat -ano | findstr :8000
netstat -ano | findstr :3000
```

Matar proceso por PID:
```bash
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
lsof -i :8000
lsof -i :3000
```

Matar proceso:
```bash
kill -9 <PID>
```

### Backend no arranca en 8000

1. Verifica que `.env` tenga `API_PORT=8000`
2. Verifica que `backend/.env` tenga `API_PORT=8000`
3. Reinicia el servidor backend

### Frontend no conecta al backend

1. Verifica que `frontend/.env.local` tenga `NEXT_PUBLIC_API_URL=http://localhost:8000`
2. Verifica que el backend este corriendo en puerto 8000
3. Abre DevTools del navegador y verifica que las peticiones vayan a `http://localhost:8000`

---

## CORS - Origenes Permitidos

El backend acepta conexiones desde estos origenes (configurado en `.env`):

```env
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3002,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3002
```

Si cambias el puerto del frontend, actualiza esta variable.

---

## Notas Importantes

1. **NO cambiar estos puertos** - Estan estandarizados para consistencia en desarrollo
2. **Puerto 8000 (Backend)** - FastAPI con Uvicorn
3. **Puerto 3000 (Frontend)** - Next.js en modo desarrollo
4. **0.0.0.0 vs localhost**:
   - Backend usa `0.0.0.0` para aceptar conexiones de cualquier interfaz
   - Frontend usa `localhost:8000` para conectarse al backend desde el navegador
5. **Docker networking**: El frontend usa `http://backend:8000` internamente (nombre del servicio Docker)

---

## Cambios Realizados

**Fecha: 2025-11-12**

- Corregido `frontend/.env.local` de puerto 8001 a 8000
- Documentacion creada para estandarizar puertos de desarrollo

---

**Mantenido por**: Sistema de Cotizador TDV
**Ultima actualizacion**: 2025-11-12
