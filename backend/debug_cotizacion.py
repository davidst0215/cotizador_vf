#!/usr/bin/env python3
"""
Script de debug paso a paso para cotización
Marca: MONTAIGNE HONG KONG LIMITED
Estilo: 123
Tipo Prenda: T-SHIRT
Categoría Lote: Lote Mediano (501-1000 prendas)
"""

import psycopg2
from psycopg2.extras import DictCursor
from decimal import Decimal
import json
from datetime import datetime

# ============================================================================
# CONFIGURACIÓN DE CONEXIÓN
# ============================================================================

DB_CONFIG = {
    "dbname": "tdv",
    "user": "david",
    "host": "18.118.59.50",
    "port": 5432,
    "sslmode": "verify-ca",
    "sslcert": r"C:\Users\siste\OneDrive\SAYA INVESTMENTS\calidad de venta\audios\piloto_abril\david (1).crt",
    "sslkey": r"C:\Users\siste\OneDrive\SAYA INVESTMENTS\calidad de venta\audios\piloto_abril\david.pk8",
    "sslrootcert": r"C:\Users\siste\OneDrive\SAYA INVESTMENTS\calidad de venta\audios\piloto_abril\root.crt"
}

# Parámetros de entrada
MARCA = "MONTAIGNE HONG KONG LIMITED"
ESTILO = 123
TIPO_PRENDA = "T-SHIRT"
VERSION_CALCULO = "FLUIDO"
CANTIDAD_PRENDAS = 750  # Lote Mediano

# ============================================================================
# UTILIDADES
# ============================================================================

def print_section(title):
    """Imprime un título de sección"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_subsection(title):
    """Imprime un subtítulo"""
    print(f"\n{title}")
    print("-" * 80)

def print_query(sql):
    """Imprime la query ejecutada"""
    print(f"\n[SQL QUERY]:\n{sql}\n")

def print_result(label, value, details=None):
    """Imprime un resultado"""
    if isinstance(value, list):
        print(f"\n{label}: {len(value)} registros encontrados")
        if value and len(value) > 0:
            print(f"Primeros 3 registros:")
            for i, row in enumerate(value[:3]):
                print(f"  {i+1}. {dict(row)}")
        if details:
            print(f"\nDetalles: {details}")
    else:
        print(f"\n{label}: {value}")
        if details:
            print(f"Detalles: {details}")

def connect_db():
    """Conecta a la base de datos"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"ERROR DE CONEXIÓN: {e}")
        exit(1)

# ============================================================================
# PASO 1: VERIFICACIÓN DE ESTILO
# ============================================================================

def paso_1_verificar_estilo(conn):
    """Verifica si el estilo existe en historial_estilos"""
    print_section("PASO 1: VERIFICACIÓN DE ESTILO")

    cursor = conn.cursor(cursor_factory=DictCursor)

    # Query 1: Buscar estilo sin filtro de volumen
    sql = f"""
    SELECT
      codigo_estilo,
      prendas_totales,
      CASE
        WHEN prendas_totales > 4000 THEN 'Muy Recurrente'
        WHEN prendas_totales > 0 THEN 'Recurrente'
        ELSE 'Nuevo'
      END as categoria_estilo
    FROM historial_estilos
    WHERE codigo_estilo = {ESTILO}
    LIMIT 1;
    """
    print_query(sql)
    cursor.execute(sql)
    resultado_sin_filtro = cursor.fetchone()

    if resultado_sin_filtro:
        print(f"[OK] Estilo {ESTILO} ENCONTRADO (sin filtro volumen)")
        print(f"  - Prendas Totales: {resultado_sin_filtro['prendas_totales']}")
        print(f"  - Categoría: {resultado_sin_filtro['categoria_estilo']}")
    else:
        print(f"[ERROR] Estilo {ESTILO} NO ENCONTRADO")
        return None

    # Query 2: Buscar estilo CON filtro >= 200
    print_subsection("Aplicando filtro >= 200 prendas")
    sql_con_filtro = f"""
    SELECT
      codigo_estilo,
      prendas_totales,
      CASE
        WHEN prendas_totales > 4000 THEN 'Muy Recurrente'
        WHEN prendas_totales > 0 THEN 'Recurrente'
        ELSE 'Nuevo'
      END as categoria_estilo
    FROM historial_estilos
    WHERE codigo_estilo = {ESTILO}
      AND prendas_totales >= 200
    LIMIT 1;
    """
    print_query(sql_con_filtro)
    cursor.execute(sql_con_filtro)
    resultado_con_filtro = cursor.fetchone()

    if resultado_con_filtro:
        print(f"[OK] Estilo {ESTILO} PASA FILTRO >= 200 prendas")
        print(f"  - Prendas Totales: {resultado_con_filtro['prendas_totales']}")
        print(f"  - Categoría: {resultado_con_filtro['categoria_estilo']}")
        estado_estilo = "RECURRENTE"
    else:
        print(f"[ERROR] Estilo {ESTILO} NO PASA FILTRO >= 200 prendas")
        print(f"  [>] Se tratará como estilo NUEVO")
        estado_estilo = "NUEVO"

    cursor.close()
    return estado_estilo

# ============================================================================
# PASO 2: COSTOS DIRECTOS (costo_op_detalle)
# ============================================================================

def paso_2_costos_directos(conn, estado_estilo):
    """Obtiene costos directos del estilo"""
    print_section("PASO 2: COSTOS DIRECTOS (costo_op_detalle)")

    cursor = conn.cursor(cursor_factory=DictCursor)

    print_subsection("Query SIN filtros")
    sql_sin_filtro = f"""
    SELECT
      cod_ordpro,
      codigo_estilo,
      tipo_de_producto,
      prendas_requeridas,
      costo_textil,
      costo_manufactura,
      costo_materia_prima,
      costo_avios,
      version_calculo
    FROM silver.costo_op_detalle
    WHERE codigo_estilo = {ESTILO}
      AND tipo_de_producto = '{TIPO_PRENDA}'
      AND version_calculo = '{VERSION_CALCULO}'
    ORDER BY cod_ordpro
    LIMIT 20;
    """
    print_query(sql_sin_filtro)
    cursor.execute(sql_sin_filtro)
    resultados_sin_filtro = cursor.fetchall()

    print(f"Total registros sin filtro: {len(resultados_sin_filtro)}")
    if resultados_sin_filtro:
        print("\nPrimeros 3 registros:")
        for i, row in enumerate(resultados_sin_filtro[:3]):
            print(f"\n  OP #{i+1}: {row['cod_ordpro']}")
            print(f"    - Prendas: {row['prendas_requeridas']}")
            print(f"    - Textil: ${row['costo_textil']}")
            print(f"    - Manufactura: ${row['costo_manufactura']}")
            print(f"    - Materia Prima: ${row['costo_materia_prima']}")
            print(f"    - Avíos: ${row['costo_avios']}")

    # Query CON filtros
    print_subsection(f"Query CON filtros (>= 200 prendas, marca={MARCA})")
    sql_con_filtro = f"""
    SELECT
      cod_ordpro,
      codigo_estilo,
      tipo_de_producto,
      prendas_requeridas,
      costo_textil,
      costo_manufactura,
      costo_materia_prima,
      costo_avios,
      version_calculo
    FROM silver.costo_op_detalle
    WHERE codigo_estilo = {ESTILO}
      AND tipo_de_producto = '{TIPO_PRENDA}'
      AND version_calculo = '{VERSION_CALCULO}'
      AND prendas_requeridas >= 200
      AND cliente = '{MARCA}'
    ORDER BY cod_ordpro
    LIMIT 20;
    """
    print_query(sql_con_filtro)
    cursor.execute(sql_con_filtro)
    resultados_con_filtro = cursor.fetchall()

    print(f"Total registros CON filtro: {len(resultados_con_filtro)}")

    if len(resultados_sin_filtro) > len(resultados_con_filtro):
        ops_excluidas = len(resultados_sin_filtro) - len(resultados_con_filtro)
        print(f"⚠️  {ops_excluidas} OPs EXCLUIDAS por filtro >= 200 prendas")

    if resultados_con_filtro:
        print("\nPrimeros 3 registros filtrados:")
        for i, row in enumerate(resultados_con_filtro[:3]):
            print(f"\n  OP #{i+1}: {row['cod_ordpro']}")
            print(f"    - Prendas: {row['prendas_requeridas']}")
            print(f"    - Textil: ${row['costo_textil']}")
            print(f"    - Manufactura: ${row['costo_manufactura']}")
            print(f"    - Materia Prima: ${row['costo_materia_prima']}")
            print(f"    - Avíos: ${row['costo_avios']}")

        # Promedios
        print_subsection("Cálculo de promedios (después de filtro)")
        sql_promedios = f"""
        SELECT
          AVG(CAST(costo_textil AS FLOAT) / NULLIF(prendas_requeridas, 0)) as costo_textil_unitario,
          AVG(CAST(costo_manufactura AS FLOAT) / NULLIF(prendas_requeridas, 0)) as costo_manufactura_unitario,
          AVG(CAST(costo_materia_prima AS FLOAT) / NULLIF(prendas_requeridas, 0)) as costo_materia_prima_unitario,
          AVG(CAST(costo_avios AS FLOAT) / NULLIF(prendas_requeridas, 0)) as costo_avios_unitario,
          COUNT(*) as cantidad_ops_promediadas
        FROM silver.costo_op_detalle
        WHERE codigo_estilo = {ESTILO}
          AND tipo_de_producto = '{TIPO_PRENDA}'
          AND version_calculo = '{VERSION_CALCULO}'
          AND prendas_requeridas >= 200
          AND cliente = '{MARCA}';
        """
        print_query(sql_promedios)
        cursor.execute(sql_promedios)
        promedios = cursor.fetchone()

        if promedios:
            print(f"\nCostos Unitarios Promediados:")
            print(f"  - Textil: ${promedios['costo_textil_unitario']:.4f}")
            print(f"  - Manufactura: ${promedios['costo_manufactura_unitario']:.4f}")
            print(f"  - Materia Prima: ${promedios['costo_materia_prima_unitario']:.4f}")
            print(f"  - Avíos: ${promedios['costo_avios_unitario']:.4f}")
            print(f"  - OPs Promediadas: {promedios['cantidad_ops_promediadas']}")

            costo_directo_total = (
                promedios['costo_textil_unitario'] +
                promedios['costo_manufactura_unitario'] +
                promedios['costo_materia_prima_unitario'] +
                promedios['costo_avios_unitario']
            )
            print(f"\n  → COSTO DIRECTO TOTAL: ${costo_directo_total:.4f}")

            return {
                'costo_textil': promedios['costo_textil_unitario'],
                'costo_manufactura': promedios['costo_manufactura_unitario'],
                'costo_materia_prima': promedios['costo_materia_prima_unitario'],
                'costo_avios': promedios['costo_avios_unitario'],
                'total': costo_directo_total,
                'ops_utilizadas': promedios['cantidad_ops_promediadas']
            }
    else:
        print("✗ NO hay OPs que cumplan todos los filtros")
        return None

    cursor.close()

# ============================================================================
# PASO 3: COSTOS DE WIPs
# ============================================================================

def paso_3_costos_wips(conn):
    """Obtiene costos de WIPs"""
    print_section("PASO 3: COSTOS DE WIPs (resumen_wip_por_prenda)")

    cursor = conn.cursor(cursor_factory=DictCursor)

    # Query SIN filtros
    print_subsection("Query SIN filtros")
    sql_sin_filtro = f"""
    SELECT
      wip_id,
      tipo_de_producto,
      total_prendas,
      costo_por_prenda,
      marca,
      mes,
      version_calculo
    FROM silver.resumen_wip_por_prenda
    WHERE tipo_de_producto = '{TIPO_PRENDA}'
      AND version_calculo = '{VERSION_CALCULO}'
    LIMIT 20;
    """
    print_query(sql_sin_filtro)
    cursor.execute(sql_sin_filtro)
    wips_sin_filtro = cursor.fetchall()

    print(f"Total registros WIP sin filtro: {len(wips_sin_filtro)}")

    # Query CON filtros
    print_subsection("Query CON filtros (>= 200 prendas, marca)")
    sql_con_filtro = f"""
    SELECT
      wip_id,
      tipo_de_producto,
      total_prendas,
      costo_por_prenda,
      marca,
      mes,
      version_calculo
    FROM silver.resumen_wip_por_prenda
    WHERE tipo_de_producto = '{TIPO_PRENDA}'
      AND version_calculo = '{VERSION_CALCULO}'
      AND total_prendas >= 200
      AND marca = '{MARCA}'
    ORDER BY wip_id
    LIMIT 50;
    """
    print_query(sql_con_filtro)
    cursor.execute(sql_con_filtro)
    wips_con_filtro = cursor.fetchall()

    print(f"Total registros WIP CON filtro: {len(wips_con_filtro)}")

    if len(wips_sin_filtro) > len(wips_con_filtro):
        excluidas = len(wips_sin_filtro) - len(wips_con_filtro)
        print(f"⚠️  {excluidas} registros EXCLUIDOS por filtro")

    if wips_con_filtro:
        print("\nPrimeros registros filtrados:")
        for row in wips_con_filtro[:10]:
            print(f"  WIP {row['wip_id']}: ${row['costo_por_prenda']} ({row['total_prendas']} prendas)")

        # Promedios por WIP
        print_subsection("Cálculo de costo promedio por WIP")
        sql_promedio_wip = f"""
        SELECT
          wip_id,
          AVG(CAST(costo_por_prenda AS FLOAT)) as costo_promedio,
          COUNT(*) as registros,
          MIN(total_prendas) as min_prendas,
          MAX(total_prendas) as max_prendas
        FROM silver.resumen_wip_por_prenda
        WHERE tipo_de_producto = '{TIPO_PRENDA}'
          AND version_calculo = '{VERSION_CALCULO}'
          AND total_prendas >= 200
          AND marca = '{MARCA}'
        GROUP BY wip_id
        ORDER BY wip_id;
        """
        print_query(sql_promedio_wip)
        cursor.execute(sql_promedio_wip)
        wips_promedios = cursor.fetchall()

        print(f"\nWIPs disponibles: {len(wips_promedios)}")
        costo_wips_total = 0

        for row in wips_promedios:
            print(f"\n  WIP {row['wip_id']}:")
            print(f"    - Costo Promedio: ${row['costo_promedio']:.4f}")
            print(f"    - Registros Promediados: {row['registros']}")
            print(f"    - Rango Prendas: {row['min_prendas']} - {row['max_prendas']}")
            costo_wips_total += row['costo_promedio']

        print(f"\n  → COSTO TOTAL WIPs: ${costo_wips_total:.4f}")

        return {
            'wips': wips_promedios,
            'costo_total': costo_wips_total,
            'cantidad_wips': len(wips_promedios)
        }
    else:
        print("✗ NO hay WIPs que cumplan los filtros")
        return None

    cursor.close()

# ============================================================================
# PASO 4: COSTOS INDIRECTOS
# ============================================================================

def paso_4_costos_indirectos(conn):
    """Obtiene costos indirectos"""
    print_section("PASO 4: COSTOS INDIRECTOS")

    cursor = conn.cursor(cursor_factory=DictCursor)

    print_subsection("Query CON filtro >= 200 prendas")
    sql = f"""
    SELECT
      codigo_estilo,
      costo_indirecto_fijo,
      gasto_administracion,
      gasto_ventas,
      prendas_requeridas,
      cod_ordpro,
      version_calculo
    FROM silver.costo_op_detalle
    WHERE codigo_estilo = {ESTILO}
      AND version_calculo = '{VERSION_CALCULO}'
      AND prendas_requeridas >= 200
      AND cliente = '{MARCA}'
    ORDER BY prendas_requeridas DESC
    LIMIT 20;
    """
    print_query(sql)
    cursor.execute(sql)
    registros = cursor.fetchall()

    print(f"Total OPs para costos indirectos: {len(registros)}")

    if registros:
        print("\nPrimeras OPs:")
        for i, row in enumerate(registros[:5]):
            print(f"\n  OP #{i+1}: {row['cod_ordpro']}")
            print(f"    - Prendas: {row['prendas_requeridas']}")
            print(f"    - CIF: ${row['costo_indirecto_fijo']}")
            print(f"    - Gasto Admin: ${row['gasto_administracion']}")
            print(f"    - Gasto Ventas: ${row['gasto_ventas']}")

        # Promedios
        print_subsection("Cálculo de promedios de costos indirectos")
        sql_promedio = f"""
        SELECT
          AVG(CAST(costo_indirecto_fijo AS FLOAT)) as cif_promedio,
          AVG(CAST(gasto_administracion AS FLOAT)) as admin_promedio,
          AVG(CAST(gasto_ventas AS FLOAT)) as ventas_promedio,
          COUNT(*) as ops_promediadas
        FROM silver.costo_op_detalle
        WHERE codigo_estilo = {ESTILO}
          AND version_calculo = '{VERSION_CALCULO}'
          AND prendas_requeridas >= 200
          AND cliente = '{MARCA}';
        """
        print_query(sql_promedio)
        cursor.execute(sql_promedio)
        promedios = cursor.fetchone()

        if promedios:
            print(f"\nCostos Indirectos Promediados:")
            print(f"  - CIF: ${promedios['cif_promedio']:.4f}")
            print(f"  - Gasto Admin: ${promedios['admin_promedio']:.4f}")
            print(f"  - Gasto Ventas: ${promedios['ventas_promedio']:.4f}")
            print(f"  - OPs Promediadas: {promedios['ops_promediadas']}")

            costo_indirecto_total = (
                promedios['cif_promedio'] +
                promedios['admin_promedio'] +
                promedios['ventas_promedio']
            )
            print(f"\n  → COSTO INDIRECTO TOTAL: ${costo_indirecto_total:.4f}")

            return {
                'cif': promedios['cif_promedio'],
                'administracion': promedios['admin_promedio'],
                'ventas': promedios['ventas_promedio'],
                'total': costo_indirecto_total
            }
    else:
        print("✗ NO hay OPs para calcular costos indirectos")
        return None

    cursor.close()

# ============================================================================
# PASO 5: APLICACIÓN DE FACTORES
# ============================================================================

def paso_5_factores(costo_directo, costo_indirecto, costo_wips):
    """Calcula los factores de ajuste"""
    print_section("PASO 5: APLICACIÓN DE FACTORES DE AJUSTE")

    # Factor de Marca
    print_subsection("1. Factor de Marca")
    print(f"Marca: {MARCA}")

    FACTORES_MARCA = {
        "LACOSTE": 1.05,
        "GREYSON": 1.05,
        "GREYSON CLOTHIERS": 1.10,
        "LULULEMON": 0.95,
        "PATAGONIA": 0.95,
        "OTRAS MARCAS": 1.10,
    }

    marca_upper = MARCA.upper().strip()
    factor_marca = 1.10  # Default

    for marca_key, factor in FACTORES_MARCA.items():
        if marca_key != "OTRAS MARCAS":
            if marca_key in marca_upper or marca_upper in marca_key:
                factor_marca = factor
                print(f"✓ Coincidencia exacta/parcial: {marca_key}")
                break

    if factor_marca == 1.10:
        print(f"→ Sin coincidencia exacta, usando OTRAS MARCAS: {factor_marca}x")

    print(f"  Factor Marca: {factor_marca}x ({(factor_marca-1)*100:+.1f}%)")

    # Factor de Lote
    print_subsection("2. Factor de Lote")
    print(f"Cantidad: {CANTIDAD_PRENDAS} prendas")

    RANGOS_LOTE = {
        "Micro Lote": {"min": 1, "max": 50, "factor": 1.15},
        "Lote Pequeño": {"min": 51, "max": 500, "factor": 1.10},
        "Lote Mediano": {"min": 501, "max": 1000, "factor": 1.05},
        "Lote Grande": {"min": 1001, "max": 4000, "factor": 1.00},
        "Lote Masivo": {"min": 4001, "max": 999999, "factor": 0.90},
    }

    categoria_lote = None
    factor_lote = 1.00

    for categoria, config in RANGOS_LOTE.items():
        if config["min"] <= CANTIDAD_PRENDAS <= config["max"]:
            categoria_lote = categoria
            factor_lote = config["factor"]
            break

    print(f"✓ Categoría: {categoria_lote}")
    print(f"  Factor Lote: {factor_lote}x ({(factor_lote-1)*100:+.1f}%)")

    # Factor de Esfuerzo
    print_subsection("3. Factor de Esfuerzo")
    print(f"Tipo Prenda: {TIPO_PRENDA}")
    print("Nota: Para T-SHIRT simple sin bordado = Esfuerzo Bajo")

    factor_esfuerzo = 0.90  # Bajo
    print(f"✓ Esfuerzo: Bajo")
    print(f"  Factor Esfuerzo: {factor_esfuerzo}x ({(factor_esfuerzo-1)*100:+.1f}%)")

    # Factor de Estilo
    print_subsection("4. Factor de Estilo")
    print("Asumiendo Estilo Recurrente (basado en historial)")

    factor_estilo = 1.00  # Recurrente
    print(f"✓ Categoría Estilo: Recurrente")
    print(f"  Factor Estilo: {factor_estilo}x ({(factor_estilo-1)*100:+.1f}%)")

    return {
        'marca': factor_marca,
        'lote': factor_lote,
        'esfuerzo': factor_esfuerzo,
        'estilo': factor_estilo
    }

# ============================================================================
# PASO 6: CÁLCULO FINAL
# ============================================================================

def paso_6_calculo_final(costo_directo, costo_indirecto, costo_wips, factores):
    """Calcula el precio final"""
    print_section("PASO 6: CÁLCULO FINAL DEL PRECIO")

    print_subsection("Desglose de Costos Base")

    print(f"\nCostos Directos: ${costo_directo['total']:.4f}")
    print(f"  - Textil: ${costo_directo['costo_textil']:.4f}")
    print(f"  - Manufactura: ${costo_directo['costo_manufactura']:.4f}")
    print(f"  - Materia Prima: ${costo_directo['costo_materia_prima']:.4f}")
    print(f"  - Avíos: ${costo_directo['costo_avios']:.4f}")

    print(f"\nCostos Indirectos: ${costo_indirecto['total']:.4f}")
    print(f"  - CIF: ${costo_indirecto['cif']:.4f}")
    print(f"  - Administración: ${costo_indirecto['administracion']:.4f}")
    print(f"  - Ventas: ${costo_indirecto['ventas']:.4f}")

    print(f"\nCostos WIPs: ${costo_wips['costo_total']:.4f}")
    print(f"  ({costo_wips['cantidad_wips']} WIPs activos)")

    # Costo Base
    costo_base = (costo_directo['total'] +
                  costo_indirecto['total'] +
                  costo_wips['costo_total'])

    print(f"\n{'='*40}")
    print(f"COSTO BASE TOTAL: ${costo_base:.4f}")
    print(f"{'='*40}")

    # Aplicar Margen Operacional (20% ejemplo)
    margen_operacional = costo_base * 0.20
    costo_con_margen = costo_base + margen_operacional

    print(f"\nMargen Operacional (20%): ${margen_operacional:.4f}")
    print(f"Costo con Margen: ${costo_con_margen:.4f}")

    # Aplicar Factores
    print_subsection("Aplicación de Factores Ajuste")

    costo_ajustado = costo_con_margen

    print(f"\nCosto Base con Margen: ${costo_ajustado:.4f}")

    print(f"\n× Factor Marca ({factores['marca']}x): ${costo_ajustado:.4f} × {factores['marca']}")
    costo_ajustado *= factores['marca']
    print(f"  = ${costo_ajustado:.4f}")

    print(f"\n× Factor Lote ({factores['lote']}x): ${costo_ajustado:.4f} × {factores['lote']}")
    costo_ajustado *= factores['lote']
    print(f"  = ${costo_ajustado:.4f}")

    print(f"\n× Factor Esfuerzo ({factores['esfuerzo']}x): ${costo_ajustado:.4f} × {factores['esfuerzo']}")
    costo_ajustado *= factores['esfuerzo']
    print(f"  = ${costo_ajustado:.4f}")

    print(f"\n× Factor Estilo ({factores['estilo']}x): ${costo_ajustado:.4f} × {factores['estilo']}")
    costo_ajustado *= factores['estilo']
    print(f"  = ${costo_ajustado:.4f}")

    # Factor de Seguridad
    factor_seguridad = 1.03  # 3%
    costo_final = costo_ajustado * factor_seguridad

    print(f"\n× Factor Seguridad ({factor_seguridad}x): ${costo_ajustado:.4f} × {factor_seguridad}")
    print(f"  = ${costo_final:.4f}")

    print(f"\n{'='*40}")
    print(f"PRECIO FINAL POR PRENDA: ${costo_final:.2f}")
    print(f"{'='*40}")

    print_subsection("Resumen Ejecutivo")
    print(f"""
Marca:           {MARCA}
Estilo:          {ESTILO}
Tipo Prenda:     {TIPO_PRENDA}
Cantidad:        {CANTIDAD_PRENDAS} (Lote Mediano)
Versión:         {VERSION_CALCULO}

DESGLOSE:
├─ Costo Base:               ${costo_base:.4f}
├─ Margen Operacional (20%): ${margen_operacional:.4f}
├─ Subtotal:                 ${costo_con_margen:.4f}
└─ Factores Ajuste:
   ├─ Marca ({factores['marca']}x):     {(factores['marca']-1)*100:+.1f}%
   ├─ Lote ({factores['lote']}x):      {(factores['lote']-1)*100:+.1f}%
   ├─ Esfuerzo ({factores['esfuerzo']}x): {(factores['esfuerzo']-1)*100:+.1f}%
   └─ Estilo ({factores['estilo']}x):    {(factores['estilo']-1)*100:+.1f}%

PRECIO FINAL:   ${costo_final:.2f} por prenda
    """)

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "="*80)
    print("SCRIPT DE DEBUG - COTIZACIÓN PASO A PASO")
    print("="*80)
    print(f"\nFecha de Ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nPARÁMETROS:")
    print(f"  - Marca: {MARCA}")
    print(f"  - Estilo: {ESTILO}")
    print(f"  - Tipo Prenda: {TIPO_PRENDA}")
    print(f"  - Cantidad: {CANTIDAD_PRENDAS} prendas")
    print(f"  - Versión: {VERSION_CALCULO}")

    # Conectar a BD
    conn = connect_db()
    print(f"\n✓ Conexión a base de datos establecida")

    try:
        # Paso 1: Verificar Estilo
        estado_estilo = paso_1_verificar_estilo(conn)
        if not estado_estilo:
            print("\n⚠️  No se puede continuar sin estilo válido")
            return

        # Paso 2: Costos Directos
        costo_directo = paso_2_costos_directos(conn, estado_estilo)
        if not costo_directo:
            print("\n⚠️  No se puede continuar sin costos directos")
            return

        # Paso 3: Costos WIPs
        costo_wips = paso_3_costos_wips(conn)
        if not costo_wips:
            print("\n⚠️  No se puede continuar sin costos WIPs")
            return

        # Paso 4: Costos Indirectos
        costo_indirecto = paso_4_costos_indirectos(conn)
        if not costo_indirecto:
            print("\n⚠️  No se puede continuar sin costos indirectos")
            return

        # Paso 5: Factores
        factores = paso_5_factores(costo_directo, costo_indirecto, costo_wips)

        # Paso 6: Cálculo Final
        paso_6_calculo_final(costo_directo, costo_indirecto, costo_wips, factores)

    finally:
        conn.close()
        print("\n✓ Conexión cerrada")
        print("\n" + "="*80)
        print("FIN DEL DEBUG")
        print("="*80 + "\n")

if __name__ == "__main__":
    main()
