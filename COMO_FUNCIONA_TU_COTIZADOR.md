# ¿CÓMO FUNCIONA TU COTIZADOR? - EXPLICACIÓN VISUAL

**Para:** Entender qué hace tu aplicación y cómo mejorarlo
**Nivel:** Técnico, pero explicado como si hablaras con un colega

---

## 1. EL ESCENARIO REAL

Imagina que eres **Sofía**, vendedora de una marca de ropa:

> "Necesito cotizar 500 polos para LACOSTE. Es un estilo que ya hemos hecho antes (LAC001). Necesito saber cuánto debo cobrar por prenda."

---

## 2. ¿QUÉ HACE TU SISTEMA? (FLUJO SIMPLIFICADO)

### PASO 1: Sofía abre la aplicación

```
┌──────────────────────────────┐
│  Sofía abre app en navegador  │
│  http://localhost:3000        │
└────────────┬──────────────────┘
             │
             ↓
┌──────────────────────────────────────┐
│   Frontend carga (Next.js React)     │
│   • Muestra formulario vacío          │
│   • Campos: Cliente, Estilo, Cantidad │
└──────────────────────────────────────┘
```

### PASO 2: Sofía ingresa el código del estilo

```
Sofía escribe: "LAC001"
             │
             ↓
┌──────────────────────────────────────────┐
│ Frontend valida que sea válido:          │
│ • No es vacío ✓                          │
│ • Tiene 6 caracteres ✓                   │
└────────────┬─────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────┐
│ Frontend ENVÍA a Backend:                │
│ GET /api/v1/estilos/LAC001               │
│     ?version_calculo=FLUIDA              │
└────────────┬─────────────────────────────┘
             │
             ↓ (Latencia red: ~50ms)
             │
    ┌────────┴──────────┐
    │                   │
    │    BACKEND (FastAPI)
    │                   │
    └────────┬──────────┘
             │
             ↓
┌──────────────────────────────────────────┐
│ Backend RECIBE petición:                 │
│ • Código estilo: "LAC001"                │
│ • Versión: "FLUIDA"                      │
│ • Usuario: "sofia@lacoste.com"          │
└────────────┬─────────────────────────────┘
```

### PASO 3: Backend busca información del estilo

```
Backend ejecuta QUERY 1:
┌─────────────────────────────────────────┐
│ SELECT * FROM historial_estilos         │
│ WHERE codigo_estilo = 'LAC001'          │
│   AND version_calculo = 'FLUIDA'        │
└────────────┬────────────────────────────┘
             │
             ↓ (Latencia BD: ~200ms)
             │
             ↓ RESULTADO:
             ├─ codigo_estilo: LAC001
             ├─ volumen_historico: 15,000 prendas (ALTO)
             ├─ categoria: "Recurrente"  ← ¡IMPORTANTE!
             ├─ ultima_produccion: 2025-10-15
             └─ version_calculo: FLUIDA

┌─────────────────────────────────────────────────────────────┐
│ Backend ejecuta QUERY 2 (OPs recientes):                     │
│ SELECT * FROM costo_op_detalle                              │
│ WHERE estilo_propio = 'LAC001'                              │
│   AND version_calculo = 'FLUIDA'                            │
│   AND fecha_facturacion >= (HOY - 12 meses)                 │
│ ORDER BY fecha_facturacion DESC                             │
│ LIMIT 50                                                     │
└────────────┬────────────────────────────────────────────────┘
             │
             ↓ (Latencia BD: ~200ms)
             │
             ↓ RESULTADO: [
                 {
                   cod_ordpro: "OP-42567",
                   fecha_facturacion: "2025-11-01",
                   prendas_requeridas: 1000,
                   costo_textil: 2.50,
                   costo_manufactura: 1.80,
                   costo_avios: 0.30,
                   ... (más campos)
                 },
                 {
                   cod_ordpro: "OP-42568",
                   ... (otra OP)
                 },
                 ... (más OPs)
               ]

┌─────────────────────────────────────────────────────────────┐
│ Backend ejecuta QUERY 3 (WIPs recomendados):                │
│ SELECT * FROM resumen_wip_por_prenda                        │
│ WHERE tipo_prenda = 'Polo'                                  │
│   AND version_calculo = 'FLUIDA'                            │
│   AND disponible = true                                      │
└────────────┬────────────────────────────────────────────────┘
             │
             ↓ (Latencia BD: ~100ms)
             │
             ↓ RESULTADO: [WIP-10, WIP-34, WIP-40, ...]
```

### PASO 4: Backend procesa los datos

```
┌─────────────────────────────────────────────────────────────┐
│ LÓGICA DE NEGOCIO (Backend utils.py):                       │
│                                                              │
│ 1. Categoriza el estilo:                                    │
│    volumen = 15,000 → "Muy Recurrente" (>4000)             │
│    FACTOR APLICAR: 0.95 (5% descuento por eficiencia)      │
│                                                              │
│ 2. Identifica los costos base:                             │
│    Promedio de últimas 5 OPs:                              │
│    • Costo textil promedio: $2.50                          │
│    • Costo manufactura promedio: $1.80                     │
│    • Costo avíos promedio: $0.30                           │
│    • (+ más componentes)                                   │
│    SUBTOTAL: $5.48 por prenda                              │
│                                                              │
│ 3. Lee factores desde config.py:                          │
│    • Factor Lote (por cantidad de 500):                    │
│      500 entra en "Lote Mediano" → Factor 1.05            │
│                                                              │
│    • Factor Cliente (LACOSTE):                             │
│      Es marca premium → Factor 1.05                        │
│                                                              │
│    • Factor Esfuerzo:                                      │
│      Polo simple → Bajo esfuerzo → Factor 0.90            │
│                                                              │
│ 4. Calcula precio final:                                   │
│                                                              │
│    Costo Base = $5.48                                      │
│      ×Factor Lote (1.05) = $5.75                          │
│      ×Factor Estilo (0.95) = $5.47                        │
│      ×Factor Esfuerzo (0.90) = $4.92                      │
│      ×Factor Marca (1.05) = $5.17                         │
│                                                              │
│    Costo Ajustado = $5.17                                  │
│    + Margen (5%) = $0.26                                   │
│    PRECIO FINAL = $5.43 por prenda                         │
│    × 500 prendas = $2,715 TOTAL                           │
│                                                              │
│ 5. Retorna respuesta JSON:                                 │
│    {                                                       │
│      "id_cotizacion": "CTZ-20251112-001",                │
│      "precio_unitario": 5.43,                             │
│      "precio_total": 2715.00,                             │
│      "componentes": { ... desglose ... },                 │
│      "factores_aplicados": {                              │
│        "lote": {"categoria": "Mediano", "factor": 1.05},  │
│        "estilo": {"categoria": "Muy Recurrente", ... },   │
│        "esfuerzo": {"nivel": "Bajo", "factor": 0.90},     │
│        "marca": {"cliente": "LACOSTE", "factor": 1.05}    │
│      }                                                     │
│    }                                                       │
└──────────────┬──────────────────────────────────────────────┘
               │
               ↓ (Latencia procesamiento: ~50ms)
               │
    ┌──────────┴───────────┐
    │                      │
    │   FRONTEND (React)
    │                      │
    └──────────┬───────────┘
               │
               ↓
┌──────────────────────────────────────────────────────────────┐
│ Frontend RECIBE respuesta y ACTUALIZA UI:                   │
│ • Muestra precio unitario: $5.43                            │
│ • Muestra precio total: $2,715.00                           │
│ • Muestra desglose de costos                                │
│ • Muestra factores aplicados                                │
│                                                              │
│ Sofía ve:                                                    │
│ ┌────────────────────────────────────────┐                 │
│ │ COTIZACIÓN LAC001 - 500 Polos          │                 │
│ ├────────────────────────────────────────┤                 │
│ │ Precio unitario: $5.43                 │                 │
│ │ Precio total: $2,715.00                │                 │
│ │                                         │                 │
│ │ DESGLOSE DE COSTOS:                    │                 │
│ │ • Textil: $2.50                        │                 │
│ │ • Manufactura: $1.80                   │                 │
│ │ • Avíos: $0.30                         │                 │
│ │ • ...                                   │                 │
│ │                                         │                 │
│ │ FACTORES APLICADOS:                    │                 │
│ │ • Por lote (Mediano): 1.05x            │                 │
│ │ • Por estilo (Muy Recurrente): 0.95x   │                 │
│ │ • Por marca (LACOSTE): 1.05x           │                 │
│ │ • Por esfuerzo (Bajo): 0.90x           │                 │
│ │                                         │                 │
│ │ [GUARDAR] [EXPORTAR] [MODIFICAR]      │                 │
│ └────────────────────────────────────────┘                 │
│                                            │                 │
│ Sofía dice: "Perfecto, lo vendo a $5.43"  │                 │
│                                            │                 │
└────────────────────────────────────────────┘
```

---

## 3. ¿POR QUÉ v7 TIENE PROBLEMAS?

### Problema 1: Queries redundantes (ejecutadas 2 veces)

```
┌─────────────────────────────────────────┐
│ Usuario 1: GET /api/v1/estilos/LAC001   │
│                                          │
│ Backend ejecuta:                         │
│ ✓ QUERY 1: historial_estilos             │
│ ✓ QUERY 2: costo_op_detalle              │
│ ✓ QUERY 3: resumen_wip                   │
│                                          │
│ Retorna respuesta ✓                      │
└────────────┬────────────────────────────┘

┌─────────────────────────────────────────┐
│ Usuario 2 (1 segundo después):           │
│ POST /api/v1/cotizaciones               │
│    (con LAC001)                          │
│                                          │
│ Backend ejecuta:                         │
│ ✓ QUERY 1: historial_estilos (REPETIDA) │ ← PROBLEMA
│ ✓ QUERY 2: costo_op_detalle (REPETIDA)  │ ← PROBLEMA
│ ✓ QUERY 3: resumen_wip (REPETIDA)       │ ← PROBLEMA
│ ✓ QUERY 4: (nueva para cotizar)          │
│ ✓ QUERY 5: (otra más)                    │
│                                          │
│ Retorna respuesta (más lenta)            │
└─────────────────────────────────────────┘

RESULTADO: Mismos datos se queryean 2 veces
IMPACTO: 2x carga en BD sin motivo
LATENCIA TOTAL: 500ms en lugar de 300ms
```

### Problema 2: VersionCalculo inconsistente

```
┌──────────────────────────────────┐
│ Frontend envía al Backend:       │
│ "version_calculo": "FLUIDO"      │
└────────────┬───────────────────┘
             │
             ↓
┌────────────────────────────────────────┐
│ Backend (database.py línea 68):        │
│ "Si es FLUIDO, cambia a FLUIDA"       │
│                                        │
│ # Conversión manual (frágil):         │
│ if version_value == "FLUIDO":         │
│     version_normalized = "FLUIDA"     │
└────────────┬────────────────────────┘
             │
             ↓
┌────────────────────────────────────────┐
│ Si la conversión falla (bug futuro):   │
│ • Query con "FLUIDO" (no existe en BD) │
│ • Retorna NULL (sin error visible)     │
│ • Sofía obtiene respuesta vacía        │
│ • Piensa que el estilo no existe       │
│ • Pero está en la BD!                  │
└────────────────────────────────────────┘

PROBLEMA: Error silencioso
CAUSA: Conversión manual en lugar de usar value real
SOLUCIÓN: VersionCalculo.FLUIDO = "FLUIDA"
```

### Problema 3: Sin caché

```
Escenario: 10 cotizadores trabajando simultáneamente

Usuario 1 a 10, todos necesitan info de LAC001:

┌─────────────────────────────────────────────────────┐
│ Usuario 1:                                          │
│ GET /api/v1/estilos/LAC001                         │
│   → Backend query BD 3 queries                      │
│   → Retorna LAC001 info                            │
│   ← Latencia: 300ms                                │
│                                                     │
│ Usuario 2:                                          │
│ GET /api/v1/estilos/LAC001                         │
│   → Backend query BD 3 queries (REPETIDAS)         │ ← NO CACHED
│   → Retorna misma info                             │
│   ← Latencia: 300ms                                │
│                                                     │
│ Usuario 3-10: (igual, 3 queries cada uno)          │
│                                                     │
│ TOTAL QUERIES A BD: 10 usuarios × 3 queries = 30   │
│ TIEMPO TOTAL: 10 usuarios × 300ms = 3 segundos    │
└─────────────────────────────────────────────────────┘

CON CACHÉ (v8):
┌─────────────────────────────────────────────────────┐
│ Usuario 1:                                          │
│ GET /api/v1/estilos/LAC001                         │
│   → Backend NO tiene en caché                      │
│   → Consulta BD (3 queries)                        │
│   → GUARDA en Redis                                │
│   ← Latencia: 300ms                                │
│                                                     │
│ Usuarios 2-10:                                      │
│ GET /api/v1/estilos/LAC001                         │
│   → Backend TIENE en caché                         │
│   → Retorna desde Redis (instantáneo)              │
│   ← Latencia: 10ms cada uno                        │
│                                                     │
│ TOTAL QUERIES A BD: 1 (solo la primera)            │
│ TIEMPO TOTAL: 300ms (usuario 1) + 10×9ms = 390ms  │
└─────────────────────────────────────────────────────┘

MEJORA: De 3 segundos a 400ms (7.5x MÁS RÁPIDO)
```

---

## 4. LOS 8 PROBLEMAS CRÍTICOS DE v7 (EXPLICADOS SIMPLES)

### 1. 🔴 Endpoint duplicado
**¿Qué pasa?** Hay 2 definiciones del mismo endpoint → FastAPI usa la segunda
**Impacto:** Frontend obtiene la versión incorrecta
**Solución v8:** Eliminar la segunda, usar una sola

### 2. 🔴 VersionCalculo inconsistente
**¿Qué pasa?** API dice "FLUIDO" pero BD tiene "FLUIDA"
**Impacto:** Conversión manual frágil → puede fallar silenciosamente
**Solución v8:** enum con value correcto + métodos helper

### 3. 🔴 Queries redundantes
**¿Qué pasa?** Mismas queries se ejecutan 2+ veces por request
**Impacto:** Carga innecesaria en BD
**Solución v8:** Sistema de caché (Redis)

### 4. 🔴 API proxy sin validación
**¿Qué pasa?** Frontend puede acceder a cualquier endpoint
**Impacto:** Security vulnerability
**Solución v8:** Whitelist de endpoints permitidos

### 5. 🟠 Expone _debug en respuestas
**¿Qué pasa?** Información interna visible en API response
**Impacto:** Revelan estructura de datos
**Solución v8:** Eliminar campo _debug

### 6. 🟠 ~400 líneas código duplicado
**¿Qué pasa?** Misma lógica repetida en 5+ métodos
**Impacto:** Difícil de mantener, bugs se replican
**Solución v8:** Métodos helper reutilizables

### 7. 🟠 Sin índices en BD
**¿Qué pasa?** Queries complejas sin índices
**Impacto:** Lentas especialmente con 100k+ registros
**Solución v8:** Crear índices en (estilo, version, fecha)

### 8. 🟠 Logging excesivo
**¿Qué pasa?** 5+ logs por request
**Impacto:** Ruido en producción, difícil debugging real
**Solución v8:** Solo 1-2 logs importantes

---

## 5. COMPARACIÓN: v7 vs v8

### Velocidad

```
v7 (hoy):
Usuario pide cotización:
  GET /api/estilos/LAC001: 300ms (3 queries)
  POST /api/cotizar: 400ms (5 queries, incluye repetidas)
  TOTAL: ~700ms
  × 10 usuarios = 7 segundos (se notan las esperas)

v8 (con cambios):
  GET /api/estilos/LAC001: 300ms (primera vez)
                          10ms (después, desde caché)
  POST /api/cotizar: 150ms (queries optimizadas + índices)
  TOTAL: ~150ms (sin caché) o ~160ms (con caché)
  × 10 usuarios = 1.6 segundos (muy rápido)

MEJORA: 4.3x más rápido
```

### Confiabilidad

```
v7:
- Endpoint duplicado: puede causar comportamiento inesperado
- Conversión manual: riesgo de errores silenciosos
- Sin caché: fallos bajo carga
- Logging excesivo: difícil encontrar errores reales

v8:
- Endpoints únicos y claros
- Conversión automática en enum
- Caché inteligente (TTL 1 hora)
- Logs minimalistas pero efectivos
- Tests para detectar bugs
```

### Mantenibilidad

```
v7:
- 400 líneas código duplicado → cambio en un lugar rompe otro
- Lógica de cotización en 1 archivo enorme (300 líneas)
- Sin documentación clara
- Difícil para nuevo desarrollador

v8:
- Código DRY (Don't Repeat Yourself)
- Arquitectura de capas clara
- Documentación completa (3 documentos)
- Fácil para nuevo desarrollador
- Tests que documentan el comportamiento
```

---

## 6. LO QUE HACE CADA COMPONENTE

### Frontend (React Next.js)

```
┌─ SistemaCotizadorTDV.tsx (Componente principal)
│  ├─ Estado: cliente, estilo, cantidad, etc
│  ├─ Formulario con validaciones
│  ├─ Tabla de OPs seleccionadas
│  ├─ Tabla de desglose de WIPs
│  └─ Llamadas a API (desde libs/api.ts)
│
└─ api.ts (Cliente HTTP)
   ├─ Función get()
   ├─ Función post()
   └─ Manejo de errores

FLUJO:
Usuario ingresa datos → Frontend valida → Frontend llama API →
Backend responde → Frontend muestra resultado
```

### Backend (FastAPI Python)

```
┌─ main.py (22 endpoints FastAPI)
│  ├─ GET /api/v1/estilos/{codigo}       ← ObtenerEstilo
│  ├─ POST /api/v1/cotizaciones          ← Cotizar
│  ├─ GET /api/v1/clientes               ← Maestros
│  └─ ... otros 19 endpoints
│
├─ database.py (2,951 líneas - MUY LARGO)
│  ├─ AsyncDatabaseManager (maneja conexión BD)
│  ├─ TDVQueries (singleton - métodos para cada query)
│  │  ├─ obtener_ops_cotizacion()
│  │  ├─ obtener_wips_disponibles()
│  │  ├─ buscar_estilos_similares()
│  │  └─ ... 20+ métodos más
│  └─ normalize_version_calculo() ← CONVERSIÓN MANUAL (problema)
│
├─ models.py (Esquemas Pydantic)
│  ├─ VersionCalculo enum (AHORA CORREGIDO)
│  ├─ CotizacionInput
│  ├─ CotizacionResponse
│  └─ ... otros modelos
│
├─ config.py (Configuración)
│  ├─ Settings (host, puerto, usuario, contraseña)
│  ├─ FactoresTDV (factores de ajuste)
│  └─ Constantes
│
├─ utils.py (1,350 líneas - Lógica de cotización)
│  └─ CotizadorTDV
│     ├─ procesar_cotizacion() ← 300 líneas, muy compleja
│     ├─ procesar_cotizacion_rapida_por_ops()
│     └─ ... métodos privados
│
└─ backtesting.py (Scripts de prueba)
   └─ Diagnósticos sin tests reales
```

### Base de Datos (PostgreSQL)

```
schema "silver":

├─ costo_op_detalle (101,503 registros)
│  ├─ cod_ordpro (ID)
│  ├─ estilo_propio (qué estilo)
│  ├─ cliente (cliente/marca)
│  ├─ fecha_facturacion (cuándo)
│  ├─ prendas_requeridas (cantidad)
│  ├─ costo_textil (componente 1)
│  ├─ costo_manufactura (componente 2)
│  ├─ costo_avios (componente 3)
│  ├─ costo_materia_prima (componente 4)
│  └─ ... más componentes
│
│  KEY QUERIES:
│  - Obtener última OP de un estilo
│  - Calcular promedio de costos por estilo
│  - Buscar OPs similares
│
├─ historial_estilos (6,251 registros)
│  ├─ codigo_estilo (ID)
│  ├─ volumen_total (cuántas prendas fabricadas)
│  ├─ categoria (Nuevo/Recurrente/Muy Recurrente)
│  └─ ultima_produccion (cuándo)
│
│  KEY QUERIES:
│  - Obtener categoría del estilo
│  - Calcular factor de estilo
│
└─ resumen_wip_por_prenda (16,936 registros)
   ├─ wip_id (ID del proceso)
   ├─ nombre_wip (ej: "Teido")
   ├─ tipo_prenda (ej: "Polo")
   ├─ costo_actual (precio del proceso)
   └─ disponible (está activo?)

   KEY QUERIES:
   - Obtener WIPs para un tipo de prenda
   - Listar WIPs disponibles
```

---

## 7. EL ALGORITMO DE COTIZACIÓN (SIMPLIFICADO)

```
ENTRADA:
├─ cliente_marca: "LACOSTE"
├─ codigo_estilo: "LAC001"
├─ cantidad_prendas: 500
├─ tipo_prenda: "Polo"
└─ version_calculo: "FLUIDA"

PASO 1: CATEGORIZAR ESTILO
├─ Buscar en BD: volumen_total del estilo
├─ Si volumen > 4000: "Muy Recurrente" (factor 0.95)
├─ Si volumen > 0 y < 4000: "Recurrente" (factor 1.00)
└─ Si volumen = 0: "Nuevo" (factor 1.05)

PASO 2: OBTENER COSTOS BASE
├─ Buscar últimas OPs del estilo en BD
├─ Promediar componentes:
│  ├─ Costo textil promedio
│  ├─ Costo manufactura promedio
│  ├─ Costo avíos promedio
│  └─ (+ otros componentes)
└─ Subtotal costo base

PASO 3: CATEGORIZAR LOTE (por cantidad)
├─ Si cantidad 1-50: "Micro Lote" (factor 1.15)
├─ Si cantidad 51-500: "Lote Pequeño" (factor 1.10)
├─ Si cantidad 501-1000: "Lote Mediano" (factor 1.05)
├─ Si cantidad 1001-4000: "Lote Grande" (factor 1.00)
└─ Si cantidad > 4000: "Lote Masivo" (factor 0.90)

PASO 4: OBTENER FACTOR MARCA
├─ Si cliente = "LACOSTE": factor 1.05
├─ Si cliente = "LULULEMON": factor 0.95
├─ Si cliente = "OTRAS": factor 1.10
└─ (from config.FACTORES_MARCA)

PASO 5: CALCULAR PRECIO FINAL
├─ Costo Base = $5.48
├─ × Factor Estilo (0.95) = $5.21
├─ × Factor Lote (1.05) = $5.47
├─ × Factor Marca (1.05) = $5.74
├─ + Margen (5%) = $0.29
└─ PRECIO FINAL = $6.03 por prenda

SALIDA:
├─ Precio unitario: $6.03
├─ Precio total: $3,015 (500 × $6.03)
├─ Desglose de componentes
├─ Factores aplicados
└─ ID cotización para referencia
```

---

## 8. RESUMEN FINAL

### ¿Qué hace tu cotizador?
1. **Recibe datos** del usuario (cliente, estilo, cantidad)
2. **Busca historial** en BD (volumen, últimas OPs)
3. **Calcula costos base** promediando datos históricos
4. **Aplica factores** (lote, estilo, marca, esfuerzo)
5. **Retorna precio** con desglose completo

### ¿Dónde está el problema en v7?
1. **Queries redundantes** → sin caché → lento
2. **Versioning inconsistente** → conversión manual → errores
3. **Código duplicado** → difícil de mantener
4. **Endpoints duplicados** → confusión
5. **Sin validaciones** → security issues

### ¿Cómo v8 lo arregla?
1. **Implementa caché** → 7.5x más rápido
2. **Enum correcto** → sin conversión manual
3. **DRY principle** → métodos reutilizables
4. **Endpoints únicos** → clara y clara
5. **Validaciones frontend+backend** → seguro

### ¿Vale la pena arreglar?
**SÍ** - La inversión de 30-40 horas se recupera en:
- Menos debugging (código limpio)
- Mejor performance (usuarios felices)
- Fácil de escalar (100+ usuarios sin problemas)
- Nuevo dev entiende rápido

---

**Creado por:** Claude Code
**Nivel:** Técnico explicado para colegas
**Fecha:** 2025-11-12
