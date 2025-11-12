# FASE 1: REFACTORIZACIÓN CRÍTICA - CAMBIOS REALIZADOS

**Estado:** EN PROGRESO
**Fecha:** 2025-11-12
**Responsable:** Claude Code (Experto FullStack)

---

## ✅ CAMBIOS COMPLETADOS

### 1. ✅ FIX: VersionCalculo Enum Corregido

**Archivo:** `backend/src/smp/models.py` (línea 23-44)

**Problema:**
- API frontend enviaba `"FLUIDO"`
- BD guardaba `"FLUIDA"`
- Había conversión manual frágil en `database.py:68`

**Solución Implementada:**
```python
class VersionCalculo(str, Enum):
    FLUIDO = "FLUIDA"  # Valor real de BD
    TRUNCADO = "truncado"

    def to_db(self) -> str:
        """Retorna el valor para usar en queries BD"""
        return self.value

    @classmethod
    def from_api(cls, value: str) -> "VersionCalculo":
        """Convierte valor de API a VersionCalculo (tolerante)"""
        # Normalizar entrada: "FLUIDO" → "FLUIDA"
        if value.upper() == "FLUIDO":
            return cls.FLUIDO
        # Intentar encontrar por valor exacto
        for member in cls:
            if member.value == value:
                return member
        # Default a FLUIDO si no encuentra
        return cls.FLUIDO
```

**Beneficio:**
- Eliminada conversión manual
- Código más robusto y autodocumentado
- Frontend puede enviar "FLUIDO" sin problemas (se normaliza automáticamente)
- BD siempre obtiene el valor correcto "FLUIDA"

**Usar así en código:**
```python
# Opción 1: Directo (si ya es VersionCalculo)
query = f"... WHERE version_calculo = %s", (version.to_db(),)

# Opción 2: Desde string (entrada de API)
version = VersionCalculo.from_api(input_data.version)
```

---

## ⏳ CAMBIOS PENDIENTES

### 2. TODO: Eliminar endpoint duplicado `/verificar-estilo-completo`

**Archivo:** `backend/src/smp/main.py`

**Problema:**
- Línea 199-298: Primera definición de `/verificar-estilo-completo`
- Línea 1023-1151: Segunda definición DUPLICADA

**Acción necesaria:**
1. Eliminar COMPLETAMENTE líneas 1023-1151
2. Renombrar primer endpoint a `/api/v1/estilos/{codigo}` (con versionado)
3. Documentar bien qué retorna

**Código a eliminar:**
```python
# BORRAR TODO ESTO (línea 1023-1151):
@app.get("/verificar-estilo-completo/{codigo_estilo}")
async def verificar_estilo_completo(...):
    # ... toda esta función
```

**Mantener y mejorar:**
```python
# CAMBIAR DE (línea 199):
@app.get("/verificar-estilo-completo/{codigo_estilo}")

# A:
@app.get("/api/v1/estilos/{codigo_estilo}", tags=["Búsqueda"])
async def obtener_estilo_detallado(
    codigo_estilo: str,
    version_calculo: VersionCalculo = Query(VersionCalculo.FLUIDO),
):
    """
    Obtiene información completa de un estilo:
    - Categorización (Nuevo/Recurrente/Muy Recurrente)
    - Volumen histórico
    - OPs recientes usadas
    - WIPs recomendados
    """
    # ... implementación
```

**Impacto:**
- FastAPI dejará de usar la SEGUNDA definición (línea 1023)
- Ahora tenemos un endpoint único y claro
- Con versionado de API (/api/v1) para futuro
- Frontend debe actualizar la URL

---

### 3. TODO: Remover campo `_debug` de respuestas API

**Problema:**
- Endpoint `/desglose-wip-ops` expone estructura interna
- Campo `_debug` revela datos sensibles

**Archivos afectados:** `backend/src/smp/main.py` (línea ~754-809)

**Buscar y eliminar:**
```python
# BUSCAR este patrón en main.py:
"_debug": {
    "cod_ordpros_input": cod_ordpros,
    "version_input": version_calculo,
    "desgloses_count": len(desgloses)
}

# Y ELIMINAR COMPLETAMENTE - NO RETORNAR ESTA DATA
```

**Cómo debe ser la respuesta:**
```python
# ANTES (malo):
return {
    "_debug": { ... datos internos ... },
    "desgloses": [...]
}

# DESPUÉS (bien):
return {
    "desgloses": [...],
    "total_procesadas": len(desgloses),
    "fecha_procesamiento": datetime.now().isoformat()
}
```

---

### 4. TODO: Reducir logging excesivo

**Problema:**
- Endpoint `/desglose-wip-ops` tiene 5+ logs por request
- Ruido en producción

**Archivos afectados:** `backend/src/smp/main.py` (línea ~754-809)

**Patrón actual (MALO):**
```python
logger.info(f" [ENDPOINT-DESGLOSE-WIP] Request recibida")
logger.info(f" [ENDPOINT-DESGLOSE-WIP] cod_ordpros recibidos: {cod_ordpros}...")
logger.info(f" [ENDPOINT-DESGLOSE-WIP] version_calculo: {version_calculo}")
logger.info(f" [ENDPOINT-DESGLOSE-WIP] Resultado: {len(desgloses)} WIPs...")
```

**Patrón nuevo (BIEN):**
```python
# Solo 1 log de entrada (si DEBUG) + 1 log de error (si ocurre)
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(f"[desglose-wip-ops] Procesando {len(cod_ordpros)} OPs")

try:
    resultado = procesar_desglose(cod_ordpros)
    # Sin log de éxito - es lo normal
except Exception as e:
    logger.error(f"[desglose-wip-ops] Error: {e}", exc_info=True)
    raise
```

**Configuración necesaria en config.py:**
```python
import logging

# Variable de ambiente para controlar verbosidad
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

### 5. TODO: Refactorizar queries duplicadas

**Problema:**
- ~400 líneas de código duplicado en `database.py`
- Mismo patrón repetido 5+ veces

**Archivos afectados:** `backend/src/smp/database.py`

**Estrategia:**
Crear método helper que consolide la lógica repetida

**Ejemplo de duplicación actual:**

```python
# MÉTODO 1 (línea ~600)
async def obtener_ops_cotizacion(self, codigo_estilo, version_calculo):
    query = f"""
        SELECT cod_ordpro, estilo_propio, cliente, ...
        FROM {settings.db_schema}.costo_op_detalle
        WHERE estilo_propio = ? AND version_calculo = ?
    """
    return await self.db.query(query, (codigo_estilo, normalize_version_calculo(version_calculo)))

# MÉTODO 2 (línea ~700) - CASI IDÉNTICO
async def obtener_ops_detalladas_para_tabla(self, codigo_estilo, version_calculo):
    query = f"""
        SELECT cod_ordpro, estilo_propio, cliente, ...
        FROM {settings.db_schema}.costo_op_detalle
        WHERE estilo_propio = ? AND version_calculo = ?
    """
    return await self.db.query(query, (codigo_estilo, normalize_version_calculo(version_calculo)))
```

**Solución:**
```python
# CREAR HELPER (agregar a TDVQueries)
async def _query_costo_op_detalle(
    self,
    conditions: Dict[str, Any],
    version_calculo: VersionCalculo,
    columns: str = "*",
    order_by: str = "fecha_facturacion DESC"
) -> List[Dict[str, Any]]:
    """
    Helper reutilizable para queries a costo_op_detalle

    Args:
        conditions: Dict columna → valor (ej: {"estilo_propio": "LAC001"})
        version_calculo: Versión de cálculo a filtrar
        columns: Columnas a seleccionar (default: todas)
        order_by: Orden del resultado

    Returns:
        Lista de registros
    """
    where_clauses = [f"{col} = %s" for col in conditions.keys()]
    where_clause = " AND ".join(where_clauses)

    query = f"""
        SELECT {columns}
        FROM {settings.db_schema}.costo_op_detalle
        WHERE {where_clause} AND version_calculo = %s
        ORDER BY {order_by}
    """

    params = (*conditions.values(), version_calculo.to_db())
    return await self.db.query(query, params)

# AHORA USAR ASÍ EN TODOS LOS MÉTODOS:
async def obtener_ops_cotizacion(self, codigo_estilo, version_calculo):
    return await self._query_costo_op_detalle(
        {"estilo_propio": codigo_estilo},
        version_calculo
    )

async def obtener_ops_detalladas_para_tabla(self, codigo_estilo, version_calculo):
    return await self._query_costo_op_detalle(
        {"estilo_propio": codigo_estilo},
        version_calculo
    )
```

---

### 6. TODO: Crear índices en BD

**Archivo:** SQL a ejecutar en PostgreSQL

**Problema:**
- Queries complejas sin índices → lenta
- Búsquedas frecuentes por estilo + version

**Solución:**
```sql
-- Conectar a BD tdv (schema silver)

-- Índice 1: Búsquedas por estilo + version
CREATE INDEX IF NOT EXISTS idx_costo_op_estilo_version
ON silver.costo_op_detalle(estilo_propio, version_calculo, fecha_facturacion DESC);

-- Índice 2: Búsquedas por cliente
CREATE INDEX IF NOT EXISTS idx_costo_op_cliente_version
ON silver.costo_op_detalle(cliente, version_calculo);

-- Índice 3: Búsquedas por tipo de producto
CREATE INDEX IF NOT EXISTS idx_costo_op_tipo_version
ON silver.costo_op_detalle(tipo_de_producto, version_calculo);

-- Índice 4: Historial estilos
CREATE INDEX IF NOT EXISTS idx_historial_codigo_version
ON silver.historial_estilos(codigo_estilo, version_calculo);

-- Índice 5: WIPs por tipo
CREATE INDEX IF NOT EXISTS idx_wip_tipo_version
ON silver.resumen_wip_por_prenda(tipo_prenda, version_calculo);

-- Verificar que se crearon:
-- SELECT schemaname, tablename, indexname FROM pg_indexes WHERE schemaname = 'silver';
```

---

## 📋 CHECKLIST FASE 1

- [x] ✅ Actualizar `VersionCalculo` enum (COMPLETADO)
- [ ] ⏳ Eliminar endpoint `/verificar-estilo-completo` duplicado
- [ ] ⏳ Remover campo `_debug` de respuestas
- [ ] ⏳ Reducir logging excesivo
- [ ] ⏳ Refactorizar queries duplicadas (crear helper)
- [ ] ⏳ Crear índices en BD
- [ ] ⏳ Levantar v8 y probar cambios

---

## 🔄 CÓMO PROCEDER

### Paso 1: Eliminar endpoint duplicado
```bash
# Abrir: backend/src/smp/main.py
# Ir a línea: 1023
# Seleccionar desde línea 1023 a 1151
# BORRAR completamente
# Cambiar línea 199 de /verificar-estilo-completo a /api/v1/estilos/{codigo}
```

### Paso 2: Remover _debug
```bash
# Buscar en main.py: "_debug"
# Encontrará en línea ~795
# Remover toda la sección
```

### Paso 3: Reducir logs
```bash
# Buscar en main.py: "logger.info(f\" [ENDPOINT-"
# Encontrará 5+ líneas
# Reemplazar con patrón nuevo
```

### Paso 4: Crear helper de queries
```bash
# Abrir: backend/src/smp/database.py
# Encontrar clase TDVQueries (línea ~300)
# Agregar método _query_costo_op_detalle después de __init__
# Reemplazar calls en otros métodos
```

### Paso 5: Crear índices
```bash
# Conectar a PostgreSQL:
psql -h 18.118.59.50 -U david -d tdv

# Ejecutar SQL:
# (copiar los CREATE INDEX de arriba)
```

---

## 🎯 PRÓXIMO: FASE 2

Una vez completada Fase 1:
1. Levantar v8 y probar
2. Validar que endpoints funcionan
3. Verificar que no haya errores
4. Comenzar Fase 2: Arquitectura de capas

---

**Creado por:** Claude Code
**Versión:** 1.0
**Estado:** Guía de implementación para FASE 1
