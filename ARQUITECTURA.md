# Documentación Técnica - Sistema Cotizador TDV Expert

## 📐 Arquitectura General

### Componentes Principales

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FRONTEND      │    │    BACKEND      │    │  BASE DE DATOS  │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (SQL Server)   │
│                 │    │                 │    │                 │
│ • React/TypeScript │  │ • Python 3.8+    │  │ • TDV Database   │
│ • Tailwind CSS  │    │ • Pydantic Models│    │ • Tablas Históricas│
│ • Lucide Icons  │    │ • CORS/Security │    │ • WIPs Data     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Flujo de Datos

```
Usuario → Frontend → API REST → Backend → Base de Datos → Procesamiento → Respuesta JSON
```

## 🏗️ Estructura de Archivos Detallada

### Backend (Python/FastAPI)

```
backend/
│
├── main.py                     # 🚀 Aplicación principal FastAPI
│   ├── Configuración CORS
│   ├── Endpoints REST
│   ├── Manejo de errores
│   ├── Health checks
│   └── Startup/Shutdown events
│
├── config.py                   # ⚙️ Configuración del sistema
│   ├── Settings (Pydantic)
│   ├── Factores de ajuste TDV
│   ├── Rangos de validación
│   └── Conexión base de datos
│
├── database.py                 # 🗄️ Capa de acceso a datos
│   ├── Conexión SQL Server
│   ├── Queries parametrizadas
│   ├── Funciones de consulta
│   └── Validación de datos
│
├── models.py                   # 📋 Modelos Pydantic
│   ├── Input/Output schemas
│   ├── Validación de tipos
│   ├── Documentación automática
│   └── Serialización JSON
│
├── utils.py                    # 🔧 Lógica de negocio
│   ├── Algoritmo de cotización
│   ├── Cálculos de factores
│   ├── Procesamiento WIPs
│   └── Validaciones de negocio
│
├── backtesting.py              # 📊 Análisis y validación
│   ├── Comparación histórica
│   ├── Métricas de precisión
│   ├── Reportes Excel
│   └── Validación de modelos
│
├── requirements.txt            # 📦 Dependencias Python
│
├── logs/
│   └── tdv_cotizador.log      # 📝 Logs del sistema
│
├── venv/                      # 🐍 Entorno virtual Python
│
└── backtesting_*.xlsx         # 📈 Reportes de análisis
```

### Frontend (Next.js/TypeScript)

```
frontend/
│
├── src/
│   ├── app/
│   │   ├── layout.tsx          # 🎨 Layout principal
│   │   ├── page.tsx           # 📱 Página principal
│   │   └── globals.css        # 🎨 Estilos globales
│   │
│   └── components/
│       └── SistemaCotizadorTDV.tsx # 🖥️ Componente principal
│           ├── Estado y hooks React
│           ├── Validación de formularios
│           ├── Comunicación con API
│           ├── Interfaces TypeScript
│           └── Renderizado condicional
│
├── package.json               # 📦 Dependencias Node.js
├── package-lock.json          # 🔒 Lock de versiones
├── tsconfig.json             # 📝 Configuración TypeScript
├── next.config.js            # ⚙️ Configuración Next.js
├── tailwind.config.js        # 🎨 Configuración Tailwind
├── postcss.config.js         # 🎨 Post-procesamiento CSS
├── next-env.d.ts            # 📝 Tipos Next.js
│
├── dist/                     # 🏗️ Build de producción
├── node_modules/             # 📦 Dependencias
└── .next/                   # 🔧 Cache Next.js
```

### Archivos de Respaldo

```
_backup_old/
├── Carga_datos_costos_wip.py   # 📥 Script carga WIPs
└── Carga_datos_finanzas.py    # 📥 Script carga finanzas
```

## 🔗 Comunicación Entre Componentes

### API Endpoints Documentados

#### 1. Información del Sistema
```http
GET /                           # Información general
GET /health                     # Estado del sistema
GET /configuracion              # Configuración y factores
```

#### 2. Cotización Principal
```http
POST /cotizar                   # Generar cotización
POST /ops-utilizadas-cotizacion # OPs utilizadas
```

#### 3. Búsqueda y Verificación
```http
GET /verificar-estilo-completo/{codigo}     # Verificación completa
GET /buscar-estilos/{codigo}                # Búsqueda similares
GET /autocompletar-estilo/{codigo}          # Auto-completado
```

#### 4. Datos Maestros
```http
GET /clientes                   # Lista clientes
GET /familias-productos         # Familias disponibles
GET /tipos-prenda/{familia}     # Tipos por familia
```

#### 5. Configuración WIPs
```http
GET /wips-disponibles                       # WIPs con costos
GET /ruta-textil-recomendada/{tipo_prenda} # Ruta textil
```

#### 6. Análisis y Reportes
```http
GET /analisis-historico         # Análisis histórico
GET /info-fechas-corrida       # Fechas de corrida
GET /versiones-calculo         # Versiones disponibles
```

### Modelos de Datos

#### CotizacionInput
```typescript
interface CotizacionInput {
  cliente_marca: string
  temporada: string
  cantidad_prendas: number
  familia_producto: string
  tipo_prenda: string
  codigo_estilo?: string
  usuario: string
  version_calculo: string
  wips_seleccionadas?: WipSeleccionada[]
}
```

#### CotizacionResponse
```typescript
interface CotizacionResponse {
  id_cotizacion: string
  fecha_cotizacion: string
  inputs: CotizacionInput
  componentes: ComponenteCosto[]
  factores_aplicados: FactoresAplicados
  costo_base_total: number
  precio_final: number
  margen_recomendado: number
  info_comercial?: InfoComercial
}
```

## 🗃️ Esquema de Base de Datos

### Tablas Principales

#### COSTO_OP_DETALLE
```sql
-- Contiene datos históricos de órdenes de producción
CREATE TABLE TDV.saya.COSTO_OP_DETALLE (
    orden_produccion VARCHAR(50),
    estilo_propio VARCHAR(100),
    cliente VARCHAR(100),
    familia_de_productos VARCHAR(100),
    tipo_de_producto VARCHAR(100),
    prendas_requeridas INT,
    costo_textil DECIMAL(10,4),
    costo_manufactura DECIMAL(10,4),
    costo_avios DECIMAL(10,4),
    costo_materia_prima DECIMAL(10,4),
    costo_indirecto_fijo DECIMAL(10,4),
    gasto_administracion DECIMAL(10,4),
    gasto_ventas DECIMAL(10,4),
    esfuerzo_total INT,
    version_calculo VARCHAR(20),
    fecha_corrida DATETIME,
    fecha_facturacion DATE
);
```

#### RESUMEN_WIP_POR_PRENDA
```sql
-- Información de Work In Process por tipo de prenda
CREATE TABLE TDV.saya.RESUMEN_WIP_POR_PRENDA (
    wip_id VARCHAR(10),
    nombre_wip VARCHAR(200),
    tipo_prenda VARCHAR(100),
    costo_actual DECIMAL(10,4),
    disponible BIT,
    grupo VARCHAR(50),
    estabilidad DECIMAL(5,2),
    fecha_corrida DATETIME,
    version_calculo VARCHAR(20)
);
```

#### HISTORIAL_ESTILOS
```sql
-- Registro histórico de estilos fabricados
CREATE TABLE TDV.saya.HISTORIAL_ESTILOS (
    codigo_estilo VARCHAR(100),
    familia_producto VARCHAR(100),
    tipo_prenda VARCHAR(100),
    volumen_total INT,
    categoria VARCHAR(50),
    ultima_produccion DATE,
    version_calculo VARCHAR(20),
    fecha_corrida DATETIME
);
```

## ⚡ Algoritmo de Cotización

### Proceso de Cálculo

```python
def algoritmo_cotizacion(input_data):
    """
    Algoritmo principal de cotización TDV
    
    Flujo:
    1. Validación de entrada
    2. Categorización del estilo
    3. Obtención de costos base
    4. Aplicación de factores
    5. Cálculo de precio final
    """
    
    # 1. Validación
    validar_entrada(input_data)
    
    # 2. Categorización
    categoria_estilo = categorizar_estilo(input_data.codigo_estilo)
    categoria_lote = categorizar_lote(input_data.cantidad_prendas)
    
    # 3. Costos base
    costos_base = obtener_costos_historicos(input_data)
    
    # 4. Factores de ajuste
    factor_estilo = get_factor_estilo(categoria_estilo)
    factor_lote = get_factor_lote(categoria_lote)
    factor_marca = get_factor_marca(input_data.cliente_marca)
    factor_esfuerzo = get_factor_esfuerzo(costos_base.esfuerzo_total)
    
    # 5. Cálculo final
    costo_ajustado = costos_base * factor_estilo * factor_lote * factor_esfuerzo
    precio_final = costo_ajustado * factor_marca
    
    return CotizacionResponse(...)
```

### Factores de Ajuste

#### Por Volumen de Lote
```python
RANGOS_LOTE = {
    'Micro Lote': {'min': 1, 'max': 50, 'factor': 1.15},      # +15%
    'Lote Pequeño': {'min': 51, 'max': 500, 'factor': 1.10},   # +10%
    'Lote Mediano': {'min': 501, 'max': 1000, 'factor': 1.05}, # +5%
    'Lote Grande': {'min': 1001, 'max': 4000, 'factor': 1.00}, # Base
    'Lote Masivo': {'min': 4001, 'max': 999999, 'factor': 0.90} # -10%
}
```

#### Por Recurrencia del Estilo
```python
FACTORES_ESTILO = {
    'Muy Recurrente': {'factor': 0.95},  # -5% (más eficiente)
    'Recurrente': {'factor': 1.00},      # Base
    'Nuevo': {'factor': 1.05}            # +5% (menos eficiente)
}
```

#### Por Marca/Cliente
```python
FACTORES_MARCA = {
    'LACOSTE': 1.05,           # Premium +5%
    'GREYSON': 1.05,           # Premium +5%
    'LULULEMON': 0.95,         # Volumen -5%
    'PATAGONIA': 0.95,         # Volumen -5%
    'OTRAS MARCAS': 1.10       # Default +10%
}
```

## 🔒 Seguridad y Validaciones

### Validación de Entrada
- **Pydantic Models:** Validación automática de tipos
- **Rangos de Seguridad:** Límites min/max por componente
- **Queries Parametrizadas:** Prevención SQL injection
- **CORS:** Orígenes específicos configurados

### Manejo de Errores
```python
# Estructura de errores JSON
{
    "error": "ERROR_CODE",
    "mensaje": "Descripción del error",
    "detalles": {"campo": "valor"},
    "timestamp": "2025-01-XX..."
}
```

## 📊 Métricas y Monitoreo

### Health Check
```python
GET /health
{
    "status": "healthy",
    "database": "connected",
    "tablas": {
        "COSTO_OP_DETALLE": 150000,
        "RESUMEN_WIP_POR_PRENDA": 250,
        "HISTORIAL_ESTILOS": 50000
    },
    "timestamp": "2025-01-XX..."
}
```

### Logging
```python
# Formato de logs
2025-01-XX 10:30:45 - backend.main - INFO - Nueva cotización: usuario | estilo_001
2025-01-XX 10:30:46 - backend.utils - INFO - Factores aplicados: lote=1.05, marca=1.10
2025-01-XX 10:30:47 - backend.main - INFO - Cotización completada: $45.67
```

## 🚀 Deploy y Configuración

### Variables de Entorno Requeridas

#### Backend
```env
DB_SERVER=131.107.20.77
DB_USERNAME=CHSAYA01
DB_PASSWORD=NewServerAz654@!
DB_DATABASE=TDV
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
CORS_ORIGINS=http://localhost:3000
```

#### Frontend
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Comandos de Deploy

#### Desarrollo
```bash
# Backend
cd backend && uvicorn main:app --reload

# Frontend  
cd frontend && npm run dev
```

#### Producción
```bash
# Backend
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm run build && npm start
```

## 🔄 Flujo de Desarrollo

### Proceso de Testing
1. **Unit Tests:** `pytest backend/`
2. **API Tests:** `pytest backend/tests/test_api.py`
3. **Frontend Tests:** `npm test`
4. **Backtesting:** `python backend/backtesting.py`

### Control de Versiones
- **Main Branch:** Código de producción
- **Feature Branches:** Nuevas funcionalidades
- **Hotfix Branches:** Correcciones urgentes

### Pipeline CI/CD
```yaml
# Ejemplo de pipeline
1. Code Push → GitHub
2. Run Tests → pytest + npm test
3. Build → Docker containers
4. Deploy → Production servers
5. Monitor → Health checks + logs
```

---

**Documento técnico actualizado:** 2025  
**Versión del sistema:** 2.0  
**Autor:** SAYA INVESTMENTS