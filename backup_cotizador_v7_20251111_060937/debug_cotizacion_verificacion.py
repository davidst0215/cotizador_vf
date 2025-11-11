#!/usr/bin/env python3
"""Debug de cotización con NORMALIZACIÓN VERIFICADA - Estilo 18420"""

import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, timedelta

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
ESTILO = "18420"
TIPO_PRENDA = "POLO BOX"
VERSION_CALCULO = "FLUIDA"
CANTIDAD_LOTE = 750

# Rangos de seguridad (minimo y maximo permitido)
RANGOS_SEGURIDAD = {
    "costo_textil": {"min": 0.05, "max": 10},
    "costo_manufactura": {"min": 0.05, "max": 10},
    "costo_materia_prima": {"min": 0.05, "max": 10},
    "costo_avios": {"min": 0.05, "max": 10},
    "costo_indirecto_fijo": {"min": 0.05, "max": 10},
    "gasto_administracion": {"min": 0.05, "max": 10},
    "gasto_ventas": {"min": 0.05, "max": 10},
}

def section(title):
    print("\n" + "="*80)
    print(title)
    print("="*80)

def normalizar_costo(valor, componente):
    """Aplica rango de seguridad a un costo"""
    rango = RANGOS_SEGURIDAD.get(componente, {"min": 0.05, "max": 10})
    valor_original = valor

    if valor < rango["min"]:
        valor = rango["min"]
    elif valor > rango["max"]:
        valor = rango["max"]

    fue_limitado = valor != valor_original
    return valor, fue_limitado

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=DictCursor)

# ====== PASO 1: OBTENER FECHA_CORRIDA MAXIMA ======
section("PASO 1: OBTENER FECHA_CORRIDA MAXIMA")

sql_max_fecha = f"""
SELECT MAX(fecha_corrida) as max_fecha_corrida
FROM silver.costo_op_detalle
WHERE version_calculo = '{VERSION_CALCULO}'
"""
print(f"[SQL]: {sql_max_fecha}")
cur.execute(sql_max_fecha)
result = cur.fetchone()
max_fecha_corrida = result['max_fecha_corrida']
print(f"MAX fecha_corrida: {max_fecha_corrida}")

# ====== PASO 2: CALCULAR VENTANA TEMPORAL (18 MESES) ======
section("PASO 2: CALCULAR VENTANA TEMPORAL")

fecha_limite = max_fecha_corrida - timedelta(days=18*30)
print(f"Ventana: desde {fecha_limite} hasta {max_fecha_corrida}")

# ====== PASO 3: OBTENER COSTOS DIRECTOS CON TODOS LOS FILTROS ======
section("PASO 3: COSTOS DIRECTOS (CON NORMALIZACION ANTES DE PROMEDIAR)")

sql_costos_directos = f"""
SELECT cod_ordpro, prendas_requeridas, costo_textil, costo_manufactura,
       costo_materia_prima, costo_avios
FROM silver.costo_op_detalle
WHERE estilo_propio = '{ESTILO}'
  AND tipo_de_producto = '{TIPO_PRENDA}'
  AND version_calculo = '{VERSION_CALCULO}'
  AND fecha_corrida = '{max_fecha_corrida}'
  AND fecha_facturacion >= '{fecha_limite}'
  AND prendas_requeridas >= 200
  AND cliente = '{MARCA}'
ORDER BY fecha_facturacion DESC
"""
print(f"[SQL]: {sql_costos_directos}\n")
cur.execute(sql_costos_directos)
ops = cur.fetchall()

print(f"Total OPs encontradas: {len(ops)}\n")

if ops:
    print("[DETALLES DE CADA OP]")
    for i, op in enumerate(ops):
        print(f"\nOP {i+1}: {op['cod_ordpro']} ({op['prendas_requeridas']} prendas)")
        print(f"  Costos BRUTOS:")
        print(f"    - Textil: ${op['costo_textil']:.4f} / {op['prendas_requeridas']} = ${op['costo_textil']/op['prendas_requeridas']:.4f}")
        print(f"    - Manufactura: ${op['costo_manufactura']:.4f} / {op['prendas_requeridas']} = ${op['costo_manufactura']/op['prendas_requeridas']:.4f}")
        print(f"    - Materia Prima: ${op['costo_materia_prima']:.4f} / {op['prendas_requeridas']} = ${op['costo_materia_prima']/op['prendas_requeridas']:.4f}")
        print(f"    - Avios: ${op['costo_avios']:.4f} / {op['prendas_requeridas']} = ${op['costo_avios']/op['prendas_requeridas']:.4f}")

    # ====== PASO 4: APLICAR NORMALIZACION ANTES DE PROMEDIAR ======
    section("PASO 4: APLICAR NORMALIZACION A CADA VALOR (ANTES DE PROMEDIAR)")

    # Calcular costos unitarios
    costos_unitarios = []
    for op in ops:
        costo_unit = {
            "cod_ordpro": op['cod_ordpro'],
            "textil": op['costo_textil'] / op['prendas_requeridas'],
            "manufactura": op['costo_manufactura'] / op['prendas_requeridas'],
            "materia_prima": op['costo_materia_prima'] / op['prendas_requeridas'],
            "avios": op['costo_avios'] / op['prendas_requeridas'],
        }
        costos_unitarios.append(costo_unit)

    # Aplicar normalizacion a cada componente
    print("\n[NORMALIZACION POR COMPONENTE]")

    # Textil
    print("\nCOSTO TEXTIL:")
    valores_textil = [c['textil'] for c in costos_unitarios]
    valores_textil_normalizados = []
    ajustes_textil = 0
    for i, val in enumerate(valores_textil):
        val_norm, fue_ajustado = normalizar_costo(val, "costo_textil")
        valores_textil_normalizados.append(val_norm)
        if fue_ajustado:
            print(f"  OP {i+1}: ${val:.4f} -> ${val_norm:.4f} [CAPPED]")
            ajustes_textil += 1
        else:
            print(f"  OP {i+1}: ${val:.4f} (OK)")

    promedio_textil = sum(valores_textil_normalizados) / len(valores_textil_normalizados)
    print(f"  PROMEDIO TEXTIL (NORMALIZADO): ${promedio_textil:.4f} ({ajustes_textil} ajustes)")

    # Manufactura
    print("\nCOSTO MANUFACTURA:")
    valores_manufactura = [c['manufactura'] for c in costos_unitarios]
    valores_manufactura_normalizados = []
    ajustes_manufactura = 0
    for i, val in enumerate(valores_manufactura):
        val_norm, fue_ajustado = normalizar_costo(val, "costo_manufactura")
        valores_manufactura_normalizados.append(val_norm)
        if fue_ajustado:
            print(f"  OP {i+1}: ${val:.4f} -> ${val_norm:.4f} [CAPPED]")
            ajustes_manufactura += 1
        else:
            print(f"  OP {i+1}: ${val:.4f} (OK)")

    promedio_manufactura = sum(valores_manufactura_normalizados) / len(valores_manufactura_normalizados)
    print(f"  PROMEDIO MANUFACTURA (NORMALIZADO): ${promedio_manufactura:.4f} ({ajustes_manufactura} ajustes)")

    # Materia Prima
    print("\nCOSTO MATERIA PRIMA:")
    valores_materia_prima = [c['materia_prima'] for c in costos_unitarios]
    valores_materia_prima_normalizados = []
    ajustes_materia_prima = 0
    for i, val in enumerate(valores_materia_prima):
        val_norm, fue_ajustado = normalizar_costo(val, "costo_materia_prima")
        valores_materia_prima_normalizados.append(val_norm)
        if fue_ajustado:
            print(f"  OP {i+1}: ${val:.4f} -> ${val_norm:.4f} [CAPPED]")
            ajustes_materia_prima += 1
        else:
            print(f"  OP {i+1}: ${val:.4f} (OK)")

    promedio_materia_prima = sum(valores_materia_prima_normalizados) / len(valores_materia_prima_normalizados)
    print(f"  PROMEDIO MATERIA PRIMA (NORMALIZADO): ${promedio_materia_prima:.4f} ({ajustes_materia_prima} ajustes)")

    # Avios
    print("\nCOSTO AVIOS:")
    valores_avios = [c['avios'] for c in costos_unitarios]
    valores_avios_normalizados = []
    ajustes_avios = 0
    for i, val in enumerate(valores_avios):
        val_norm, fue_ajustado = normalizar_costo(val, "costo_avios")
        valores_avios_normalizados.append(val_norm)
        if fue_ajustado:
            print(f"  OP {i+1}: ${val:.4f} -> ${val_norm:.4f} [CAPPED]")
            ajustes_avios += 1
        else:
            print(f"  OP {i+1}: ${val:.4f} (OK)")

    promedio_avios = sum(valores_avios_normalizados) / len(valores_avios_normalizados)
    print(f"  PROMEDIO AVIOS (NORMALIZADO): ${promedio_avios:.4f} ({ajustes_avios} ajustes)")

    # ====== PASO 5: OBTENER COSTOS INDIRECTOS (CON NORMALIZACION) ======
    section("PASO 5: COSTOS INDIRECTOS (CON NORMALIZACION ANTES DE PROMEDIAR)")

    sql_costos_indirectos = f"""
    SELECT costo_indirecto_fijo, gasto_administracion, gasto_ventas
    FROM silver.costo_op_detalle
    WHERE estilo_propio = '{ESTILO}'
      AND tipo_de_producto = '{TIPO_PRENDA}'
      AND version_calculo = '{VERSION_CALCULO}'
      AND fecha_corrida = '{max_fecha_corrida}'
      AND fecha_facturacion >= '{fecha_limite}'
      AND prendas_requeridas >= 200
      AND cliente = '{MARCA}'
    ORDER BY fecha_facturacion DESC
    """
    print(f"[SQL]: {sql_costos_indirectos}\n")
    cur.execute(sql_costos_indirectos)
    ops_indirectos = cur.fetchall()

    print(f"Total OPs para indirectos: {len(ops_indirectos)}\n")

    if ops_indirectos:
        # CIF
        print("COSTO INDIRECTO FIJO:")
        valores_cif = [float(op['costo_indirecto_fijo']) for op in ops_indirectos]
        valores_cif_normalizados = []
        ajustes_cif = 0
        for i, val in enumerate(valores_cif):
            val_norm, fue_ajustado = normalizar_costo(val, "costo_indirecto_fijo")
            valores_cif_normalizados.append(val_norm)
            if fue_ajustado:
                print(f"  OP {i+1}: ${val:.4f} -> ${val_norm:.4f} [CAPPED]")
                ajustes_cif += 1
            else:
                print(f"  OP {i+1}: ${val:.4f} (OK)")

        promedio_cif = sum(valores_cif_normalizados) / len(valores_cif_normalizados)
        print(f"  PROMEDIO CIF (NORMALIZADO): ${promedio_cif:.4f} ({ajustes_cif} ajustes)")

        # Admin
        print("\nGASTO ADMINISTRACION:")
        valores_admin = [float(op['gasto_administracion']) for op in ops_indirectos]
        valores_admin_normalizados = []
        ajustes_admin = 0
        for i, val in enumerate(valores_admin):
            val_norm, fue_ajustado = normalizar_costo(val, "gasto_administracion")
            valores_admin_normalizados.append(val_norm)
            if fue_ajustado:
                print(f"  OP {i+1}: ${val:.4f} -> ${val_norm:.4f} [CAPPED]")
                ajustes_admin += 1
            else:
                print(f"  OP {i+1}: ${val:.4f} (OK)")

        promedio_admin = sum(valores_admin_normalizados) / len(valores_admin_normalizados)
        print(f"  PROMEDIO ADMIN (NORMALIZADO): ${promedio_admin:.4f} ({ajustes_admin} ajustes)")

        # Ventas
        print("\nGASTO VENTAS:")
        valores_ventas = [float(op['gasto_ventas']) for op in ops_indirectos]
        valores_ventas_normalizados = []
        ajustes_ventas = 0
        for i, val in enumerate(valores_ventas):
            val_norm, fue_ajustado = normalizar_costo(val, "gasto_ventas")
            valores_ventas_normalizados.append(val_norm)
            if fue_ajustado:
                print(f"  OP {i+1}: ${val:.4f} -> ${val_norm:.4f} [CAPPED]")
                ajustes_ventas += 1
            else:
                print(f"  OP {i+1}: ${val:.4f} (OK)")

        promedio_ventas = sum(valores_ventas_normalizados) / len(valores_ventas_normalizados)
        print(f"  PROMEDIO VENTAS (NORMALIZADO): ${promedio_ventas:.4f} ({ajustes_ventas} ajustes)")

# ====== RESUMEN FINAL ======
section("RESUMEN EJECUTIVO CON NORMALIZACION")

costo_directo_total = promedio_textil + promedio_manufactura + promedio_materia_prima + promedio_avios
costo_indirecto_total = promedio_cif + promedio_admin + promedio_ventas

print(f"""
COSTOS DIRECTOS (UNITARIOS):
  - Textil:         ${promedio_textil:.4f}
  - Manufactura:    ${promedio_manufactura:.4f}
  - Materia Prima:  ${promedio_materia_prima:.4f}
  - Avios:          ${promedio_avios:.4f}
  ═════════════════════════════════
  TOTAL DIRECTO:    ${costo_directo_total:.4f}

COSTOS INDIRECTOS (UNITARIOS):
  - CIF:            ${promedio_cif:.4f}
  - Admin:          ${promedio_admin:.4f}
  - Ventas:         ${promedio_ventas:.4f}
  ═════════════════════════════════
  TOTAL INDIRECTO:  ${costo_indirecto_total:.4f}

SUBTOTAL (Directo + Indirecto): ${costo_directo_total + costo_indirecto_total:.4f}

VERIFICACION:
  ✓ Normalizacion aplicada a CADA valor ANTES de promediar
  ✓ Todos los costos mayores a $10.00 fueron capped a $10.00
  ✓ Filtros aplicados:
    - prendas_requeridas >= 200
    - cliente = {MARCA}
    - fecha_facturacion >= 18 meses antes de max(fecha_corrida)
    - version_calculo = {VERSION_CALCULO}
""")

conn.close()
print("[COMPLETO] Debug finalizado correctamente\n")
