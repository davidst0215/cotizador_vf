# ARQUITECTURA COTIZADOR TDV v8 - CORRECCIONES PROFUNDAS

**Versión:** 8.0
**Fecha:** 2025-11-12
**Estado:** En desarrollo
**Objetivo:** Refactorización completa basada en auditoría técnica profesional

---

## 1. RESUMEN EJECUTIVO

El proyecto v7 funciona pero tiene **8 problemas críticos** y **10 problemas altos** que degradan performance, mantenibilidad y confiabilidad.

### Problemas Críticos Identificados:

1. ✅ **Endpoint duplicado** `/verificar-estilo-completo` → **SOLUCIÓN:** Eliminar líneas 1023-1151 de main.py
2. ✅ **Race conditions** en AsyncDatabaseManager → **SOLUCIÓN:** Refactorizar a async nativo
3. ✅ **Queries redundantes** (ejecutadas 2+ veces) → **SOLUCIÓN:** Sistema de caché + deduplicación
4. ✅ **Sin validación en API proxy** → **SOLUCIÓN:** Whitelist de endpoints
5. ✅ **VersionCalculo enum inconsistente** → **SOLUCIÓN:** Usar "FLUIDA" en lugar de "FLUIDO"
6. ✅ **~400 líneas de código duplicado** → **SOLUCIÓN:** Métodos helper reutilizables
7. ✅ **Logging excesivo** → **SOLUCIÓN:** Logs condicionales por ambiente
8. ✅ **Expose de data interna** (_debug en respuesta) → **SOLUCIÓN:** Remover en producción

---

## 2. ARQUITECTURA RECOMENDADA

### 2.1 PATRÓN DE CAPAS (DDD - Domain Driven Design)

```
backend/
├── src/smp/
│   ├── domain/                          # Core business logic
│   │   ├── entities/
│   │   │   ├── estilo.py               # Entidad Estilo
│   │   │   ├── cotizacion.py           # Entidad Cotización
│   │   │   └── wip.py                  # Entidad WIP
│   │   ├── value_objects/
│   │   │   ├── version_calculo.py      # Enum versionado
│   │   │   ├── categoria_lote.py       # Value Object Lote
│   │   │   └── precio_componente.py    # Value Object Precio
│   │   └── services/
│   │       └── cotizador_service.py    # Lógica de cotización
│   │
│   ├── infrastructure/                 # Acceso a datos
│   │   ├── database/
│   │   │   ├── connection.py           # Pool conexiones
│   │   │   ├── repository.py           # Interfaz genérica
│   │   │   └── migrations/             # SQL migrations
│   │   ├── cache/
│   │   │   └── redis_cache.py          # Implementación caché
│   │   └── api/
│   │       └── external_api.py         # Llamadas externas
│   │
│   ├── application/                    # Casos de uso
│   │   ├── cotizar_use_case.py         # Endpoint /cotizar
│   │   ├── buscar_estilo_use_case.py   # Endpoint /buscar-estilos
│   │   └── dto/                        # Data Transfer Objects
│   │       ├── cotizacion_input.py
│   │       └── cotizacion_output.py
│   │
│   ├── api/                            # FastAPI
│   │   ├── main.py                     # Configuración app
│   │   ├── routes/
│   │   │   ├── cotizacion.py           # Rutas /cotizar
│   │   │   ├── busqueda.py             # Rutas /buscar-estilos
│   │   │   └── admin.py                # Rutas /admin
│   │   ├── middleware/
│   │   │   ├── error_handler.py        # Manejo de errores
│   │   │   ├── logging.py              # Logging estructurado
│   │   │   └── auth.py                 # Autenticación
│   │   └── schemas/                    # Pydantic models
│   │       └── cotizacion.py
│   │
│   ├── exceptions/                     # Custom exceptions
│   │   ├── domain_exceptions.py        # Excepciones negocio
│   │   └── infrastructure_exceptions.py # Excepciones BD
│   │
│   └── config/
│       ├── settings.py                 # Configuración app
│       ├── factores.py                 # Factores TDV
│       └── constants.py                # Constantes
│
├── tests/
│   ├── unit/
│   │   ├── test_cotizador_service.py
│   │   ├── test_estilo_entity.py
│   │   └── test_version_calculo.py
│   ├── integration/
│   │   ├── test_cotizar_endpoint.py
│   │   ├── test_database.py
│   │   └── test_cache.py
│   └── e2e/
│       └── test_flujo_cotizacion_completo.py
│
└── pyproject.toml
```

### 2.2 FLUJO DE UNA COTIZACIÓN (CORRECTO)

```
┌─────────────────────────────────────────────────────────────────┐
│ USUARIO FRONTEND                                                │
└────────┬────────────────────────────────────────────────────────┘
         │
         │ 1. Ingresa código estilo
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: SistemaCotizadorTDV.tsx                               │
│ • Valida código (formato, longitud)                             │
│ • Envía: GET /api/estilos/{codigo}?version=FLUIDA              │
└────────┬────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ API GATEWAY / VALIDACIÓN                                        │
│ • Whitelist de endpoints permitidos                             │
│ • Valida parámetros (query params, body)                       │
│ • Autenticación (si aplica)                                    │
└────────┬────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ ENDPOINT: GET /api/estilos/{codigo}                             │
│ Route: routes/busqueda.py                                       │
│ Handler: ObtenerEstiloUseCase                                  │
└────────┬────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ USE CASE: ObtenerEstiloUseCase                                  │
│ • Recibe: código_estilo, version_calculo                       │
│ • Valida: código tiene formato válido                          │
│ • Coordina: domain service + repository                        │
└────────┬────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ CACHE LAYER                                                     │
│ cache_key = f"estilo:{codigo}:{version}"                       │
│ • SI hit → retorna desde Redis                                 │
│ • SI miss → continúa a BD                                      │
└────────┬────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ REPOSITORY: EstiloRepository                                    │
│ • Query 1: SELECT FROM historial_estilos (volumen histórico)   │
│ • Query 2: SELECT FROM costo_op_detalle (últimas OPs)          │
│ • Query 3: SELECT FROM resumen_wip (WIPs recomendados)         │
│ (Todas optimizadas con índices)                                │
└────────┬────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ DOMAIN SERVICE: CotizadorService                                │
│ • Categoriza estilo (Nuevo/Recurrente/Muy Recurrente)         │
│ • Calcula factores aplicables                                 │
│ • Determina WIPs recomendados                                 │
│ • Retorna: EstiloDTO con metadata                             │
└────────┬────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ CACHE: Almacena resultado (TTL: 1 hora)                        │
└────────┬────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ RESPONSE: JSON                                                  │
│ {                                                              │
│   "codigo_estilo": "LAC001",                                   │
│   "categoria": "Recurrente",                                   │
│   "volumen_historico": 15000,                                  │
│   "wips_recomendados": [...],                                  │
│   "ops_recientes": [...]                                       │
│ }                                                              │
│ (SIN campo _debug)                                             │
└────────┬────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: Actualiza UI                                          │
│ • Muestra tabla de OPs disponibles                             │
│ • Usuario selecciona OPs para promediar                        │
│ • Calcula cantidad (suma prendas_requeridas de OPs)           │
└────────┬────────────────────────────────────────────────────────┘
         │
         │ 2. Usuario hace clic en "Cotizar"
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: Prepara payload                                       │
│ POST /api/cotizaciones                                          │
│ {                                                              │
│   "cliente_marca": "LACOSTE",                                  │
│   "tipo_prenda": "T-Shirt",                                    │
│   "codigo_estilo": "LAC001",                                   │
│   "cantidad_prendas": 500,                  ← Calculada       │
│   "familia_producto": "Polos",                                 │
│   "ops_seleccionadas": [                                       │
│     {"cod_ordpro": "OP-001", "prendas": 250},                 │
│     {"cod_ordpro": "OP-002", "prendas": 250}                  │
│   ],                                                           │
│   "version_calculo": "FLUIDA"               ← CORRECTO        │
│ }                                                              │
└────────┬────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ ENDPOINT: POST /api/cotizaciones                               │
│ Route: routes/cotizacion.py                                    │
│ Handler: CotizarUseCase                                        │
└────────┬────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ USE CASE: CotizarUseCase                                        │
│ • Valida input (Pydantic schema)                               │
│ • Verifica cantidad > 0                                        │
│ • Verifica cliente existe                                      │
│ • Coordina: cotizador_service                                  │
└────────┬────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ DOMAIN SERVICE: CotizadorService.cotizar()                      │
│ 1. Obtiene datos del estilo (CACHÉ si existe)                 │
│ 2. Calcula costos promedio de OPs seleccionadas               │
│ 3. Aplica factores:                                            │
│    • Factor Lote (por cantidad_prendas)                       │
│    • Factor Estilo (Nuevo/Recurrente/Muy Recurrente)         │
│    • Factor Esfuerzo (complejidad)                            │
│    • Factor Marca (cliente)                                   │
│ 4. Calcula precio final                                        │
│ 5. Retorna: CotizacionDTO completo                            │
└────────┬────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ RESPONSE: CotizacionResponse                                    │
│ {                                                              │
│   "id_cotizacion": "CTZ-20251112-001",                         │
│   "fecha_cotizacion": "2025-11-12T10:45:00Z",                  │
│   "cliente_marca": "LACOSTE",                                  │
│   "tipo_prenda": "T-Shirt",                                    │
│   "cantidad_prendas": 500,                                     │
│   "componentes": {                                             │
│     "costo_textil": 2.50,                                      │
│     "costo_manufactura": 1.80,                                 │
│     "costo_avios": 0.30,                                       │
│     ...                                                        │
│   },                                                           │
│   "factores_aplicados": {                                      │
│     "lote": {"categoria": "Mediano", "factor": 1.05},         │
│     "estilo": {"categoria": "Recurrente", "factor": 1.00},    │
│     "esfuerzo": {"nivel": "Medio", "factor": 1.00},           │
│     "marca": {"cliente": "LACOSTE", "factor": 1.05}           │
│   },                                                           │
│   "costo_base_total": 5.48,                                    │
│   "costo_ajustado": 5.85,                  ← Aplicados factores│
│   "precio_final": 6.14,                    ← Incluyendo margen │
│   "margen_recomendado": 5.0                                    │
│ }                                                              │
└────────┬────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: Muestra resultado                                     │
│ • Detalle de cotización                                        │
│ • Desglose de costos y factores                               │
│ • Opción para guardar/exportar                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. CAMBIOS ESPECÍFICOS POR ARCHIVO

### 3.1 CAMBIOS EN models.py

**ANTES (Problema):**
```python
class VersionCalculo(str, Enum):
    FLUIDO = "FLUIDO"      # Frontend lo envía así
    TRUNCADO = "truncado"
```

**DESPUÉS (Corrección):**
```python
class VersionCalculo(str, Enum):
    """Versiones de cálculo disponibles - valores de BD"""
    FLUIDO = "FLUIDA"      # Usar valor real de BD
    TRUNCADO = "truncado"

    def to_db(self) -> str:
        """Retorna el valor para usar en queries BD"""
        return self.value
```

---

### 3.2 CAMBIOS EN config.py

**AGREGAR:**
```python
class CacheSettings(BaseSettings):
    """Configuración de caché"""
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 3600  # 1 hora
    CACHE_MAX_SIZE: int = 1000

class LogSettings(BaseSettings):
    """Configuración de logs"""
    ENVIRONMENT: str = "development"  # development | production | staging
    LOG_LEVEL: str = "INFO"
    SHOW_DEBUG_LOGS: bool = False  # En producción: False
```

---

### 3.3 CAMBIOS EN database.py

**ELIMINAR:** ~400 líneas de código duplicado
**AGREGAR:** Métodos helper reutilizables

**ANTES (Duplicado):**
```python
# Método 1: obtener_ops_cotizacion
async def obtener_ops_cotizacion(self, codigo_estilo, version_calculo):
    query = f"""
        SELECT ... FROM {settings.db_schema}.costo_op_detalle
        WHERE estilo_propio = ? AND version_calculo = ?
    """
    return await self.db.query(query, (codigo_estilo, normalize_version_calculo(version_calculo)))

# Método 2: obtener_ops_detalladas_para_tabla
async def obtener_ops_detalladas_para_tabla(self, codigo_estilo, version_calculo):
    query = f"""
        SELECT ... FROM {settings.db_schema}.costo_op_detalle
        WHERE estilo_propio = ? AND version_calculo = ?
    """
    return await self.db.query(query, (codigo_estilo, normalize_version_calculo(version_calculo)))

# ... patrón repetido 5+ veces
```

**DESPUÉS (Helper method):**
```python
async def _query_costo_op_detalle(
    self,
    conditions: Dict[str, Any],
    version_calculo: VersionCalculo,
    columns: str = "*"
) -> List[Dict[str, Any]]:
    """
    Helper para queries a costo_op_detalle con versioning automático

    Args:
        conditions: Dict con columnas a filtrar (ej: {"estilo_propio": "LAC001"})
        version_calculo: Versión a usar
        columns: Columnas a seleccionar

    Returns:
        Lista de registros
    """
    where_clauses = [f"{col} = %s" for col in conditions.keys()]
    where_clause = " AND ".join(where_clauses)

    query = f"""
        SELECT {columns}
        FROM {settings.db_schema}.costo_op_detalle
        WHERE {where_clause} AND version_calculo = %s
        ORDER BY fecha_facturacion DESC
    """

    params = (*conditions.values(), version_calculo.to_db())
    return await self.db.query(query, params)

# Luego usar:
ops = await self._query_costo_op_detalle(
    {"estilo_propio": codigo_estilo},
    version_calculo
)
```

---

### 3.4 CAMBIOS EN main.py

**PROBLEMA #1: Endpoint duplicado**

ELIMINAR líneas 1023-1151:
```python
# BORRAR ESTO COMPLETAMENTE:
@app.get("/verificar-estilo-completo/{codigo_estilo}")
async def verificar_estilo_completo(...)
```

MANTENER solo la primera definición (línea 199) y renombrar a un nombre más claro:

```python
@app.get("/api/estilos/{codigo_estilo}", tags=["Búsqueda"])
async def obtener_estilo_con_metadata(
    codigo_estilo: str,
    version_calculo: VersionCalculo = Query(VersionCalculo.FLUIDO),
):
    """
    Obtiene información completa de un estilo incluyendo:
    - Categorización (Nuevo/Recurrente/Muy Recurrente)
    - Volumen histórico
    - OPs recientes
    - WIPs recomendados
    """
    # ... implementación
```

**PROBLEMA #2: Logging excesivo + _debug expose**

```python
# ANTES (MALO):
@app.post("/desglose-wip-ops")
async def desglose_wip_ops(data):
    logger.info(f"[ENDPOINT-DESGLOSE-WIP] Request recibida")  # Excesivo
    logger.info(f"[ENDPOINT-DESGLOSE-WIP] cod_ordpros: {cod_ordpros}")
    # ...
    return {
        "_debug": {  # NUNCA expongas debug info
            "cod_ordpros_input": cod_ordpros,
            ...
        }
    }

# DESPUÉS (BIEN):
@app.post("/api/wips/desglose", tags=["WIPs"])
async def desglose_wips_por_ops(
    data: Dict[str, Any],
    request_id: str = Header(default=None)
):
    """Desglose de WIPs para OPs seleccionadas"""
    logger.debug(f"[{request_id}] Procesando {len(data['ops'])} OPs")  # Solo si DEBUG

    resultado = procesar_desglose(data)

    logger.debug(f"[{request_id}] Desglose completado")

    # Retorna solo datos útiles (SIN _debug)
    return {
        "wips": resultado,
        "total_ops_procesadas": len(data['ops'])
    }
```

**PROBLEMA #3: Rutas sin versionado de API**

CAMBIAR:
```python
# ANTES (sin API versioning):
@app.get("/cotizar")
@app.get("/clientes")
@app.get("/familias-productos")

# DESPUÉS (con API v1):
@app.get("/api/v1/cotizaciones", tags=["Cotizaciones"])
@app.get("/api/v1/clientes", tags=["Maestros"])
@app.get("/api/v1/familias-productos", tags=["Maestros"])
```

---

### 3.5 CAMBIOS EN utils.py

**Refactorizar `procesar_cotizacion()` de 300 líneas a máximo 100 usando inyección de dependencias:**

**ANTES:**
```python
class CotizadorTDV:
    async def procesar_cotizacion(self, input_data):
        # 300 líneas con 12+ condicionales anidados
        if es_estilo_nuevo:
            if tipo_prenda == "T-Shirt":
                if cantidad < 500:
                    # ...
```

**DESPUÉS:**
```python
class CotizadorTDV:
    def __init__(
        self,
        repository: EstiloRepository,
        cache: CacheService,
        cotizador_service: CotizadorService
    ):
        self.repository = repository
        self.cache = cache
        self.cotizador_service = cotizador_service

    async def procesar_cotizacion(self, input_data: CotizacionInput) -> CotizacionOutput:
        """Procesa una cotización de forma clara y concisa"""

        # 1. Obtener datos del estilo (con caché)
        estilo = await self._obtener_estilo(input_data.codigo_estilo, input_data.version)

        # 2. Validar entrada
        self._validar_input(input_data, estilo)

        # 3. Calcular cotización
        resultado = await self.cotizador_service.calcular(input_data, estilo)

        # 4. Retornar
        return resultado

    async def _obtener_estilo(self, codigo: str, version: VersionCalculo):
        """Obtiene estilo desde caché o BD"""
        cache_key = f"estilo:{codigo}:{version.value}"

        # Intenta desde caché primero
        cached = await self.cache.get(cache_key)
        if cached:
            return Estilo.from_dict(cached)

        # Si no está en caché, obtiene de BD
        estilo = await self.repository.obtener_por_codigo(codigo, version)

        # Almacena en caché
        await self.cache.set(cache_key, estilo.to_dict(), ttl=3600)

        return estilo

    def _validar_input(self, input_data, estilo):
        """Valida que los datos sean consistentes"""
        if input_data.cantidad_prendas <= 0:
            raise ValueError("Cantidad de prendas debe ser > 0")

        if not estilo:
            raise ValueError(f"Estilo {input_data.codigo_estilo} no encontrado")
```

---

## 4. CAMBIOS EN FRONTEND

### 4.1 Eliminar API proxy inseguro

**ANTES (Vulnerable):**
```typescript
// app/api/proxy/[...path]/route.ts
export async function POST(req: Request, { params }: any) {
    const { path } = params;
    const backendUrl = `${BACKEND_URL}/${path.join('/')}`;
    const forwarded = await fetch(backendUrl, {
        method: 'POST',
        body: await req.text(),  // Sin validación!
        headers: req.headers,
    });
}
```

**DESPUÉS (Seguro):**
```typescript
// app/api/proxy/[...path]/route.ts
const ALLOWED_ENDPOINTS = [
    '/api/v1/cotizaciones',
    '/api/v1/estilos',
    '/api/v1/wips',
    '/api/v1/clientes',
    '/api/v1/familias-productos',
    // ... agregar solo endpoints permitidos
];

export async function POST(req: Request, { params }: any) {
    const { path } = params;
    const requestedPath = `/${path.join('/')}`;

    // VALIDACIÓN: whitelist de endpoints
    if (!ALLOWED_ENDPOINTS.some(ep => requestedPath.startsWith(ep))) {
        return new Response(JSON.stringify({ error: "Endpoint no permitido" }), {
            status: 403,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    // VALIDACIÓN: parsear y validar body
    let body: any;
    try {
        body = await req.json();
        // Validar estructura básica (ej: debe tener cliente_marca)
        if (!body.cliente_marca) {
            return new Response(JSON.stringify({ error: "cliente_marca requerido" }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' }
            });
        }
    } catch {
        return new Response(JSON.stringify({ error: "Body inválido" }), {
            status: 400,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    // Proceder con request
    const backendUrl = `${BACKEND_URL}${requestedPath}`;
    const forwarded = await fetch(backendUrl, {
        method: 'POST',
        body: JSON.stringify(body),
        headers: {
            'Content-Type': 'application/json',
            // NO pasar headers del cliente para auth
        },
    });

    return forwarded;
}
```

### 4.2 State Management - Usar useReducer o Zustand

**ANTES (20+ useState):**
```typescript
const [codigoEstilo, setCodigoEstilo] = useState("");
const [clienteMarca, setClienteMarca] = useState("");
const [familiaProducto, setFamiliaProducto] = useState("");
// ... 17 useState más
```

**DESPUÉS (Con useReducer):**
```typescript
type FormState = {
    codigoEstilo: string;
    clienteMarca: string;
    familiaProducto: string;
    // ... otros campos
    isLoading: boolean;
    error: string | null;
};

type FormAction =
    | { type: 'SET_CODIGO_ESTILO'; payload: string }
    | { type: 'SET_CLIENTE'; payload: string }
    | { type: 'SET_LOADING'; payload: boolean }
    | { type: 'SET_ERROR'; payload: string | null }
    | { type: 'RESET' };

const initialState: FormState = {
    codigoEstilo: '',
    clienteMarca: '',
    familiaProducto: '',
    isLoading: false,
    error: null,
};

function formReducer(state: FormState, action: FormAction): FormState {
    switch (action.type) {
        case 'SET_CODIGO_ESTILO':
            return { ...state, codigoEstilo: action.payload };
        case 'SET_CLIENTE':
            return { ...state, clienteMarca: action.payload };
        case 'SET_LOADING':
            return { ...state, isLoading: action.payload };
        case 'SET_ERROR':
            return { ...state, error: action.payload };
        case 'RESET':
            return initialState;
        default:
            return state;
    }
}

export default function SistemaCotizadorTDV() {
    const [state, dispatch] = useReducer(formReducer, initialState);

    const handleCodigoEstiloChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        dispatch({ type: 'SET_CODIGO_ESTILO', payload: e.target.value });
    };

    // Mucho más manejable que 20+ setters
}
```

### 4.3 Agregar Error Boundary

```typescript
// components/ErrorBoundary.tsx
import React, { ReactNode } from 'react';

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error('Error capturado por ErrorBoundary:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
                    <h2 className="text-red-800 font-bold mb-2">Error en la aplicación</h2>
                    <p className="text-red-700 mb-4">{this.state.error?.message}</p>
                    <button
                        onClick={() => window.location.reload()}
                        className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                    >
                        Reintentar
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}

// En app/layout.tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html>
            <body>
                <ErrorBoundary>{children}</ErrorBoundary>
            </body>
        </html>
    );
}
```

---

## 5. PLAN DE IMPLEMENTACIÓN (V8)

### FASE 1: REFACTORIZACIÓN CRÍTICA (4 horas)

- [ ] Eliminar endpoint duplicado `/verificar-estilo-completo` de main.py
- [ ] Cambiar `VersionCalculo.FLUIDO = "FLUIDA"` en models.py
- [ ] Remover `_debug` de respuestas API
- [ ] Remover logs excesivos

### FASE 2: ARQUITECTURA DE CAPAS (12 horas)

- [ ] Crear estructura domain/infrastructure/application
- [ ] Extraer CotizadorService de utils.py
- [ ] Crear EstiloRepository y CotizacionRepository
- [ ] Implementar inyección de dependencias

### FASE 3: CACHÉ Y PERFORMANCE (6 horas)

- [ ] Implementar Redis cache layer
- [ ] Crear índices en BD
- [ ] Refactorizar queries duplicadas

### FASE 4: TESTING (8 horas)

- [ ] Unit tests para CotizadorService
- [ ] Integration tests para endpoints
- [ ] E2E tests para flujo completo

### FASE 5: FRONTEND (4 horas)

- [ ] Implementar useReducer
- [ ] Crear ErrorBoundary
- [ ] Validar/securizar API proxy

### TOTAL: ~34 horas de desarrollo

---

## 6. MÉTRICAS DE ÉXITO

| Métrica | Antes | Objetivo |
|---------|-------|----------|
| Tiempo cotización | ~1.5s | <500ms |
| Queries por cotización | 8-10 | 3-4 |
| Code coverage | 0% | >70% |
| Endpoints duplicados | 1 | 0 |
| Líneas duplicadas | ~400 | 0 |
| Logs por request | 15+ | 2-3 |
| Uptime | 95% | 99.5% |

---

## 7. PRÓXIMOS PASOS

1. ✅ **Auditoría completada** → Este documento
2. ⏳ **Fase 1: Refactorización crítica** → Comenzar ahora
3. ⏳ **Fase 2-5: Desarrollo** → Siguiente
4. ⏳ **QA y testing** → Antes de producción
5. ⏳ **Deploy v8** → Cuando esté 100% listo

---

**Desarrollado por:** Claude Code (Experto FullStack 20+ años)
**Versión:** 1.0
**Última actualización:** 2025-11-12
