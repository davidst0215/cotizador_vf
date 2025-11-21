# EXPLICACIÓN DETALLADA: CÁLCULO DE HILOS EN TABLA DESGLOSE

## Resumen Ejecutivo
La tabla de **Desglose de Hilos** implementa una **agregación de dos niveles**:
1. **NIVEL 1 (Backend SQL)**: SUM de kg_por_prenda dentro de cada OP
2. **NIVEL 2 (Backend SQL)**: AVG de esos SUMs entre las diferentes OPs

Esto significa que para cada hilo, se suma lo que aparece en cada OP por separado, y luego se promedian esos totales.

---

## EJEMPLO CON ESTILO 18738 (2 OPs)

Supongamos que el estilo 18738 tiene 2 OPs:
- OP-2024-0001
- OP-2024-0002

Y el hilo **HILO-789 (Tipo: Regular)** aparece en ambas OPs.

### PASO 1: DATOS CRUDOS EN LA BD (tabla costo_hilados_detalle_op)

La tabla tiene **múltiples registros** para el mismo hilo dentro de la misma OP (porque hay múltiples prendas o registros de la misma fecha_corrida).

```
OP-2024-0001:
  Registro 1: HILO-789, kg_por_prenda=1.5, costo_total_original=100
  Registro 2: HILO-789, kg_por_prenda=1.5, costo_total_original=100
  Registro 3: HILO-789, kg_por_prenda=2.0, costo_total_original=150

OP-2024-0002:
  Registro 1: HILO-789, kg_por_prenda=1.0, costo_total_original=80
  Registro 2: HILO-789, kg_por_prenda=1.5, costo_total_original=120
```

### PASO 2: AGREGACIÓN NIVEL 1 (SUM POR OP)

Se ejecuta un CTE llamado `hilos_por_op` que hace:
```sql
SELECT
    cod_hilado,        -- HILO-789
    tipo_hilo,         -- Regular
    op_codigo,         -- OP-2024-0001 o OP-2024-0002
    SUM(kg_por_prenda) as kg_por_prenda_sum,
    SUM(costo_total_original) as costo_total_sum,
    ...
FROM costo_hilados_detalle_op
WHERE op_codigo IN (...)
GROUP BY cod_hilado, tipo_hilo, op_codigo
```

**Resultado NIVEL 1:**

```
HILO-789, Regular, OP-2024-0001:
  kg_sum = 1.5 + 1.5 + 2.0 = 5.0 kg
  costo_sum = 100 + 100 + 150 = 350

HILO-789, Regular, OP-2024-0002:
  kg_sum = 1.0 + 1.5 = 2.5 kg
  costo_sum = 80 + 120 = 200
```

### PASO 3: AGREGACIÓN NIVEL 2 (AVG ENTRE OPs)

Se ejecuta el SELECT final que hace:
```sql
SELECT
    cod_hilado,        -- HILO-789
    tipo_hilo,         -- Regular
    AVG(kg_por_prenda_sum) as kg_por_prenda,
    AVG(costo_total_sum) as costo_total_original,
    COUNT(DISTINCT op_codigo) as frecuencia_ops
FROM hilos_por_op
GROUP BY cod_hilado, tipo_hilo
```

**Resultado NIVEL 2 (LO QUE VES EN LA TABLA):**

```
HILO-789, Regular:
  kg_por_prenda = (5.0 + 2.5) / 2 = 3.75 kg ✅
  costo_total = (350 + 200) / 2 = 275 ✅
  frecuencia_ops = 2 (aparece en 2 OPs)
```

### PASO 4: CÁLCULOS FINALES (EN EL FRONTEND)

Con los valores del NIVEL 2, el frontend calcula:

```
kg_requeridos (desde BD, también promediado)

costo_por_kg = costo_total / kg_requeridos
             = 275 / [valor_promediado]

costo_por_prenda_final = costo_por_kg × kg_por_prenda
                       = [valor_calculado] × 3.75
```

---

## DIAGRAMA DEL FLUJO

```
┌─────────────────────────────────────────────────────┐
│ TABLA costo_hilados_detalle_op (DATOS CRUDOS)      │
│                                                     │
│ OP-2024-0001: 3 registros para HILO-789            │
│ OP-2024-0002: 2 registros para HILO-789            │
└──────────────────────┬──────────────────────────────┘
                       ↓
        ┌──────────────────────────────┐
        │ NIVEL 1: SUM POR OP          │
        │ (CTE: hilos_por_op)          │
        ├──────────────────────────────┤
        │ OP-2024-0001: kg_sum=5.0     │
        │ OP-2024-0002: kg_sum=2.5     │
        └──────────────┬───────────────┘
                       ↓
        ┌──────────────────────────────┐
        │ NIVEL 2: AVG ENTRE OPs       │
        │ (SELECT final de la query)   │
        ├──────────────────────────────┤
        │ kg_por_prenda = 3.75         │
        │ frecuencia_ops = 2           │
        └──────────────┬───────────────┘
                       ↓
    ┌──────────────────────────────────────────┐
    │ TABLA FINAL: Desglose de Hilos           │
    │ (Lo que ves en la interfaz)              │
    ├──────────────────────────────────────────┤
    │ HILO-789: kg=3.75, freq=2, costo=...    │
    └──────────────────────────────────────────┘
```

---

## CÓDIGO SQL COMPLETO (obtener_hilos_para_estilo)

```sql
WITH max_fechas AS (
    -- Obtener la fecha_corrida MÁS RECIENTE para cada OP
    SELECT
        op_codigo,
        MAX(fecha_corrida) as fecha_corrida_max
    FROM costo_hilados_detalle_op
    WHERE op_codigo IN ('OP-2024-0001', 'OP-2024-0002')
    GROUP BY op_codigo
),
hilos_por_op AS (
    -- NIVEL 1: SUM por OP
    -- Esto suma todos los registros del mismo hilo dentro de una OP
    SELECT
        chdo.cod_hilado,
        chdo.descripcion_hilo,
        chdo.tipo_hilo,
        chdo.op_codigo,
        SUM(chdo.kg_por_prenda) as kg_por_prenda_sum,
        SUM(chdo.costo_total_original) as costo_total_sum,
        SUM(chdo.kg_requeridos) as kg_requeridos_sum,
        SUM(chdo.prendas_requeridas) as prendas_requeridas_sum
    FROM costo_hilados_detalle_op chdo
    INNER JOIN max_fechas mf
        ON chdo.op_codigo = mf.op_codigo
        AND chdo.fecha_corrida = mf.fecha_corrida_max
    WHERE chdo.op_codigo IN ('OP-2024-0001', 'OP-2024-0002')
    GROUP BY
        chdo.cod_hilado,
        chdo.descripcion_hilo,
        chdo.tipo_hilo,
        chdo.op_codigo
)
SELECT
    -- NIVEL 2: AVG entre OPs
    -- Promedia los SUMs de NIVEL 1 entre las diferentes OPs
    cod_hilado,
    descripcion_hilo,
    tipo_hilo,
    AVG(kg_por_prenda_sum) as kg_por_prenda,
    AVG(costo_total_sum) as costo_total_original,
    AVG(kg_requeridos_sum) as kg_requeridos,
    AVG(prendas_requeridas_sum) as prendas_requeridas,
    COUNT(DISTINCT op_codigo) as frecuencia_ops
FROM hilos_por_op
GROUP BY
    cod_hilado,
    descripcion_hilo,
    tipo_hilo
ORDER BY descripcion_hilo
```

---

## PUNTOS CLAVE

### ✅ LO CORRECTO

1. **Filtrado por `max_fechas`**: Solo se usan los registros de la fecha_corrida MÁS RECIENTE para cada OP
   - Evita duplicados de fechas anteriores
   - Asegura que solo tengas UNA VERSIÓN de los datos por OP

2. **Agregación de dos niveles**:
   - **Nivel 1**: SUM dentro de cada OP
   - **Nivel 2**: AVG entre OPs
   - Esto es matemáticamente correcto para promediar OPs

3. **Parámetro `frecuencia_ops`**: Indica en cuántas OPs del estilo aparece cada hilo
   - Útil para ver "este hilo se usa en 2 de 3 OPs del estilo"

4. **Valores promediados**:
   - `kg_por_prenda` es el PROMEDIO del kg/prenda entre las OPs
   - `costo_total_original` es el PROMEDIO del costo entre las OPs
   - Esto es útil cuando tienes OPs con cantidades diferentes

### ⚠️ QUÉ VERIFICAR SI NO CUADRAN LOS VALORES

1. **¿Hay múltiples registros para el mismo hilo en la misma OP?**
   - Si es así, NIVEL 1 sumará todos esos registros ✅ (correcto)

2. **¿Hay múltiples fechas_corrida?**
   - Si es así, solo se usa MAX(fecha_corrida) ✅ (correcto)
   - Verifica que `max_fechas` esté filtrando correctamente

3. **¿El AVG es realmente lo que quieres?**
   - Si tienes 2 OPs con kg_sum=5 y kg_sum=2.5, el AVG=3.75 ✅ (correcto)
   - Pero si quieres el TOTAL, sería SUM=7.5

---

## EJEMPLO NUMÉRICO COMPLETO

**Estilo 18738 con 2 OPs:**

### OP-2024-0001 (DATOS CRUDOS):
```
HILO-001: 1.5 + 1.5 + 2.0 = 5.0 kg, costo 350
HILO-002: 0.5 + 0.5 = 1.0 kg, costo 50
HILO-003: 3.0 = 3.0 kg, costo 300
```

### OP-2024-0002 (DATOS CRUDOS):
```
HILO-001: 1.0 + 1.5 = 2.5 kg, costo 200
HILO-002: 2.0 = 2.0 kg, costo 100
HILO-004: 1.5 = 1.5 kg, costo 75
```

### RESULTADO FINAL (TABLA DESGLOSE):
```
HILO-001: kg_avg=3.75, costo_avg=275, freq=2 ✅
HILO-002: kg_avg=1.5,  costo_avg=75,  freq=2 ✅
HILO-003: kg_avg=3.0,  costo_avg=300, freq=1 ✅
HILO-004: kg_avg=1.5,  costo_avg=75,  freq=1 ✅
```

---

## DIFERENCIA CON FILTRO POR OPs SELECCIONADAS

**ANTES (cuando filtraba por OPs seleccionadas):**
- Mostraba solo los hilos de las OPs que tenías checked
- Si marcabas OP-2024-0001, solo veías hilos de esa OP

**AHORA (filtro por estilo):**
- Muestra TODOS los hilos del estilo, independientemente de qué OPs tengas marcadas
- Si tienes el estilo 18738, ve TODOS los hilos de ese estilo
- El marcado de OPs es SOLO para telas
- kg_por_prenda es PROMEDIO entre todas las OPs del estilo

Este cambio es importante porque:
- El costo de un hilo en un estilo es más consistente si lo promedias
- No depende de qué OPs específicas tengas seleccionadas
- Refleja mejor el uso "típico" del hilo en ese estilo

