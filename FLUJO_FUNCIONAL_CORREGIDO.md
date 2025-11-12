# 🎯 FLUJO FUNCIONAL CORREGIDO - COTIZADOR TDV v8

**Versión:** 2.0 (Corregida)
**Cambios:** Removidas familia + temporada, flujo secuencial correctamente ordenado

---

## 📍 FLUJO PASO A PASO (CORRECTO)

Imagina que **Sofía** necesita cotizar 500 polos para LACOSTE con estilo LAC001.

### 1️⃣ **SOFÍA ABRE LA APP**
```
Frontend (Next.js React) en http://localhost:3000
├─ Formulario con campos:
│  ├─ Cliente/Marca ✓
│  ├─ Código Estilo ✓
│  ├─ Cantidad de Prendas ✓
│  ├─ Tipo de Prenda ✓
│  ├─ ❌ REMOVER: Familia (no se usa)
│  ├─ ❌ REMOVER: Temporada (no se usa)
│  └─ Versión Cálculo (default: FLUIDA)
└─ "Ingresa código estilo LAC001"
```

---

### 2️⃣ **SOFÍA INGRESA EL CÓDIGO DE ESTILO**
```
Sofía escribe: "LAC001"
         │
         ↓
Frontend valida:
├─ No está vacío ✓
├─ Formato válido ✓
└─ Envía: GET /api/v1/estilos/LAC001?version=FLUIDA

⏱️ Latencia red: ~50ms
```

---

### 3️⃣ **BACKEND BUSCA INFORMACIÓN DEL ESTILO**
```
Backend ejecuta 2 QUERIES (no 3):

QUERY 1: Obtener metadata del estilo
┌─────────────────────────────────────────┐
│ SELECT * FROM historial_estilos         │
│ WHERE codigo_estilo = 'LAC001'          │
│   AND version_calculo = 'FLUIDA'        │
└─────────────────────────────────────────┘
         │
         ↓ Resultado:
         ├─ codigo_estilo: LAC001
         ├─ volumen_historico: 15,000 prendas
         ├─ categoria: "Muy Recurrente"
         └─ ultima_produccion: 2025-10-15

⏱️ BD Query: ~100ms


QUERY 2: Obtener últimas OPs de este estilo
┌─────────────────────────────────────────┐
│ SELECT cod_ordpro, prendas_requeridas,  │
│        costo_textil, costo_manufactura, │
│        costo_avios, costo_materia_prima,│
│        ... todos los componentes        │
│ FROM costo_op_detalle                   │
│ WHERE estilo_propio = 'LAC001'          │
│   AND version_calculo = 'FLUIDA'        │
│   AND fecha_facturacion >= (HOY - 12mo) │
│ ORDER BY fecha_facturacion DESC         │
│ LIMIT 100                               │
└─────────────────────────────────────────┘
         │
         ↓ Resultado: Lista de 50+ OPs
         ├─ OP-42567 | 1000 prendas | $2.50 textil | $1.80 mfg | ...
         ├─ OP-42568 | 800 prendas  | $2.48 textil | $1.85 mfg | ...
         ├─ OP-42569 | 500 prendas  | $2.52 textil | $1.78 mfg | ...
         ├─ OP-42570 | 1200 prendas | $2.49 textil | $1.82 mfg | ...
         └─ ... (más OPs)

⏱️ BD Query: ~150ms

⏱️ TOTAL Backend: ~250ms
```

---

### 4️⃣ **BACKEND RETORNA INFORMACIÓN (SIN CÁLCULOS)**
```
Backend responde:

{
  "codigo_estilo": "LAC001",
  "categoria": "Muy Recurrente",
  "volumen_historico": 15000,
  "factor_estilo": 0.95,        ← Ya se calcula aquí

  "ops_disponibles": [
    {
      "cod_ordpro": "OP-42567",
      "prendas_requeridas": 1000,
      "fecha_facturacion": "2025-11-01",
      "costo_textil": 2.50,
      "costo_manufactura": 1.80,
      "costo_avios": 0.30,
      "costo_materia_prima": 0.40,
      "costo_indirecto_fijo": 0.48,
      "esfuerzo_total": 4
    },
    {
      "cod_ordpro": "OP-42568",
      "prendas_requeridas": 800,
      ... (misma estructura)
    },
    ... (50+ OPs más)
  ]
}

✅ IMPORTANTE: NO se calcula precio aquí
✅ IMPORTANTE: Se devuelven todos los datos para que usuario elija OPs
```

---

### 5️⃣ **FRONTEND MUESTRA TABLA DE OPs**
```
┌──────────────────────────────────────────────────────────┐
│ ESTILO: LAC001 - Muy Recurrente (15,000 prendas)        │
├──────────────────────────────────────────────────────────┤
│ ☑️ OP-42567 | 1000 | $2.50 | $1.80 | $0.30 | Total: ... │
│ ☑️ OP-42568 | 800  | $2.48 | $1.85 | $0.30 | Total: ... │
│ ☐ OP-42569 | 500  | $2.52 | $1.78 | $0.30 | Total: ... │
│ ☑️ OP-42570 | 1200 | $2.49 | $1.82 | $0.30 | Total: ... │
│ ☐ OP-42571 | 600  | $2.51 | $1.80 | $0.30 | Total: ... │
│                                                          │
│ OPs seleccionadas: 3                                     │
│ Total prendas: 3,000                                     │
│                                                          │
│ [COTIZAR CON OPs SELECCIONADAS]                         │
└──────────────────────────────────────────────────────────┘

✅ Frontend NO calcula nada
✅ Frontend SOLO muestra datos y permite seleccionar
```

---

### 6️⃣ **SOFÍA SELECCIONA OPs Y ESPECIFICA CANTIDAD**
```
Sofía selecciona:
├─ OP-42567 (1000 prendas) ✓
├─ OP-42568 (800 prendas) ✓
├─ OP-42570 (1200 prendas) ✓
└─ Especifica cantidad final: 500 prendas

⚠️ NOTA: Cantidad final (500) puede ser DIFERENTE
   a la suma de OPs (3000). Sofía cotiza "como si fuera"
   una de estas OPs pero con 500 cantidad en lugar de 1000.
```

---

### 7️⃣ **SOFÍA HACE CLIC EN "COTIZAR"**
```
Frontend envía:

POST /api/v1/cotizaciones
{
  "cliente_marca": "LACOSTE",
  "tipo_prenda": "Polo",
  "cantidad_prendas": 500,              ← LA CANTIDAD FINAL
  "codigo_estilo": "LAC001",
  "ops_seleccionadas": [
    {"cod_ordpro": "OP-42567"},
    {"cod_ordpro": "OP-42568"},
    {"cod_ordpro": "OP-42570"}
  ],
  "version_calculo": "FLUIDA"
}

⏱️ Latencia red: ~50ms

❌ REMOVIDO: familia_producto
❌ REMOVIDO: temporada
```

---

### 8️⃣ **BACKEND CALCULA PRECIO (AQUÍ ES DONDE OCURRE)**
```
Backend recibe request y AHORA calcula:

PASO 1: Verificar categoría estilo
├─ Ya la tiene de Query 1 anterior
├─ LAC001 = "Muy Recurrente"
└─ Factor Estilo = 0.95

PASO 2: Promediar costos de OPs SELECCIONADAS
├─ Obtiene datos de las 3 OPs seleccionadas
├─ Calcula promedio:
│  ├─ Costo textil promedio: ($2.50 + $2.48 + $2.49) / 3 = $2.49
│  ├─ Costo manufactura promedio: ($1.80 + $1.85 + $1.82) / 3 = $1.82
│  ├─ Costo avíos promedio: ($0.30 + $0.30 + $0.30) / 3 = $0.30
│  ├─ Costo materia prima promedio: $0.40
│  ├─ Costo indirecto promedio: $0.48
│  └─ SUBTOTAL PROMEDIADO: $5.49
│
└─ ✅ IMPORTANTE: Solo usa las 3 OPs seleccionadas
   NO usa todas las 50+ OPs

PASO 3: Categorizar lote (por cantidad FINAL = 500)
├─ 500 entra en "Lote Mediano" (501-1000)
└─ Factor Lote = 1.05

PASO 4: Obtener factor marca
├─ Cliente: "LACOSTE"
├─ LACOSTE es premium
└─ Factor Marca = 1.05

PASO 5: Obtener factor esfuerzo
├─ Promedio de esfuerzo de OPs seleccionadas
├─ ($4 + $4 + $4) / 3 = 4 (BAJO)
└─ Factor Esfuerzo = 0.90

PASO 6: Calcular precio final
├─ Costo Base Promediado: $5.49
├─ × Factor Estilo (0.95): $5.49 × 0.95 = $5.22
├─ × Factor Lote (1.05): $5.22 × 1.05 = $5.48
├─ × Factor Esfuerzo (0.90): $5.48 × 0.90 = $4.93
├─ × Factor Marca (1.05): $4.93 × 1.05 = $5.17
├─ + Margen (5%): $5.17 × 1.05 = $5.43
└─ PRECIO FINAL: $5.43 por prenda

PASO 7: Calcular totales
├─ Precio Total: 500 × $5.43 = $2,715
├─ Margen Total: $2,715 × 5% = $135.75
└─ Costo Base Total: $2,715 - $135.75 = $2,579.25

⏱️ Cálculo: ~100ms
```

---

### 9️⃣ **BACKEND RETORNA COTIZACIÓN COMPLETA**
```
{
  "id_cotizacion": "CTZ-20251112-LAC001-001",
  "fecha_cotizacion": "2025-11-12T10:45:30Z",

  "inputs": {
    "cliente_marca": "LACOSTE",
    "tipo_prenda": "Polo",
    "cantidad_prendas": 500,
    "codigo_estilo": "LAC001",
    "ops_seleccionadas": ["OP-42567", "OP-42568", "OP-42570"],
    "version_calculo": "FLUIDA"
  },

  "componentes": {
    "costo_textil": 2.49,
    "costo_manufactura": 1.82,
    "costo_avios": 0.30,
    "costo_materia_prima": 0.40,
    "costo_indirecto_fijo": 0.48,
    "subtotal_costos": 5.49
  },

  "factores_aplicados": {
    "estilo": {
      "categoria": "Muy Recurrente",
      "volumen_historico": 15000,
      "factor": 0.95
    },
    "lote": {
      "categoria": "Lote Mediano",
      "cantidad": 500,
      "factor": 1.05
    },
    "esfuerzo": {
      "nivel": "Bajo",
      "esfuerzo_promedio": 4,
      "factor": 0.90
    },
    "marca": {
      "cliente": "LACOSTE",
      "factor": 1.05
    }
  },

  "costo_base_total": 2579.25,      # 500 × $5.49
  "precio_ajustado": 2579.25,       # Después de aplicar factores
  "margen": 135.75,                 # 5%
  "precio_final_total": 2715.00,    # $5.43 × 500
  "precio_unitario": 5.43
}
```

---

### 🔟 **FRONTEND MUESTRA RESULTADO**
```
┌────────────────────────────────────────────────────────┐
│ ✅ COTIZACIÓN COMPLETADA                               │
│                                                        │
│ ID: CTZ-20251112-LAC001-001                           │
│ Fecha: 12 Nov 2025 - 10:45 AM                         │
│                                                        │
│ CLIENT: LACOSTE                                        │
│ ESTILO: LAC001 (Muy Recurrente)                       │
│ CANTIDAD: 500 Polos                                    │
│                                                        │
│ ════════════════════════════════════════════════════  │
│ DESGLOSE DE COSTOS (PROMEDIO OPs SELECCIONADAS):      │
│ ────────────────────────────────────────────────────  │
│ • Textil............... $2.49                         │
│ • Manufactura.......... $1.82                         │
│ • Avíos................ $0.30                         │
│ • Materia Prima........ $0.40                         │
│ • Indirectos........... $0.48                         │
│ ────────────────────────────────────────────────────  │
│ Subtotal Costo......... $5.49                         │
│                                                        │
│ ════════════════════════════════════════════════════  │
│ FACTORES APLICADOS:                                    │
│ ────────────────────────────────────────────────────  │
│ • Estilo (Muy Recurrente).... 0.95x ✓               │
│ • Lote (Mediano)............. 1.05x ✓               │
│ • Esfuerzo (Bajo)............ 0.90x ✓               │
│ • Marca (LACOSTE)............ 1.05x ✓               │
│                                                        │
│ ════════════════════════════════════════════════════  │
│ PRECIO FINAL:                                          │
│ ────────────────────────────────────────────────────  │
│ Costo Ajustado........... $2,579.25                   │
│ Margen (5%)............. $135.75                      │
│ ────────────────────────────────────────────────────  │
│ PRECIO UNITARIO......... $5.43                        │
│ PRECIO TOTAL (500)...... $2,715.00                    │
│                                                        │
│ ════════════════════════════════════════════════════  │
│                                                        │
│ Sofía: "Perfecto, vendo a $5.43 por prenda"         │
│                                                        │
│ [GUARDAR] [PDF] [NUEVA COTIZACIÓN]                   │
└────────────────────────────────────────────────────────┘
```

---

## 📊 COMPARACIÓN: FLUJO VIEJO vs NUEVO

### ❌ FLUJO VIEJO (v7 - INCORRECTO)

```
1. Usuario ingresa código estilo
2. Backend CALCULA precio promedio ANTES de que user seleccione OPs
3. Frontend muestra tabla de OPs
4. Usuario selecciona OPs
5. Backend RECALCULA precio (con las OPs seleccionadas)

PROBLEMA: ¿Para qué calcular primero si el usuario puede seleccionar OPs diferentes?
```

### ✅ FLUJO NUEVO (v8 - CORRECTO)

```
1. Usuario ingresa código estilo
2. Backend SOLO busca OPs (sin calcular precio)
3. Frontend muestra tabla de OPs
4. Usuario selecciona OPs Y especifica cantidad
5. Backend CALCULA precio SOLO UNA VEZ (con OPs seleccionadas)

VENTAJA: Lógica clara, secuencial, eficiente
```

---

## 🎯 CAMPOS QUE SE USAN

### ✅ CAMPOS A MANTENER
```
Frontend Input:
├─ cliente_marca (LACOSTE, LULULEMON, etc)
├─ codigo_estilo (LAC001)
├─ cantidad_prendas (500)
├─ tipo_prenda (Polo, T-Shirt, etc)
├─ ops_seleccionadas (lista de OPs a promediar)
└─ version_calculo (FLUIDA, truncado)

Backend Output:
├─ componentes_costo (textil, manufactura, etc)
├─ factores_aplicados (estilo, lote, marca, esfuerzo)
├─ precio_unitario
├─ precio_total
└─ id_cotizacion
```

### ❌ CAMPOS A REMOVER
```
❌ familia_producto - No se usa en cálculos
❌ temporada - No se usa en cálculos

NOTA: tipo_prenda ES DIFERENTE a familia_producto
      tipo_prenda = "Polo" (específico)
      familia_producto = "Polos" (categoría amplia)

      Solo necesitamos tipo_prenda
```

---

## ⏱️ RESUMEN TIMING

```
Paso 1: Usuario ingresa código
        └─ Frontend: 10ms

Paso 2: Backend busca info estilo + OPs
        └─ BD Query 1 (historial): 100ms
        └─ BD Query 2 (costo_op_detalle): 150ms
        └─ Total Backend: 250ms

Paso 3: Frontend muestra tabla
        └─ Frontend: 20ms

Paso 4: Usuario selecciona OPs
        └─ Frontend: 0ms (local)

Paso 5: Backend calcula precio (con OPs seleccionadas)
        └─ Cálculo en memoria: 100ms
        └─ Total Backend: 100ms

Paso 6: Frontend muestra cotización
        └─ Frontend: 20ms

═════════════════════════════════════════════════════════════
TOTAL: ~550ms (incluyendo latencias de red)

CON CACHÉ (v8):
- Si mismo estilo ya se consultó: 10ms (desde Redis)
- Paso 2 se reduce a: 60ms
- TOTAL: ~190ms (3x MÁS RÁPIDO)
```

---

## 📋 CAMBIOS A REALIZAR EN CÓDIGO

### Backend (models.py)
```python
# REMOVER de CotizacionInput:
# ❌ familia_producto: str
# ❌ temporada: str

# MANTENER:
# ✅ cliente_marca: str
# ✅ codigo_estilo: str
# ✅ cantidad_prendas: int
# ✅ tipo_prenda: str
# ✅ ops_seleccionadas: List[Dict]
# ✅ version_calculo: VersionCalculo
```

### Backend (main.py)
```python
# REMOVER validaciones de:
# ❌ familia_producto
# ❌ temporada

# MANTENER validaciones de:
# ✅ cliente_marca
# ✅ codigo_estilo
# ✅ cantidad_prendas (> 0)
# ✅ tipo_prenda
# ✅ ops_seleccionadas (no vacío)
```

### Frontend (SistemaCotizadorTDV.tsx)
```typescript
// REMOVER campos:
// ❌ const [familiaProducto, setFamiliaProducto] = useState("")
// ❌ const [temporada, setTemporada] = useState("")

// MANTENER campos:
// ✅ const [clienteMarca, setClienteMarca] = useState("")
// ✅ const [codigoEstilo, setCodigoEstilo] = useState("")
// ✅ const [cantidadPrendas, setCantidadPrendas] = useState(0)
// ✅ const [tipoPrenda, setTipoPrenda] = useState("")
```

---

## ✅ CHECKLIST CORRECCIONES

- [ ] Backend: Remover familia_producto de models.py
- [ ] Backend: Remover temporada de models.py
- [ ] Backend: Remover validaciones de estos campos en main.py
- [ ] Backend: Remover estos campos de database.py queries
- [ ] Frontend: Remover inputs de familia y temporada del formulario
- [ ] Frontend: Remover useState para estos campos
- [ ] Frontend: Remover envío de estos campos en POST /cotizar
- [ ] Actualizar documentación de API
- [ ] Validar que flujo secuencial sea correcto

---

**Versión:** 2.0 (Corregida)
**Fecha:** 2025-11-12
**Estado:** Listo para implementación en v8
