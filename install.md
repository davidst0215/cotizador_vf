# Guía de Instalación - Sistema Cotizador TDV Expert

## 🎯 Requisitos Previos

### Sistema Operativo

- **Windows 10/11** (recomendado)
- **Linux Ubuntu 20.04+** (compatible)
- **macOS 12+** (compatible)

### Software Base Requerido

- **Python 3.8 o superior** ✅
- **Node.js 16.x o superior** ✅
- **npm 8.x o superior** ✅
- **Git** (para clonar repositorio)

### Acceso a Base de Datos

- **SQL Server TDV** accesible
- **Credenciales de conexión** válidas
- **Puertos de red** abiertos (1433 para SQL Server)

## 🚀 Instalación Paso a Paso

### 1. Clonar o Extraer el Proyecto

#### Opción A: Si tienes Git

```bash
git clone [URL_DEL_REPOSITORIO]
cd COSTEO_TDV
```

#### Opción B: Si tienes el archivo comprimido

```bash
# Extraer el archivo .zip/.rar
# Navegar al directorio extraído
cd COSTEO_TDV
```

### 2. Verificar Estructura del Proyecto

```bash
# Deberías ver esta estructura
COSTEO_TDV/
├── backend/
├── frontend/
├── db_ops/
├── README.md
└── install.md
```

## 🐍 Configuración del Backend (Python/FastAPI)

### Paso 1: Navegar al Backend

```bash
cd backend
```

### Paso 2: Crear Entorno Virtual

#### En Windows:

```cmd
python -m venv venv
venv\Scripts\activate
```

#### En Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### Paso 3: Verificar Entorno Activo

```bash
# Deberías ver (venv) al inicio del prompt
(venv) C:\...\COSTEO_TDV\backend>
```

### Paso 4: Actualizar pip

```bash
python -m pip install --upgrade pip
```

### Paso 5: Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Paso 6: Verificar Instalación

```bash
# Verificar FastAPI
python -c "import fastapi; print('FastAPI instalado correctamente')"

# Verificar conexión SQL Server
python -c "import pyodbc; print('PYODBC instalado correctamente')"
```

### Paso 7: Configurar Variables de Entorno

#### Crear archivo .env

```bash
# En Windows
copy NUL .env

# En Linux/macOS
touch .env
```

#### Contenido del archivo .env

```env
# Configuración Base de Datos TDV
DB_SERVER=131.107.20.77
DB_PORT=1433
DB_USERNAME=CHSAYA01
DB_PASSWORD=NewServerAz654@!
DB_DATABASE=TDV

# Configuración API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
LOG_LEVEL=INFO

# Configuración CORS (separar con comas)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Cache (opcional)
CACHE_TTL=3600
```

### Paso 8: Crear Directorio de Logs

```bash
mkdir logs
# Se creará automáticamente el archivo tdv_cotizador.log al iniciar
```

### Paso 9: Probar Conexión a Base de Datos

```bash
python -c "
from config import settings
from database import tdv_queries
try:
    health = tdv_queries.health_check()
    print('✅ Conexión a BD exitosa:', health)
except Exception as e:
    print('❌ Error de conexión:', e)
"
```

### Paso 10: Iniciar el Backend

```bash
python main.py
```

**¡El backend debería iniciarse en http://localhost:8000!**

## 🌐 Configuración del Frontend (Next.js/TypeScript)

### Paso 1: Abrir Nueva Terminal

```bash
# Mantener el backend corriendo y abrir nueva terminal
# Navegar al directorio raíz del proyecto
cd COSTEO_TDV
```

### Paso 2: Navegar al Frontend

```bash
cd frontend
```

### Paso 3: Verificar Node.js y npm

```bash
node --version    # Debe ser 16.x o superior
npm --version     # Debe ser 8.x o superior
```

### Paso 4: Instalar Dependencias

```bash
npm install
```

### Paso 5: Configurar Variables de Entorno

#### Crear archivo .env.local

```bash
# Crear archivo de variables de entorno
# En Windows
echo. > .env.local

# En Linux/macOS
touch .env.local
```

#### Contenido del archivo .env.local

```env
# URL del backend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Configuración de desarrollo (opcional)
NODE_ENV=development
```

### Paso 6: Verificar Configuración

```bash
# Verificar que package.json existe y tiene las dependencias correctas
npm list --depth=0
```

### Paso 7: Iniciar el Frontend

```bash
npm run dev
```

**¡El frontend debería iniciarse en http://localhost:3000!**

## ✅ Verificación de Instalación

### 1. Verificar Backend

Abre tu navegador y ve a:

- **API Principal:** http://localhost:8000
- **Documentación:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### 2. Verificar Frontend

Abre tu navegador y ve a:

- **Aplicación:** http://localhost:3000

### 3. Prueba de Integración

En el frontend:

1. Llenar el formulario de cotización
2. Hacer clic en "Generar Cotización"
3. Verificar que aparece un resultado

## 🔧 Solución de Problemas Comunes

### Error: "python no es reconocido"

```bash
# En Windows, instalar Python desde python.org
# O usar Microsoft Store: buscar "Python"
```

### Error: "npm no es reconocido"

```bash
# Instalar Node.js desde nodejs.org
# Reiniciar terminal después de instalar
```

### Error: "No se puede conectar a la base de datos"

```bash
# Verificar credenciales en .env
# Verificar conectividad de red
ping 131.107.20.77

# Probar conexión con telnet
telnet 131.107.20.77 1433
```

### Error: "Puerto 8000 ya está en uso"

```bash
# En Windows
netstat -ano | findstr :8000
taskkill /PID [PID_NUMBER] /F

# En Linux/macOS
lsof -ti:8000 | xargs kill -9
```

### Error: "Puerto 3000 ya está en uso"

```bash
# Cambiar puerto en package.json o usar:
npm run dev -- --port 3001
```

### Error: "Module not found"

```bash
# Backend: Verificar entorno virtual activo
pip list

# Frontend: Reinstalar dependencias
rm -rf node_modules package-lock.json
npm install
```

### Error de CORS

```bash
# Verificar que CORS_ORIGINS en .env incluye el puerto del frontend
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## 🎛️ Configuración para Producción

### Backend en Producción

```bash
# Desactivar debug
DEBUG=false

# Cambiar host y puerto según necesidad
API_HOST=0.0.0.0
API_PORT=8000

# Configurar CORS para dominios de producción
CORS_ORIGINS=https://tu-dominio.com
```

### Frontend en Producción

```bash
# Build de producción
npm run build

# Iniciar en modo producción
npm start

# O usar servidor web como Nginx
npm run build
# Servir archivos desde carpeta 'dist/'
```

### Variables de Entorno de Producción

```env
# Backend
NODE_ENV=production
DEBUG=false
LOG_LEVEL=WARNING

# Frontend
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://api-tu-dominio.com
```

## 📊 Verificación de Logs

### Logs del Backend

```bash
# Ver logs en tiempo real
tail -f backend/logs/tdv_cotizador.log

# En Windows
type backend\logs\tdv_cotizador.log
```

### Logs del Frontend

```bash
# Los logs aparecen en la consola donde corriste npm run dev
# También en la consola del navegador (F12)
```

## 🔄 Scripts de Automatización

### Script de Instalación Completa (Windows)

```batch
@echo off
echo Instalando Backend...
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt

echo Instalando Frontend...
cd ..\frontend
npm install

echo ¡Instalación completa!
echo Para iniciar:
echo 1. cd backend && venv\Scripts\activate && python main.py
echo 2. En otra terminal: cd frontend && npm run dev
```

### Script de Instalación Completa (Linux/macOS)

```bash
#!/bin/bash
echo "Instalando Backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "Instalando Frontend..."
cd ../frontend
npm install

echo "¡Instalación completa!"
echo "Para iniciar:"
echo "1. cd backend && source venv/bin/activate && python main.py"
echo "2. En otra terminal: cd frontend && npm run dev"
```

## 📋 Lista de Verificación Post-Instalación

- [ ] Python 3.8+ instalado y funcionando
- [ ] Node.js 16+ instalado y funcionando
- [ ] Entorno virtual Python creado y activado
- [ ] Dependencias backend instaladas (requirements.txt)
- [ ] Dependencias frontend instaladas (npm install)
- [ ] Archivo .env creado con credenciales correctas
- [ ] Archivo .env.local creado para frontend
- [ ] Conexión a base de datos TDV exitosa
- [ ] Backend inicia en puerto 8000
- [ ] Frontend inicia en puerto 3000
- [ ] API docs accesibles en /docs
- [ ] Prueba de cotización exitosa

## 📞 Soporte de Instalación

### Información del Sistema

Para reportar problemas, incluir:

- Sistema operativo y versión
- Versión de Python (`python --version`)
- Versión de Node.js (`node --version`)
- Mensaje de error completo
- Logs relevantes

### Contacto

- **Equipo de Desarrollo:** SAYA INVESTMENTS
- **Documentación técnica:** Ver architecture.md.md
- **Manual de usuario:** Ver README.md

---

**Guía de instalación actualizada:** 2025
**Versión del sistema:** 2.0
**Compatibilidad:** Windows/Linux/macOS
