#!/usr/bin/env python3
"""Debug simple de cotizacion - MONTAIGNE HONG KONG LIMITED / Estilo 123 / T-SHIRT"""

import psycopg2
from psycopg2.extras import DictCursor

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

MARCA = "MONTAIGNE HONG KONG LIMITED"
ESTILO = "18420"  # Estilo que existe en historial
TIPO_PRENDA = "POLO BOX"  # Tipo de prenda correcto
VERSION_CALCULO = "FLUIDA"  # FLUIDA (no FLUIDO)
CANTIDAD_LOTE = 750  # Lote Mediano

def section(title):
    print("\n" + "="*80)
    print(title)
    print("="*80)

def query(sql):
    print("\n[SQL]:")
    print(sql)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=DictCursor)

# ====== PASO 1: ESTILO ======
section("PASO 1: VERIFICACION DE ESTILO")

sql = f"""
SELECT codigo_estilo, total_prendas_desde_2020, categoria_recurrencia
FROM silver.historial_estilos
WHERE codigo_estilo = '{ESTILO}'
"""
query(sql)
cur.execute(sql)
estilo = cur.fetchone()

if estilo:
    print(f"[ENCONTRADO] Estilo {ESTILO}")
    print(f"  Prendas Totales (desde 2020): {estilo['total_prendas_desde_2020']}")
    print(f"  Categoria: {estilo['categoria_recurrencia']}")
else:
    print(f"[NO ENCONTRADO] Estilo {ESTILO}")
    conn.close()
    exit()

# ====== PASO 2: COSTOS DIRECTOS SIN FILTRO ======
section("PASO 2: COSTOS DIRECTOS - SIN FILTRO")

sql = f"""
SELECT cod_ordpro, prendas_requeridas, costo_textil, costo_manufactura,
       costo_materia_prima, costo_avios
FROM silver.costo_op_detalle
WHERE estilo_propio = '{ESTILO}'
  AND tipo_de_producto = '{TIPO_PRENDA}'
  AND version_calculo = '{VERSION_CALCULO}'
"""
query(sql)
cur.execute(sql)
ops_sin_filtro = cur.fetchall()

print(f"Total OPs SIN filtro: {len(ops_sin_filtro)}")
if ops_sin_filtro:
    for i, op in enumerate(ops_sin_filtro[:3]):
        print(f"  OP {i+1}: {op['cod_ordpro']} | Prendas: {op['prendas_requeridas']} | Textil: {op['costo_textil']}")

# ====== PASO 3: COSTOS DIRECTOS CON FILTRO ======
section("PASO 3: COSTOS DIRECTOS - CON FILTROS (>= 200 prendas, marca)")

sql = f"""
SELECT cod_ordpro, prendas_requeridas, costo_textil, costo_manufactura,
       costo_materia_prima, costo_avios
FROM silver.costo_op_detalle
WHERE estilo_propio = '{ESTILO}'
  AND tipo_de_producto = '{TIPO_PRENDA}'
  AND version_calculo = '{VERSION_CALCULO}'
  AND prendas_requeridas >= 200
  AND cliente = '{MARCA}'
"""
query(sql)
cur.execute(sql)
ops_con_filtro = cur.fetchall()

print(f"Total OPs CON filtro: {len(ops_con_filtro)}")
excluidas = len(ops_sin_filtro) - len(ops_con_filtro)
if excluidas > 0:
    print(f"[FILTRADAS] {excluidas} OPs excluidas por volumen < 200")

if ops_con_filtro:
    for i, op in enumerate(ops_con_filtro[:3]):
        print(f"  OP {i+1}: {op['cod_ordpro']} | Prendas: {op['prendas_requeridas']} | Textil: {op['costo_textil']}")

    # Promedios
    sql_prom = f"""
    SELECT
      AVG(CAST(costo_textil AS FLOAT) / NULLIF(prendas_requeridas, 0)) as costo_textil_unitario,
      AVG(CAST(costo_manufactura AS FLOAT) / NULLIF(prendas_requeridas, 0)) as costo_manufactura_unitario,
      AVG(CAST(costo_materia_prima AS FLOAT) / NULLIF(prendas_requeridas, 0)) as costo_materia_prima_unitario,
      AVG(CAST(costo_avios AS FLOAT) / NULLIF(prendas_requeridas, 0)) as costo_avios_unitario
    FROM silver.costo_op_detalle
    WHERE estilo_propio = '{ESTILO}'
      AND tipo_de_producto = '{TIPO_PRENDA}'
      AND version_calculo = '{VERSION_CALCULO}'
      AND prendas_requeridas >= 200
      AND cliente = '{MARCA}'
    """
    cur.execute(sql_prom)
    prom = cur.fetchone()

    print(f"\n[PROMEDIOS UNITARIOS]")
    print(f"  Textil: ${prom['costo_textil_unitario']:.4f}")
    print(f"  Manufactura: ${prom['costo_manufactura_unitario']:.4f}")
    print(f"  Materia Prima: ${prom['costo_materia_prima_unitario']:.4f}")
    print(f"  Avios: ${prom['costo_avios_unitario']:.4f}")

    costo_directo = (prom['costo_textil_unitario'] + prom['costo_manufactura_unitario'] +
                     prom['costo_materia_prima_unitario'] + prom['costo_avios_unitario'])
    print(f"  TOTAL: ${costo_directo:.4f}")

# ====== PASO 4: COSTOS WIPS SIN FILTRO ======
section("PASO 4: COSTOS WIPS - SIN FILTRO")

sql = f"""
SELECT DISTINCT wip_id, total_prendas, costo_por_prenda
FROM silver.resumen_wip_por_prenda
WHERE tipo_de_producto = '{TIPO_PRENDA}'
  AND version_calculo = '{VERSION_CALCULO}'
LIMIT 20
"""
query(sql)
cur.execute(sql)
wips_sin_filtro = cur.fetchall()

print(f"Total registros WIP SIN filtro: {len(wips_sin_filtro)}")
if wips_sin_filtro:
    for i, wip in enumerate(wips_sin_filtro[:5]):
        print(f"  WIP {wip['wip_id']}: ${wip['costo_por_prenda']} ({wip['total_prendas']} prendas)")

# ====== PASO 5: COSTOS WIPS CON FILTRO ======
section("PASO 5: COSTOS WIPS - CON FILTROS (>= 200 prendas, marca)")

sql = f"""
SELECT DISTINCT wip_id, total_prendas, costo_por_prenda
FROM silver.resumen_wip_por_prenda
WHERE tipo_de_producto = '{TIPO_PRENDA}'
  AND version_calculo = '{VERSION_CALCULO}'
  AND total_prendas >= 200
  AND marca = '{MARCA}'
ORDER BY wip_id
"""
query(sql)
cur.execute(sql)
wips_con_filtro = cur.fetchall()

print(f"Total registros WIP CON filtro: {len(wips_con_filtro)}")
if len(wips_sin_filtro) > len(wips_con_filtro):
    print(f"[FILTRADOS] {len(wips_sin_filtro) - len(wips_con_filtro)} registros excluidos")

if wips_con_filtro:
    for i, wip in enumerate(wips_con_filtro[:10]):
        print(f"  WIP {wip['wip_id']}: ${wip['costo_por_prenda']} ({wip['total_prendas']} prendas)")

    # Promedios por WIP
    sql_wip_prom = f"""
    SELECT wip_id, AVG(CAST(costo_por_prenda AS FLOAT)) as costo_promedio, COUNT(*) as registros
    FROM silver.resumen_wip_por_prenda
    WHERE tipo_de_producto = '{TIPO_PRENDA}'
      AND version_calculo = '{VERSION_CALCULO}'
      AND total_prendas >= 200
      AND marca = '{MARCA}'
    GROUP BY wip_id
    ORDER BY wip_id
    """
    cur.execute(sql_wip_prom)
    wips_promedios = cur.fetchall()

    print(f"\n[PROMEDIOS POR WIP]")
    costo_wips_total = 0
    for wip in wips_promedios:
        print(f"  WIP {wip['wip_id']}: ${wip['costo_promedio']:.4f} ({wip['registros']} registros)")
        costo_wips_total += wip['costo_promedio']

    print(f"  TOTAL WIPs: ${costo_wips_total:.4f}")

# ====== PASO 6: COSTOS INDIRECTOS ======
section("PASO 6: COSTOS INDIRECTOS (>= 200 prendas)")

sql = f"""
SELECT
  AVG(CAST(costo_indirecto_fijo AS FLOAT)) as cif,
  AVG(CAST(gasto_administracion AS FLOAT)) as admin,
  AVG(CAST(gasto_ventas AS FLOAT)) as ventas
FROM silver.costo_op_detalle
WHERE estilo_propio = '{ESTILO}'
  AND version_calculo = '{VERSION_CALCULO}'
  AND prendas_requeridas >= 200
  AND cliente = '{MARCA}'
"""
query(sql)
cur.execute(sql)
indirecto = cur.fetchone()

if indirecto:
    print(f"[PROMEDIOS]")
    print(f"  CIF: ${indirecto['cif']:.4f}")
    print(f"  Administracion: ${indirecto['admin']:.4f}")
    print(f"  Ventas: ${indirecto['ventas']:.4f}")
    costo_indirecto_total = indirecto['cif'] + indirecto['admin'] + indirecto['ventas']
    print(f"  TOTAL: ${costo_indirecto_total:.4f}")

# ====== PASO 7: FACTORES ======
section("PASO 7: FACTORES DE AJUSTE")

print(f"Marca: {MARCA}")
print(f"  Factor Marca: 1.10x (+10%, OTRAS MARCAS)")
print(f"Cantidad: 750 prendas")
print(f"  Factor Lote Mediano (501-1000): 1.05x (+5%)")
print(f"Tipo: T-SHIRT simple")
print(f"  Factor Esfuerzo Bajo: 0.90x (-10%)")
print(f"Estilo: Recurrente")
print(f"  Factor Estilo: 1.00x (0%)")

# ====== RESUMEN FINAL ======
section("RESUMEN EJECUTIVO")

print(f"""
Parametros:
  - Marca: {MARCA}
  - Estilo: {ESTILO}
  - Tipo Prenda: {TIPO_PRENDA}
  - Cantidad: 750 prendas (Lote Mediano)
  - Version: {VERSION_CALCULO}

Validaciones:
  [OK] Estilo encontrado en historial
  [OK] {len(ops_con_filtro)} OPs con volumen >= 200 prendas
  [OK] {len(wips_promedios)} WIPs disponibles
  [FILTRADOS] {len(ops_sin_filtro) - len(ops_con_filtro)} OPs por volumen < 200

Costos Base (por prenda):
  - Directo: ${costo_directo:.4f}
  - Indirecto: ${costo_indirecto_total:.4f}
  - WIPs: ${costo_wips_total:.4f}
  - Subtotal: ${costo_directo + costo_indirecto_total + costo_wips_total:.4f}

Factores Ajuste:
  x 1.10 (marca OTRAS MARCAS)
  x 1.05 (lote mediano)
  x 0.90 (esfuerzo bajo)
  x 1.00 (estilo recurrente)
  = Multiplicador Total: {1.10 * 1.05 * 0.90 * 1.00:.4f}x
""")

conn.close()
print("[COMPLETO] Debug finalizado correctamente")
