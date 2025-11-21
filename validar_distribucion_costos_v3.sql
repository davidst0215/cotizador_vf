-- ============================================================================
-- SCRIPT DE VALIDACIÓN: Distribución de costos en populate_costo_materia_prima_v3
-- ============================================================================
-- Este script verifica que la bolsa de costos se distribuya correctamente
-- entre los hilos de cada OP en cada mes
-- ============================================================================

-- ============================================================================
-- VALIDACIÓN 1: Resumen de distribución por mes
-- ============================================================================
-- Verifica que suma(costo_final) = bolsa_target para cada mes

SELECT
    'VALIDACIÓN 1: DISTRIBUCIÓN POR MES' as validacion,
    fecha_despacho,
    COUNT(*) as hilos_totales,
    COUNT(DISTINCT op_codigo) as ops_totales,
    ROUND(SUM(costo_total_original), 2) as suma_original,
    ROUND(AVG(factor_aplicado), 6) as factor_mes,
    ROUND(SUM(costo_total_final), 2) as suma_final,
    (SELECT ROUND(materia_prima, 2) FROM silver.costos_mp_ct_avios ct
     WHERE
        CONCAT(
            CASE ct.mes
                WHEN 1 THEN 'Ene' WHEN 2 THEN 'Feb' WHEN 3 THEN 'Mar' WHEN 4 THEN 'Abr'
                WHEN 5 THEN 'May' WHEN 6 THEN 'Jun' WHEN 7 THEN 'Jul' WHEN 8 THEN 'Ago'
                WHEN 9 THEN 'Sep' WHEN 10 THEN 'Oct' WHEN 11 THEN 'Nov' WHEN 12 THEN 'Dic'
            END, '-', RIGHT(ct.año::TEXT, 2)
        ) = fecha_despacho
    ) as bolsa_target,
    ROUND(
        SUM(costo_total_final) -
        (SELECT materia_prima FROM silver.costos_mp_ct_avios ct
         WHERE
            CONCAT(
                CASE ct.mes
                    WHEN 1 THEN 'Ene' WHEN 2 THEN 'Feb' WHEN 3 THEN 'Mar' WHEN 4 THEN 'Abr'
                    WHEN 5 THEN 'May' WHEN 6 THEN 'Jun' WHEN 7 THEN 'Jul' WHEN 8 THEN 'Ago'
                    WHEN 9 THEN 'Sep' WHEN 10 THEN 'Oct' WHEN 11 THEN 'Nov' WHEN 12 THEN 'Dic'
                END, '-', RIGHT(ct.año::TEXT, 2)
            ) = fecha_despacho
        ),
        2
    ) as diferencia_respecto_target,
    CASE
        WHEN ABS(SUM(costo_total_final) -
            (SELECT materia_prima FROM silver.costos_mp_ct_avios ct
             WHERE
                CONCAT(
                    CASE ct.mes
                        WHEN 1 THEN 'Ene' WHEN 2 THEN 'Feb' WHEN 3 THEN 'Mar' WHEN 4 THEN 'Abr'
                        WHEN 5 THEN 'May' WHEN 6 THEN 'Jun' WHEN 7 THEN 'Jul' WHEN 8 THEN 'Ago'
                        WHEN 9 THEN 'Sep' WHEN 10 THEN 'Oct' WHEN 11 THEN 'Nov' WHEN 12 THEN 'Dic'
                    END, '-', RIGHT(ct.año::TEXT, 2)
                ) = fecha_despacho
            )) < 0.01 THEN 'OK ✓'
        ELSE 'ERROR ⚠️'
    END as estado
FROM silver.costo_hilados_detalle_op
GROUP BY fecha_despacho
ORDER BY fecha_despacho DESC;


-- ============================================================================
-- VALIDACIÓN 2: Detalles por OP - Ejemplo de una OP
-- ============================================================================
-- Muestra cómo se distribuye el costo de una OP entre sus hilos

SELECT
    'VALIDACIÓN 2: DETALLES POR OP (Ejemplo)' as validacion,
    op_codigo,
    cod_hilado,
    tipo_hilo,
    kg_requeridos,
    prendas_requeridas,
    ROUND(kg_por_prenda, 4) as kg_por_prenda,
    ROUND(usd_por_kg_original, 4) as usd_kg_original,
    ROUND(costo_total_original, 2) as costo_original,
    ROUND(costo_por_prenda_original, 4) as costo_por_prenda_orig,
    ROUND(factor_aplicado, 6) as factor,
    ROUND(usd_por_kg_final, 4) as usd_kg_final,
    ROUND(costo_total_final, 2) as costo_final,
    ROUND(costo_por_prenda_final, 4) as costo_por_prenda_final,
    fecha_despacho
FROM silver.costo_hilados_detalle_op
WHERE op_codigo = (
    -- Obtener la primera OP con más hilos para ver la distribución
    SELECT op_codigo FROM silver.costo_hilados_detalle_op
    GROUP BY op_codigo
    ORDER BY COUNT(*) DESC
    LIMIT 1
)
ORDER BY tipo_hilo, cod_hilado;

-- Resumen de la OP seleccionada
SELECT
    'RESUMEN OP' as tipo,
    SUM(costo_total_original)::NUMERIC(18,2) as costo_original_total,
    SUM(costo_total_final)::NUMERIC(18,2) as costo_final_total,
    (SUM(costo_total_final) / NULLIF(SUM(costo_total_original), 0))::NUMERIC(18,6) as factor_calculado,
    (SELECT ROUND(AVG(factor_aplicado), 6)
     FROM silver.costo_hilados_detalle_op t2
     WHERE t2.op_codigo = t1.op_codigo LIMIT 1) as factor_registrado
FROM silver.costo_hilados_detalle_op t1
WHERE op_codigo = (
    SELECT op_codigo FROM silver.costo_hilados_detalle_op
    GROUP BY op_codigo
    ORDER BY COUNT(*) DESC
    LIMIT 1
)
GROUP BY 1;


-- ============================================================================
-- VALIDACIÓN 3: Detectar posibles duplicados
-- ============================================================================
-- Un hilo no debería aparecer 2 veces para el mismo OP/tipo_hilo/fecha

SELECT
    'VALIDACIÓN 3: DUPLICADOS' as validacion,
    op_codigo,
    cod_hiltel,
    tipo_hilo,
    COUNT(*) as veces_aparece,
    SUM(kg_requeridos) as kg_total
FROM silver.costo_hilados_detalle_op
GROUP BY op_codigo, cod_hiltel, tipo_hilo
HAVING COUNT(*) > 1
ORDER BY op_codigo, cod_hiltel;

SELECT
    CASE WHEN COUNT(*) = 0 THEN '✓ No hay duplicados'
         ELSE '⚠️ Se encontraron ' || COUNT(*) || ' hilos duplicados'
    END as resultado_duplicados
FROM (
    SELECT op_codigo, cod_hiltel, tipo_hilo
    FROM silver.costo_hilados_detalle_op
    GROUP BY op_codigo, cod_hiltel, tipo_hilo
    HAVING COUNT(*) > 1
) t;


-- ============================================================================
-- VALIDACIÓN 4: Verificar integridad de costo por prenda
-- ============================================================================
-- Verifica que costo_por_prenda = costo_total / prendas_requeridas

SELECT
    'VALIDACIÓN 4: INTEGRIDAD COSTO POR PRENDA' as validacion,
    COUNT(*) as total_registros,
    COUNT(CASE
        WHEN ABS(costo_por_prenda_final - (costo_total_final / prendas_requeridas)) < 0.01
        THEN 1
    END) as registros_correctos,
    COUNT(CASE
        WHEN ABS(costo_por_prenda_final - (costo_total_final / prendas_requeridas)) >= 0.01
        THEN 1
    END) as registros_con_error,
    CASE WHEN COUNT(CASE
        WHEN ABS(costo_por_prenda_final - (costo_total_final / prendas_requeridas)) >= 0.01
        THEN 1
    END) = 0 THEN '✓ OK'
    ELSE '⚠️ ERROR'
    END as estado
FROM silver.costo_hilados_detalle_op
WHERE prendas_requeridas > 0;


-- ============================================================================
-- VALIDACIÓN 5: Verificar kg_por_prenda
-- ============================================================================
-- Verifica que kg_por_prenda = kg_requeridos / prendas_requeridas

SELECT
    'VALIDACIÓN 5: INTEGRIDAD KG POR PRENDA' as validacion,
    COUNT(*) as total_registros,
    COUNT(CASE
        WHEN ABS(kg_por_prenda - (kg_requeridos / prendas_requeridas)) < 0.000001
        THEN 1
    END) as registros_correctos,
    COUNT(CASE
        WHEN ABS(kg_por_prenda - (kg_requeridos / prendas_requeridas)) >= 0.000001
        THEN 1
    END) as registros_con_error,
    CASE WHEN COUNT(CASE
        WHEN ABS(kg_por_prenda - (kg_requeridos / prendas_requeridas)) >= 0.000001
        THEN 1
    END) = 0 THEN '✓ OK'
    ELSE '⚠️ ERROR'
    END as estado
FROM silver.costo_hilados_detalle_op
WHERE prendas_requeridas > 0;


-- ============================================================================
-- VALIDACIÓN 6: Verificar que todos los meses tienen targets
-- ============================================================================
-- Detecta meses sin presupuesto asignado

SELECT
    'VALIDACIÓN 6: COBERTURA DE TARGETS' as validacion,
    COUNT(DISTINCT cd.fecha_despacho) as meses_con_datos,
    COUNT(DISTINCT ct.mes) as meses_con_targets,
    COUNT(DISTINCT CASE
        WHEN EXISTS (
            SELECT 1 FROM silver.costos_mp_ct_avios ct2
            WHERE CONCAT(
                CASE ct2.mes WHEN 1 THEN 'Ene' WHEN 2 THEN 'Feb' WHEN 3 THEN 'Mar' WHEN 4 THEN 'Abr'
                WHEN 5 THEN 'May' WHEN 6 THEN 'Jun' WHEN 7 THEN 'Jul' WHEN 8 THEN 'Ago'
                WHEN 9 THEN 'Sep' WHEN 10 THEN 'Oct' WHEN 11 THEN 'Nov' WHEN 12 THEN 'Dic'
                END, '-', RIGHT(ct2.año::TEXT, 2)
            ) = cd.fecha_despacho
        ) THEN cd.fecha_despacho
    END) as meses_con_ambos
FROM silver.costo_hilados_detalle_op cd
CROSS JOIN silver.costos_mp_ct_avios ct;

SELECT
    fecha_despacho,
    'SIN TARGET PRESUPUESTADO ⚠️' as estado
FROM (
    SELECT DISTINCT fecha_despacho FROM silver.costo_hilados_detalle_op cd
) meses_datos
WHERE NOT EXISTS (
    SELECT 1 FROM silver.costos_mp_ct_avios ct
    WHERE CONCAT(
        CASE ct.mes WHEN 1 THEN 'Ene' WHEN 2 THEN 'Feb' WHEN 3 THEN 'Mar' WHEN 4 THEN 'Abr'
        WHEN 5 THEN 'May' WHEN 6 THEN 'Jun' WHEN 7 THEN 'Jul' WHEN 8 THEN 'Ago'
        WHEN 9 THEN 'Sep' WHEN 10 THEN 'Oct' WHEN 11 THEN 'Nov' WHEN 12 THEN 'Dic'
        END, '-', RIGHT(ct.año::TEXT, 2)
    ) = fecha_despacho
)
ORDER BY fecha_despacho;


-- ============================================================================
-- VALIDACIÓN 7: Factores aplicados por mes
-- ============================================================================
-- Verifica que dentro de un mes, todos los hilos usen el mismo factor

SELECT
    'VALIDACIÓN 7: UNIFORMIDAD DE FACTORES' as validacion,
    fecha_despacho,
    COUNT(DISTINCT factor_aplicado) as factores_diferentes,
    MIN(factor_aplicado)::NUMERIC(18,6) as factor_minimo,
    MAX(factor_aplicado)::NUMERIC(18,6) as factor_maximo,
    AVG(factor_aplicado)::NUMERIC(18,6) as factor_promedio,
    CASE
        WHEN COUNT(DISTINCT factor_aplicado) = 1 THEN '✓ Uniforme'
        ELSE '⚠️ Múltiples factores'
    END as estado
FROM silver.costo_hilados_detalle_op
WHERE factor_aplicado > 0
GROUP BY fecha_despacho
ORDER BY fecha_despacho;


-- ============================================================================
-- VALIDACIÓN 8: Análisis de proporcionalidad
-- ============================================================================
-- Verifica que cada hilo mantenga su proporción relativa después del ajuste

WITH proporciones AS (
    SELECT
        op_codigo,
        fecha_despacho,
        cod_hiltel,
        tipo_hilo,
        costo_total_original / NULLIF(SUM(costo_total_original) OVER (PARTITION BY op_codigo), 0) as prop_original,
        costo_total_final / NULLIF(SUM(costo_total_final) OVER (PARTITION BY op_codigo), 0) as prop_final
    FROM silver.costo_hilados_detalle_op
)
SELECT
    'VALIDACIÓN 8: PROPORCIONALIDAD' as validacion,
    COUNT(*) as total_comparaciones,
    COUNT(CASE
        WHEN ABS(prop_original - prop_final) < 0.0001 THEN 1
    END) as proporciones_iguales,
    ROUND(AVG(ABS(prop_original - prop_final)), 6)::NUMERIC(18,6) as diferencia_promedio,
    MAX(ABS(prop_original - prop_final))::NUMERIC(18,6) as diferencia_maxima,
    CASE WHEN AVG(ABS(prop_original - prop_final)) < 0.0001 THEN '✓ Proporciones conservadas'
         ELSE '⚠️ Proporciones alteradas'
    END as resultado
FROM proporciones;


-- ============================================================================
-- RESUMEN FINAL
-- ============================================================================

SELECT '' as linea_separadora;
SELECT '════════════════════════════════════════════════════════════' as titulo;
SELECT 'RESUMEN FINAL DE VALIDACIÓN' as titulo;
SELECT '════════════════════════════════════════════════════════════' as titulo;

SELECT
    COUNT(*) as total_hilos,
    COUNT(DISTINCT op_codigo) as total_ops,
    COUNT(DISTINCT fecha_despacho) as total_meses,
    ROUND(SUM(costo_total_final), 2) as costo_total_distribuido,
    ROUND(AVG(factor_aplicado), 6) as factor_promedio,
    MIN(fecha_corrida) as primera_corrida,
    MAX(fecha_corrida) as ultima_corrida
FROM silver.costo_hilados_detalle_op;

SELECT '' as linea_fin;
SELECT '✓ Todas las validaciones completadas' as mensaje_final;
