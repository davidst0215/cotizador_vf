#!/usr/bin/env python3
"""Trace detallado de cómo se calculan los costos con normalizacion"""

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

ESTILO = "18420"
TIPO_PRENDA = "POLO BOX"
VERSION_CALCULO = "FLUIDA"
MARCA = "MONTAIGNE HONG KONG LIMITED"

RANGOS_SEGURIDAD = {
    "costo_textil": {"min": 0.05, "max": 10},
    "costo_manufactura": {"min": 0.05, "max": 10},
    "costo_materia_prima": {"min": 0.05, "max": 10},
    "costo_avios": {"min": 0.05, "max": 10},
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=DictCursor)

print("="*100)
print("TRACE DETALLADO: CALCULO DE COSTOS CON NORMALIZACION")
print("="*100)

# ====== PASO 1: OBTENER DATOS BRUTOS DE LA BD ======
print("\nPASO 1: OBTENER FECHA_CORRIDA MAXIMA Y DATOS BRUTOS")
print("-" * 100)

# Primero obtener max fecha_corrida
sql_max_fecha = f"""
SELECT MAX(fecha_corrida) as max_fecha_corrida
FROM silver.costo_op_detalle
WHERE version_calculo = '{VERSION_CALCULO}'
"""

cur.execute(sql_max_fecha)
result = cur.fetchone()
max_fecha_corrida = result['max_fecha_corrida']
print(f"\nMAX fecha_corrida: {max_fecha_corrida}\n")

# Ahora obtener los datos CON TODOS LOS FILTROS
sql = f"""
SELECT cod_ordpro, prendas_requeridas, costo_textil, costo_manufactura,
       costo_materia_prima, costo_avios
FROM silver.costo_op_detalle
WHERE estilo_propio = '{ESTILO}'
  AND tipo_de_producto = '{TIPO_PRENDA}'
  AND version_calculo = '{VERSION_CALCULO}'
  AND fecha_corrida = '{max_fecha_corrida}'
  AND fecha_facturacion >= (SELECT MAX(fecha_facturacion) - INTERVAL '18 months' FROM silver.costo_op_detalle WHERE version_calculo = '{VERSION_CALCULO}')
  AND prendas_requeridas >= 200
  AND cliente = '{MARCA}'
ORDER BY fecha_facturacion DESC
"""

cur.execute(sql)
ops = cur.fetchall()

print(f"\nSQL ejecutada:")
print(f"{sql}\n")

print(f"RESULTADOS: {len(ops)} OPs encontradas\n")

for i, op in enumerate(ops, 1):
    print(f"OP {i}: {op['cod_ordpro']}")
    print(f"  Prendas requeridas: {op['prendas_requeridas']}")
    print(f"  Costo TOTAL Textil: ${op['costo_textil']}")
    print(f"  Costo TOTAL Manufactura: ${op['costo_manufactura']}")
    print(f"  Costo TOTAL Materia Prima: ${op['costo_materia_prima']}")
    print(f"  Costo TOTAL Avios: ${op['costo_avios']}\n")

# ====== PASO 2: CALCULAR COSTOS UNITARIOS ======
print("\nPASO 2: CALCULAR COSTOS UNITARIOS (dividir total / prendas)")
print("-" * 100)

costos_unitarios = []

for i, op in enumerate(ops, 1):
    textil_unitario = float(op['costo_textil']) / float(op['prendas_requeridas'])
    manufactura_unitario = float(op['costo_manufactura']) / float(op['prendas_requeridas'])
    materia_prima_unitaria = float(op['costo_materia_prima']) / float(op['prendas_requeridas'])
    avios_unitario = float(op['costo_avios']) / float(op['prendas_requeridas'])

    costo_unit = {
        "cod_ordpro": op['cod_ordpro'],
        "prendas": op['prendas_requeridas'],
        "textil": textil_unitario,
        "manufactura": manufactura_unitario,
        "materia_prima": materia_prima_unitaria,
        "avios": avios_unitario,
    }
    costos_unitarios.append(costo_unit)

    print(f"OP {i}: {op['cod_ordpro']}")
    print(f"  Textil:       ${op['costo_textil']} / {op['prendas_requeridas']} = ${textil_unitario:.4f}")
    print(f"  Manufactura:  ${op['costo_manufactura']} / {op['prendas_requeridas']} = ${manufactura_unitario:.4f}")
    print(f"  Materia Prima: ${op['costo_materia_prima']} / {op['prendas_requeridas']} = ${materia_prima_unitaria:.4f}")
    print(f"  Avios:        ${op['costo_avios']} / {op['prendas_requeridas']} = ${avios_unitario:.4f}\n")

# ====== PASO 3: APLICAR NORMALIZACION A CADA VALOR ======
print("\nPASO 3: APLICAR NORMALIZACION A CADA VALOR UNITARIO")
print("-" * 100)

def normalizar(valor, componente):
    rango = RANGOS_SEGURIDAD.get(componente, {"min": 0.05, "max": 10})
    valor_original = valor
    if valor < rango["min"]:
        valor = rango["min"]
    elif valor > rango["max"]:
        valor = rango["max"]
    fue_limitado = valor != valor_original
    return valor, fue_limitado, valor_original

# Normalizar Textil
print("\nCOSTO TEXTIL (rango: $0.05 - $10.00):")
valores_textil_normalizados = []
for i, cu in enumerate(costos_unitarios, 1):
    val_norm, fue_lim, val_orig = normalizar(cu['textil'], 'costo_textil')
    valores_textil_normalizados.append(val_norm)
    estado = "[CAPPED A 10.00]" if fue_lim else "[OK]"
    print(f"  OP {i}: ${val_orig:.4f} {estado} -> ${val_norm:.4f}")

promedio_textil = sum(valores_textil_normalizados) / len(valores_textil_normalizados)
print(f"\n  PROMEDIO TEXTIL = ({' + '.join([f'{v:.4f}' for v in valores_textil_normalizados])}) / {len(valores_textil_normalizados)}")
print(f"  PROMEDIO TEXTIL = {sum(valores_textil_normalizados):.4f} / {len(valores_textil_normalizados)}")
print(f"  PROMEDIO TEXTIL = ${promedio_textil:.4f}  [ESTE ES EL VALOR FINAL]")

# Normalizar Manufactura
print("\n\nCOSTO MANUFACTURA (rango: $0.05 - $10.00):")
valores_manufactura_normalizados = []
for i, cu in enumerate(costos_unitarios, 1):
    val_norm, fue_lim, val_orig = normalizar(cu['manufactura'], 'costo_manufactura')
    valores_manufactura_normalizados.append(val_norm)
    estado = "[CAPPED A 10.00]" if fue_lim else "[OK]"
    print(f"  OP {i}: ${val_orig:.4f} {estado} -> ${val_norm:.4f}")

promedio_manufactura = sum(valores_manufactura_normalizados) / len(valores_manufactura_normalizados)
print(f"\n  PROMEDIO MANUFACTURA = ({' + '.join([f'{v:.4f}' for v in valores_manufactura_normalizados])}) / {len(valores_manufactura_normalizados)}")
print(f"  PROMEDIO MANUFACTURA = {sum(valores_manufactura_normalizados):.4f} / {len(valores_manufactura_normalizados)}")
print(f"  PROMEDIO MANUFACTURA = ${promedio_manufactura:.4f}  [ESTE ES EL VALOR FINAL]")

# Normalizar Materia Prima
print("\n\nCOSTO MATERIA PRIMA (rango: $0.05 - $10.00):")
valores_materia_prima_normalizados = []
for i, cu in enumerate(costos_unitarios, 1):
    val_norm, fue_lim, val_orig = normalizar(cu['materia_prima'], 'costo_materia_prima')
    valores_materia_prima_normalizados.append(val_norm)
    estado = "[CAPPED A 10.00]" if fue_lim else "[OK]"
    print(f"  OP {i}: ${val_orig:.4f} {estado} -> ${val_norm:.4f}")

promedio_materia_prima = sum(valores_materia_prima_normalizados) / len(valores_materia_prima_normalizados)
print(f"\n  PROMEDIO MATERIA PRIMA = ({' + '.join([f'{v:.4f}' for v in valores_materia_prima_normalizados])}) / {len(valores_materia_prima_normalizados)}")
print(f"  PROMEDIO MATERIA PRIMA = {sum(valores_materia_prima_normalizados):.4f} / {len(valores_materia_prima_normalizados)}")
print(f"  PROMEDIO MATERIA PRIMA = ${promedio_materia_prima:.4f}  [ESTE ES EL VALOR FINAL]")

# Normalizar Avios
print("\n\nCOSTO AVIOS (rango: $0.05 - $10.00):")
valores_avios_normalizados = []
for i, cu in enumerate(costos_unitarios, 1):
    val_norm, fue_lim, val_orig = normalizar(cu['avios'], 'costo_avios')
    valores_avios_normalizados.append(val_norm)
    estado = "[CAPPED A 10.00]" if fue_lim else "[OK]"
    print(f"  OP {i}: ${val_orig:.4f} {estado} -> ${val_norm:.4f}")

promedio_avios = sum(valores_avios_normalizados) / len(valores_avios_normalizados)
print(f"\n  PROMEDIO AVIOS = ({' + '.join([f'{v:.4f}' for v in valores_avios_normalizados])}) / {len(valores_avios_normalizados)}")
print(f"  PROMEDIO AVIOS = {sum(valores_avios_normalizados):.4f} / {len(valores_avios_normalizados)}")
print(f"  PROMEDIO AVIOS = ${promedio_avios:.4f}  [ESTE ES EL VALOR FINAL]")

# ====== PASO 4: RESUMEN ======
print("\n\n" + "="*100)
print("RESUMEN - VALORES FINALES (DESPUES DE NORMALIZACION)")
print("="*100)

print(f"""
Costo Textil (normalizado):      ${promedio_textil:.4f}
Costo Manufactura (normalizado): ${promedio_manufactura:.4f}
Costo Materia Prima (normalizado): ${promedio_materia_prima:.4f}
Costo Avios (normalizado):       ${promedio_avios:.4f}

SUBTOTAL COSTOS DIRECTOS:        ${promedio_textil + promedio_manufactura + promedio_materia_prima + promedio_avios:.4f}
""")

print("\nESTOS SON LOS VALORES QUE DEVUELVE EL BACKEND AL API")
print("(Y que ves en el test_api_cotizacion.py como $7.4369 para Textil y $8.1734 para Manufactura)")

conn.close()
