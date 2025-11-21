# ANÁLISIS COMPARATIVO: populate_costo_materia_prima vs v3

## 1. DIFERENCIAS FUNDAMENTALES

### populate_costo_materia_prima (Original)
- **Granularidad**: Calcula costos a nivel de **OP completo** (agregado)
- **Tabla destino**: `silver.costo_materia_prima` (resumen por OP)
- **Flujo**:
  1. Obtiene todos los hilos de cada OP
  2. Suma costos por OP
  3. Aplica factor de ajuste mensual
  4. Inserta 1 registro por OP

### populate_costo_materia_prima_v3 (Nueva)
- **Granularidad**: Calcula costos a nivel de **HILO individual** dentro de cada OP
- **Tabla destino**: `silver.costo_hilados_detalle_op` (detalles por hilo/OP)
- **Flujo**:
  1. Obtiene cada hilo de cada OP por separado
  2. Calcula costo individual del hilo
  3. Aplica factor de ajuste mensual al hilo
  4. Inserta 1 registro por hilo/OP

---

## 2. FLUJO DE CÁLCULO - VERSIÓN ORIGINAL

```
PASO 1: Extrae OPs con actividad WIP
  └─> ops_base: 1 registro por OP

PASO 2: Calcula fechas de despacho (mes/año)
  └─> fechas_wip: 1 fecha por OP

PASO 3: COSTOS DE HILADOS AGREGADOS
  ├─> Tabla: requerimientos_hilados
  │   └─> 1 registro por hilo/OP (TODOS los hilos de la OP)
  │
  ├─> Tabla: mejor_costo_por_hilado
  │   └─> Busca mejor precio histórico para cada hilo/OP
  │
  └─> Tabla: costos_hilados
      └─> SUMA TODOS los hilos por OP
          └─> INSERT:
              - kg_hilados_total
              - inductor_hilados_original (=suma costos)
              - hilados_diferentes (COUNT hilos)

PASO 4: COSTOS DE TELA AGREGADOS
  └─> costos_tela: 1 registro por OP (suma tela)

PASO 6: CONSOLIDA Y CALCULA FACTORES
  ├─> Cálculo de factor_hilados (mensual):
  │   factor_h = target_hilados / SUM(inductor_hilados_original por mes)
  │
  │   Aplica a cada OP:
  │   costo_hilados_final = inductor_hilados_original * factor_h
  │
  └─> Factor NO se distribuye a nivel de hilo

PASO 7: INSERT en costo_materia_prima
  └─> 1 registro por OP con:
      - costo_hilados_final (total ajustado)
      - costo_tela_final (total ajustado)
      - costo_total_mp_final
```

**PROBLEMA POTENCIAL**: El factor se aplica al costo TOTAL de la OP, no se sabe cómo se distribuye entre hilos.

---

## 3. FLUJO DE CÁLCULO - VERSIÓN V3

```
PASO 1-2: Mismo que original
  └─> ops_base, fechas_wip

PASO 3: REQUERIMIENTOS HILADOS (DESGLOSADO)
  └─> requerimientos_hilados
      └─> 1 registro POR HILO (no se agregan)
          - cod_ordpro
          - tipo_hilo (CRUDO/TENIDO)
          - cod_hiltel, cod_hilado
          - kg_requeridos
          - descripcion

PASO 4: MEJOR COSTO POR HILADO (individual)
  └─> mejor_costo_por_hilado
      └─> Busca mejor precio histórico para CADA HILO
          └─> Resultado:
              - cod_ordpro
              - cod_hilado
              - kg_requeridos
              - usd_por_kg (precio por kg de ESTE hilo)
              - fecha_precio

PASO 6: CONSOLIDA DETALLE FINAL (POR HILO)
  └─> detalle_final
      ├─> cod_ordpro
      ├─> cod_hilado
      ├─> kg_requeridos
      ├─> prendas_requeridas
      ├─> kg_por_prenda = kg_requeridos / prendas_requeridas
      ├─> usd_por_kg (precio unitario del hilo)
      ├─> costo_total = kg_requeridos * usd_por_kg
      └─> costo_por_prenda = costo_total / prendas_requeridas

PASO 7: APLICAR FACTORES DE AJUSTE
  ├─> targets_hilados: mes/año → target_monto (bolsa de costos)
  │
  ├─> factores_mes: CALCULA FACTOR POR MES
  │   ├─> Agrupa detalle_final por fecha_despacho_formato
  │   ├─> Sum(costo_total) por mes = suma de TODOS los hilos de TODOS OPs en ese mes
  │   └─> factor_mes = target_monto / NULLIF(Sum(costo_total), 0)
  │       └─> ESTO ES CORRECTO: distribuyendo la bolsa entre todos los hilos del mes
  │
  ├─> detalle_unico: ELIMINA DUPLICADOS
  │   └─> DISTINCT ON (cod_ordpro, cod_hiltel, tipo_hilo)
  │       └─> Mantiene el más reciente (fecha_precio DESC)
  │
  └─> INSERT FINAL en costo_hilados_detalle_op
      ├─> Por cada hilo única (sin duplicados):
      ├─> usd_por_kg_final = usd_por_kg_original * factor_aplicado
      ├─> costo_total_final = costo_total_original * factor_aplicado
      └─> costo_por_prenda_final = costo_por_prenda_original * factor_aplicado
```

---

## 4. VALIDACIÓN DE LA DISTRIBUCIÓN DE COSTOS EN V3

### ¿Cómo se distribuye la bolsa de costos?

**Fórmula en V3**:
```
factor_mes = target_monto / NULLIF(SUM(costo_total), 0)

Donde:
  target_monto = Bolsa de costos presupuestada del mes
  SUM(costo_total) = Suma de costos originales de TODOS los hilos del mes
```

### Flujo de distribución:

1. **Se calcula factor_mes por mes completo**
   ```
   Mes: ENE-25
   Bolsa presupuestada: $10,000
   Costos reales de todos hilos mes ENE: $8,000
   Factor: 10,000 / 8,000 = 1.25
   ```

2. **Se aplica el factor a CADA hilo individualmente**
   ```
   Para OP-001 con 3 hilos:

   Hilo A (rojo):
     costo_original = 500 USD
     costo_final = 500 * 1.25 = 625 USD

   Hilo B (azul):
     costo_original = 300 USD
     costo_final = 300 * 1.25 = 375 USD

   Hilo C (verde):
     costo_original = 200 USD
     costo_final = 200 * 1.25 = 250 USD

   Total OP-001: 625 + 375 + 250 = 1,250 USD (proporcional)
   ```

3. **Verificación de integridad**
   ```
   Suma original mes ENE: 8,000 USD
   Suma final mes ENE: 8,000 * 1.25 = 10,000 USD ✓
   (Coincide con bolsa presupuestada)
   ```

### ✅ DISTRIBUCIÓN CORRECTA

**Características positivas de V3**:

1. ✓ **Factor uniforme por mes**: Todos los hilos del mismo mes usan el mismo factor
2. ✓ **Distribución proporcional**: Cada hilo se ajusta proporcionalmente a su costo original
3. ✓ **Trazabilidad**: Se puede ver exactamente qué factor se aplicó a cada hilo
4. ✓ **Deduplicación correcta**: DISTINCT ON elimina duplicados ANTES de aplicar factor
5. ✓ **Suma garantizada**:
   - Suma(costo_original) * factor = Suma(costo_final) = target_monto

---

## 5. ANÁLISIS DE CASOS CRÍTICOS

### Caso 1: OP con múltiples hilos iguales
```
OP-001 requiere:
  - 5 kg de Hilo Rojo (código H-001)
  - 3 kg de Hilo Rojo (código H-001) [Duplicado]
  - 2 kg de Hilo Azul (código H-002)

Tabla requerimientos_hilados muestra:
  Registro 1: OP-001, H-001, 5 kg
  Registro 2: OP-001, H-001, 3 kg  ← DUPLICADO

Tabla mejor_costo_por_hilado:
  Obtiene precio para cada uno independientemente
  Resultado: ambos con mismo precio (busca el mismo hilo H-001)

Tabla detalle_final:
  Registro 1: OP-001, H-001, 5 kg, costo = 250
  Registro 2: OP-001, H-001, 3 kg, costo = 150  ← PROBLEMA

Tabla detalle_unico (DISTINCT ON):
  ├─ DISTINCT ON (cod_ordpro, cod_hiltel, tipo_hilo)
  ├─ ORDER BY ... fecha_precio DESC
  └─ Resultado: Mantiene UNO de los dos (el más reciente)
     PIERDE 3kg de costo (150 USD)
```

⚠️ **ALERTA**: Si hay duplicados legítimos en requerimientos_hilados,
V3 los agrupa incorrectamente y pierde datos.

---

### Caso 2: Hilo sin precio histórico
```
Requerimiento: OP-001 necesita 5 kg de Hilo H-999

mejor_costo_por_hilado busca:
  SELECT ... FROM hi_movistk_ordpro_item
  WHERE cod_hilado = 'H-999'

Si NO encuentra precio:
  No entra en la tabla mejor_costo_por_hilado

Resultado en detalle_final:
  Hilo H-999 NO aparece (se pierde del cálculo)

Efecto:
  El hilo existe en requerimientos pero no en costos
  Se calcula costo_total = 0 o no existe el registro
```

⚠️ **ALERTA**: Hilos sin precio histórico desaparecen de los cálculos.

---

### Caso 3: Mes sin target presupuestado
```
OP-001 con fecha_despacho = "Mar-25"
targets_hilados NO tiene entrada para "Mar-25"

En tabla factores_mes (línea 844-851):
  LEFT JOIN targets_hilados th ON ...
  WHERE th.target_monto IS NOT NULL

Si "Mar-25" no está en targets:
  factores_mes NO tiene entrada para "Mar-25"

En INSERT final (línea 887):
  COALESCE(fm.factor_mes, 1.0)

Resultado:
  factor_aplicado = 1.0 (sin ajuste)
  costo_final = costo_original (sin cambio)
```

✓ **CORRECTO**: Degradación elegante (mantiene costo original)
⚠️ **PERO**: Si todo debe tener target, esto es un error silencioso

---

## 6. CÁLCULO CORRECTO DE DISTRIBUCIÓN

Para que la distribución sea completamente correcta:

1. **Debe haber deduplicación en requerimientos_hilados**
   ```sql
   -- ANTES de calcular costos:
   -- Agrupar: SUM(kg_requeridos) por (cod_ordpro, cod_hiltel, tipo_hilo)
   ```

2. **Los hilos sin precio deben manejarse explícitamente**
   ```sql
   -- No desaparecer silenciosamente
   -- Generar log o usar precio por defecto
   ```

3. **Los targets incompletos deben validarse**
   ```sql
   -- Verificar que TODOS los meses tienen targets
   -- O documentar cuál es el comportamiento esperado
   ```

---

## 7. CONSULTAS DE VALIDACIÓN

### Validación 1: Verificar que suma de costos finales = bolsa de costos

```sql
SELECT
    fecha_despacho,
    COUNT(*) as hilos_totales,
    SUM(costo_total_original) as suma_original,
    ROUND(AVG(factor_aplicado), 6) as factor_mes,
    SUM(costo_total_final) as suma_final,
    (SELECT materia_prima FROM silver.costos_mp_ct_avios ct
     WHERE CONCAT(
         CASE ct.mes WHEN 1 THEN 'Ene' WHEN 2 THEN 'Feb' WHEN 3 THEN 'Mar'
         WHEN 4 THEN 'Abr' WHEN 5 THEN 'May' WHEN 6 THEN 'Jun' WHEN 7 THEN 'Jul'
         WHEN 8 THEN 'Ago' WHEN 9 THEN 'Sep' WHEN 10 THEN 'Oct'
         WHEN 11 THEN 'Nov' WHEN 12 THEN 'Dic' END, '-', RIGHT(ct.año::TEXT, 2)
     ) = fecha_despacho
    ) as bolsa_target,
    SUM(costo_total_final) -
    (SELECT materia_prima FROM silver.costos_mp_ct_avios ct
     WHERE CONCAT(
         CASE ct.mes WHEN 1 THEN 'Ene' WHEN 2 THEN 'Feb' WHEN 3 THEN 'Mar'
         WHEN 4 THEN 'Abr' WHEN 5 THEN 'May' WHEN 6 THEN 'Jun' WHEN 7 THEN 'Jul'
         WHEN 8 THEN 'Ago' WHEN 9 THEN 'Sep' WHEN 10 THEN 'Oct'
         WHEN 11 THEN 'Nov' WHEN 12 THEN 'Dic' END, '-', RIGHT(ct.año::TEXT, 2)
     ) as diferencia
FROM silver.costo_hilados_detalle_op
GROUP BY fecha_despacho
ORDER BY fecha_despacho;
```

### Validación 2: Detectar duplicados en requerimientos

```sql
SELECT
    cod_ordpro,
    cod_hiltel,
    tipo_hilo,
    COUNT(*) as veces_que_aparece,
    SUM(kg_requeridos) as kg_total
FROM silver.costo_hilados_detalle_op
GROUP BY cod_ordpro, cod_hiltel, tipo_hilo
HAVING COUNT(*) > 1;
```

### Validación 3: Detectar hilos sin precio

```sql
SELECT
    rh.cod_ordpro,
    rh.cod_hiltel,
    rh.cod_hilado,
    rh.kg_requeridos,
    rh.tipo_hilo
FROM
    (SELECT DISTINCT cod_ordpro, cod_hiltel, cod_hilado, kg_requeridos, tipo_hilo
     FROM silver.costo_hilados_detalle_op) df

RIGHT JOIN bronze.es_ordproreq_hilcru_detalle rh
    ON df.cod_ordpro = rh.cod_ordpro
    AND df.cod_hiltel = rh.cod_hiltel

WHERE df.cod_ordpro IS NULL;
```

---

## 8. RECOMENDACIONES

### ✅ V3 es matemáticamente correcta EN CUANTO A DISTRIBUCIÓN PROPORCIONAL

La fórmula `factor = bolsa / suma_costos_reales` es correcta.

### ⚠️ Pero tiene vulnerabilidades en MANEJO DE EXCEPCIONES:

1. **Duplicados legítimos**: DISTINCT ON puede perder datos
2. **Hilos sin precio**: Desaparecen silenciosamente
3. **Targets incompletos**: Se usan factores por defecto sin validar

### 🔧 Mejoras sugeridas:

```sql
-- 1. Agrupar primero los requerimientos (suma kg por hilo/OP)
DROP TABLE IF EXISTS requerimientos_agrupados;
CREATE TEMP TABLE requerimientos_agrupados AS
SELECT
    cod_ordpro,
    tipo_hilo,
    cod_hiltel,
    cod_hilado,
    SUM(kg_requeridos) as kg_requeridos_total  -- SUMA si hay duplicados
FROM requerimientos_hilados
GROUP BY cod_ordpro, tipo_hilo, cod_hiltel, cod_hilado;

-- 2. Validar targets
DROP TABLE IF EXISTS targets_validados;
CREATE TEMP TABLE targets_validados AS
SELECT *
FROM targets_hilados
WHERE target_monto > 0;

-- Verificar que no hay meses sin targets
SELECT COUNT(*) as meses_sin_targets
FROM (
    SELECT DISTINCT fecha_despacho_formato FROM detalle_final
    EXCEPT
    SELECT mes_año FROM targets_validados
);
```

---

## CONCLUSIÓN

**populate_costo_materia_prima_v3 DISTRIBUYE CORRECTAMENTE la bolsa de costos**

cuando:
- ✓ No hay duplicados legítimos en requerimientos
- ✓ Todos los hilos tienen precio histórico
- ✓ Todos los meses tienen targets presupuestados

**Fórmula validada**:
```
Suma(costo_final) = Suma(costo_original) * factor = bolsa_mes
```

**Proporcionalidad validada**:
```
Cada hilo se ajusta al mismo factor que los demás del mes
Mantiene relaciones de proporción relativa
```

**Recomendación**: Ejecutar las consultas de validación antes de usar en producción.
