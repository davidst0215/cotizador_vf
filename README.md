# Sistema Cotizador TDV Expert

**Versión:** 2.0
**Arquitectura:** FastAPI + Next.js + TypeScript
**Base de Datos:** PostgreSQL (TDV Real Database)
**Colaborador:** davidst0215

## 📋 Descripción del Proyecto

El Sistema Cotizador TDV Expert es una aplicación web completa para cotización inteligente de prendas textiles basada en metodología WIP (Work In Process). El sistema utiliza datos históricos reales de producción para generar cotizaciones precisas con factores de ajuste basados en análisis de TDV.

### 🎯 Características Principales

- **Cotización Inteligente:** Algoritmo de cotización basado en datos históricos reales
- **Auto-completado:** Sugerencias automáticas para estilos recurrentes
- **Análisis de Costos:** Desglose detallado de componentes de costo
- **Factores de Ajuste:** Ajustes automáticos por lote, esfuerzo, estilo y marca
- **Rutas Textiles:** Recomendaciones de WIPs por tipo de prenda
- **Análisis Histórico:** Benchmarking basado en datos de producción
- **API RESTful:** Endpoints completos para integración
- **Interfaz Moderna:** Frontend responsive con Next.js y TypeScript

## 🏗️ Arquitectura del Sistema

### Backend (FastAPI)

- **main.py:** API principal con endpoints REST
- **database.py:** Conexión y queries a SQL Server
- **models.py:** Modelos Pydantic para validación
- **config.py:** Configuración y factores de ajuste
- **utils.py:** Lógica de cotización y cálculos
- **backtesting.py:** Análisis y validación de resultados

### Frontend (Next.js + TypeScript)

- **SistemaCotizadorTDV.tsx:** Componente principal de la interfaz
- **Tailwind CSS:** Framework de estilos
- **Lucide React:** Iconografía

### Base de Datos

- **COSTO_OP_DETALLE:** Datos históricos de órdenes de producción
- **RESUMEN_WIP_POR_PRENDA:** Información de WIPs por tipo de prenda
- **HISTORIAL_ESTILOS:** Registro de estilos fabricados

## 🚀 Instalación y Configuración

### Requisitos del Sistema

- **Python:** 3.8 o superior
- **Node.js:** 16.x o superior
- **SQL Server:** Conexión a base de datos TDV
- **Sistema Operativo:** Windows/Linux/macOS

### 1. Configuración del Backend

```bash
# Navegar al directorio backend
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual (Windows)
venv\Scripts\activate

# Activar entorno virtual (Linux/macOS)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
# Crear archivo .env con:
# DB_SERVER=131.107.20.77
# DB_USERNAME=CHSAYA01
# DB_PASSWORD=NewServerAz654@!
# DB_DATABASE=TDV
```

### 2. Configuración del Frontend

```bash
# Navegar al directorio frontend
cd frontend

# Instalar dependencias
npm install

# Configurar variables de entorno
# Crear archivo .env.local con:
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

## ▶️ Ejecución del Sistema

### Iniciar Backend

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Iniciar Frontend

```bash
cd frontend
npm run dev
```

### Acceder a la Aplicación

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **API Alternative Docs:** http://localhost:8000/redoc

## 🔧 Funcionalidades del Sistema

### 1. Cotización de Prendas

- **Entrada de Datos:** Cliente, temporada, cantidad, familia de productos, tipo de prenda
- **Auto-completado:** Sugerencias automáticas para estilos recurrentes
- **Verificación de Estilos:** Categorización automática (Nuevo/Recurrente/Muy Recurrente)
- **Cálculo Inteligente:** Algoritmo basado en datos históricos reales

### 2. Análisis de Costos

- **Desglose Detallado:** Textil, manufactura, avíos, materia prima, gastos indirectos
- **Factores de Ajuste:**
  - **Lote:** Micro/Pequeño/Mediano/Grande/Masivo
  - **Esfuerzo:** Bajo/Medio/Alto (basado en complejidad)
  - **Estilo:** Nuevo/Recurrente/Muy Recurrente
  - **Marca:** Factores específicos por cliente

### 3. Rutas Textiles

- **WIPs Recomendadas:** Selección automática de Work In Process
- **Costos Actualizados:** Información en tiempo real de costos de WIPs
- **Optimización:** Sugerencias de rutas más eficientes

### 4. Análisis Histórico

- **Benchmarking:** Comparación con datos históricos
- **Tendencias:** Análisis de costos por períodos
- **Volúmenes:** Información de producción histórica

## 📊 Endpoints de la API

### Generales

- `GET /` - Información del sistema
- `GET /health` - Estado de la aplicación y base de datos
- `GET /configuracion` - Configuración del sistema

### Cotización

- `POST /cotizar` - Generar cotización
- `POST /ops-utilizadas-cotizacion` - OPs utilizadas en cotización

### Búsqueda y Verificación

- `GET /verificar-estilo-completo/{codigo_estilo}` - Verificación completa de estilo
- `GET /buscar-estilos/{codigo_estilo}` - Búsqueda de estilos similares
- `GET /autocompletar-estilo/{codigo_estilo}` - Auto-completado de información

### Datos Maestros

- `GET /clientes` - Lista de clientes disponibles
- `GET /familias-productos` - Familias de productos
- `GET /tipos-prenda/{familia}` - Tipos de prenda por familia

### Configuración de WIPs

- `GET /wips-disponibles` - WIPs disponibles con costos
- `GET /ruta-textil-recomendada/{tipo_prenda}` - Ruta textil recomendada

### Análisis

- `GET /analisis-historico` - Análisis histórico por familia/tipo
- `GET /info-fechas-corrida` - Información de fechas de corrida
- `GET /versiones-calculo` - Versiones de cálculo disponibles

## 🗃️ Estructura de Base de Datos

### Tablas Principales

#### COSTO_OP_DETALLE

Contiene los datos históricos de órdenes de producción con todos los componentes de costo.

**Campos principales:**

- `estilo_propio`: Código del estilo
- `cliente`: Cliente/marca
- `familia_de_productos`: Familia del producto
- `tipo_de_producto`: Tipo de prenda
- `prendas_requeridas`: Cantidad producida
- `costo_textil`: Costo de textiles
- `costo_manufactura`: Costo de manufactura
- `costo_avios`: Costo de avíos
- `costo_materia_prima`: Costo de materia prima
- `costo_indirecto_fijo`: Costos indirectos fijos
- `gasto_administracion`: Gastos administrativos
- `gasto_ventas`: Gastos de ventas
- `esfuerzo_total`: Nivel de complejidad
- `version_calculo`: Versión del cálculo (FLUIDA/truncado)
- `fecha_corrida`: Fecha de procesamiento

#### RESUMEN_WIP_POR_PRENDA

Información de Work In Process (WIPs) por tipo de prenda.

**Campos principales:**

- `wip_id`: Identificador del WIP
- `nombre_wip`: Nombre del proceso
- `tipo_prenda`: Tipo de prenda aplicable
- `costo_actual`: Costo actual del WIP
- `disponible`: Estado de disponibilidad
- `grupo`: Grupo (textil/manufactura)
- `estabilidad`: Indicador de estabilidad de costos

#### HISTORIAL_ESTILOS

Registro histórico de estilos fabricados.

**Campos principales:**

- `codigo_estilo`: Código del estilo
- `familia_producto`: Familia del producto
- `tipo_prenda`: Tipo de prenda
- `volumen_total`: Volumen histórico total
- `categoria`: Categorización del estilo
- `version_calculo`: Versión del cálculo

## ⚙️ Configuración Avanzada

### Variables de Entorno

#### Backend (.env)

```env
# Base de Datos
DB_SERVER=131.107.20.77
DB_PORT=1433
DB_USERNAME=CHSAYA01
DB_PASSWORD=NewServerAz654@!
DB_DATABASE=TDV

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

#### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Factores de Ajuste Configurables

#### Rangos de Lote

- **Micro Lote:** 1-50 prendas (Factor: 1.15)
- **Lote Pequeño:** 51-500 prendas (Factor: 1.10)
- **Lote Mediano:** 501-1000 prendas (Factor: 1.05)
- **Lote Grande:** 1001-4000 prendas (Factor: 1.00)
- **Lote Masivo:** 4001+ prendas (Factor: 0.90)

#### Factores de Esfuerzo

- **Bajo:** 0-5 (Factor: 0.90)
- **Medio:** 6 (Factor: 1.00)
- **Alto:** 7-10 (Factor: 1.15)

#### Factores de Estilo

- **Muy Recurrente:** >4000 prendas fabricadas (Factor: 0.95)
- **Recurrente:** <4000 prendas fabricadas (Factor: 1.00)
- **Nuevo:** Estilo no fabricado (Factor: 1.05)

#### Factores de Marca

- **LACOSTE:** 1.05
- **GREYSON:** 1.05
- **GREYSON CLOTHIERS:** 1.10
- **LULULEMON:** 0.95
- **PATAGONIA:** 0.95
- **OTRAS MARCAS:** 1.10 (Default)

## 🧪 Testing y Validación

### Backtesting

El sistema incluye módulos de backtesting para validar la precisión de las cotizaciones:

```bash
cd backend
python backtesting.py
```

### Tests Automatizados

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## 📈 Monitoreo y Logs

### Logs del Sistema

- **Ubicación:** `backend/logs/tdv_cotizador.log`
- **Nivel:** INFO por defecto
- **Formato:** Timestamp - Logger - Level - Message
- **Encoding:** UTF-8 para soporte de caracteres especiales

### Health Check

- **Endpoint:** `GET /health`
- **Monitorea:** Conexión BD, tablas principales, estado general

## 🔒 Seguridad

### Base de Datos

- Conexión autenticada con credenciales seguras
- Queries parametrizadas para prevenir SQL injection
- Timeout de conexión configurado

### API

- CORS configurado para orígenes específicos
- Validación de entrada con Pydantic
- Manejo de errores estructurado
- Logging de actividades

## 🔄 Versionado

### Versiones de Cálculo

El sistema soporta múltiples versiones de cálculo:

- **FLUIDA:** Metodología actual optimizada
- **truncado:** Metodología con datos limitados

### Control de Versiones

- **Backend:** v2.0
- **Frontend:** v2.0
- **API:** v2.0

## 📞 Soporte y Mantenimiento

### Estructura de Archivos de Respaldo

```
db_ops/
├── Carga_datos_costos_wip.py    # Script de carga histórico
└── Carga_datos_finanzas.py     # Script de finanzas histórico
```

### Logs de Backtesting

```
backend/src/smp/
├── backtesting_estilos_YYYYMMDD_HHMMSS.xlsx
└── backtesting_ops_YYYYMMDD_HHMMSS.xlsx
```

### Actualizaciones de Datos

- Los datos se actualizan mediante `fecha_corrida` en las tablas principales
- Sistema de verificación de fechas de última corrida
- Alertas automáticas para datos desactualizados

## 🚨 Troubleshooting

### Problemas Comunes

#### Error de Conexión a BD

```
Verificar:
- Credenciales en .env
- Conectividad de red al servidor SQL
- Estado del servicio SQL Server
```

#### Error en Frontend

```
Verificar:
- Backend ejecutándose en puerto 8000
- CORS configurado correctamente
- Variables de entorno del frontend
```

#### Cotizaciones Inconsistentes

```
Verificar:
- Fechas de corrida actualizadas
- Versión de cálculo correcta
- Factores de ajuste configurados
```

### Comandos de Diagnóstico

```bash
# Verificar estado de tablas
curl http://localhost:8000/health

# Verificar versiones de cálculo
curl http://localhost:8000/versiones-calculo

# Verificar fechas de corrida
curl http://localhost:8000/info-fechas-corrida
```

## 📄 Licencia

Este proyecto es propiedad de SAYA INVESTMENTS y está destinado para uso interno de TDV.

---

**Desarrollado por:** SAYA INVESTMENTS
**Contacto:** Equipo de Desarrollo TDV
**Última actualización:** 2025
