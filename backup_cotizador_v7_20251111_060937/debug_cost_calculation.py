"""
Simula exactamente lo que hace _procesar_costos_historicos_con_limites_previos
"""
import psycopg2
from datetime import datetime, timezone
from decimal import Decimal

# Configurar conexión
conn_params = {
    'host': '18.118.59.50',
    'port': 5432,
    'database': 'tdv',
    'user': 'david',
    'sslmode': 'verify-ca',
    'sslcert': 'C:/Users/siste/OneDrive/SAYA INVESTMENTS/calidad de venta/audios/piloto_abril/david (1).crt',
    'sslkey': 'C:/Users/siste/OneDrive/SAYA INVESTMENTS/calidad de venta/audios/piloto_abril/david.pk8',
    'sslrootcert': 'C:/Users/siste/OneDrive/SAYA INVESTMENTS/calidad de venta/audios/piloto_abril/root.crt',
}

# Rangos de seguridad (desde config.py)
RANGOS_SEGURIDAD = {
    "costo_textil": {"min": 0.05, "max": 10},
    "costo_manufactura": {"min": 0.05, "max": 10},
    "costo_materia_prima": {"min": 0.05, "max": 10},
    "costo_indirecto_fijo": {"min": 0.05, "max": 10},
    "gasto_administracion": {"min": 0.05, "max": 10},
    "gasto_ventas": {"min": 0.05, "max": 10},
    "costo_avios": {"min": 0.05, "max": 10},
}

def safe_float(val, default):
    return float(val) if isinstance(val, (int, float, Decimal)) else default

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

estilo = '18420'
version = 'FLUIDO'
schema = 'silver'

print(f"=== Simulación de _procesar_costos_historicos_con_limites_previos ===\n")

# Obtener los mismos 5 registros que el backend usa
cursor.execute(f"""
    SELECT
        costo_textil, costo_manufactura, costo_avios,
        costo_materia_prima, costo_indirecto_fijo,
        gasto_administracion, gasto_ventas,
        prendas_requeridas, fecha_facturacion
    FROM {schema}.costo_op_detalle
    WHERE estilo_propio = %s
      AND version_calculo = %s
      AND fecha_corrida = (
        SELECT MAX(fecha_corrida)
        FROM {schema}.costo_op_detalle
        WHERE estilo_propio = %s AND version_calculo = %s
      )
      AND prendas_requeridas > 0
    ORDER BY fecha_facturacion DESC
    LIMIT 5
""", (estilo, version, estilo, version))

records = cursor.fetchall()
print(f"Registros encontrados: {len(records)}\n")

print("RAW RECORDS FROM DATABASE:")
for idx, row in enumerate(records):
    print(f"  Record {idx+1}: {row}")
print()

# Convertir a dict format como lo hace el backend
recs = []
for row in records:
    rec = {
        'costo_textil': row[0],
        'costo_manufactura': row[1],
        'costo_avios': row[2],
        'costo_materia_prima': row[3],
        'costo_indirecto_fijo': row[4],
        'gasto_administracion': row[5],
        'gasto_ventas': row[6],
        'prendas_requeridas': row[7],
        'fecha_facturacion': row[8],
    }
    print(f"Dict created: costo_textil={rec['costo_textil']}, prendas={rec['prendas_requeridas']}")
    recs.append(rec)

# Calcular pesos (con timezone aware datetime)
now = datetime.now(timezone.utc)
weights = [
    0.1
    if not isinstance(rec.get("fecha_facturacion"), datetime)
    else max(0.1, 1.0 - (now - rec["fecha_facturacion"]).days / 365.0)
    for rec in recs
]
sum_weights = sum(weights) or 1e-10

print(f"Pesos calculados: {weights}")
print(f"Suma de pesos: {sum_weights}\n")

cols = [
    "costo_textil",
    "costo_manufactura",
    "costo_avios",
    "costo_materia_prima",
    "costo_indirecto_fijo",
    "gasto_administracion",
    "gasto_ventas",
]

print("=" * 120)
print("PASO 1: DIVIDIR POR PRENDAS REQUERIDAS (convertir a costo por unidad)")
print("=" * 120)

for col in cols:
    print(f"\n{col}:")
    print(f"  {'Idx':<3} {'Valor Total':<15} {'Prendas':<10} {'Por Unidad (antes clip)':<20}")
    print(f"  {'-'*3} {'-'*15} {'-'*10} {'-'*20}")

    vals_per_unit = []
    for idx, rec in enumerate(recs):
        total_cost = safe_float(rec.get(col, 0), 0)
        prendas = max(1.0, safe_float(rec.get("prendas_requeridas", 1), 1))
        per_unit = total_cost / prendas
        vals_per_unit.append(per_unit)
        print(f"  {idx+1:<3} ${total_cost:<14.2f} {prendas:<10.0f} ${per_unit:<19.4f}")

    # Ahora aplicar clipping
    print(f"\n  Rango de seguridad: ${RANGOS_SEGURIDAD[col]['min']} - ${RANGOS_SEGURIDAD[col]['max']}")
    print(f"  {'Idx':<3} {'Antes Clip':<20} {'Después Clip':<20} {'¿Ajustado?':<15}")
    print(f"  {'-'*3} {'-'*20} {'-'*20} {'-'*15}")

    min_val = RANGOS_SEGURIDAD[col]["min"]
    max_val = RANGOS_SEGURIDAD[col]["max"]
    adjustments = 0

    for idx, val in enumerate(vals_per_unit):
        clipped = max(min_val, min(max_val, val))
        was_adjusted = "SÍ" if clipped != val else "NO"
        if clipped != val:
            adjustments += 1
        print(f"  {idx+1:<3} ${val:<19.4f} ${clipped:<19.4f} {was_adjusted:<15}")
        vals_per_unit[idx] = clipped

    # Calcular promedio ponderado
    weighted_avg = sum(v * w for v, w in zip(vals_per_unit, weights)) / sum_weights
    print(f"\n  [OK] Promedio ponderado: ${weighted_avg:.4f}")
    print(f"  [STATS] Total ajustados: {adjustments}")

cursor.close()
conn.close()
