#!/usr/bin/env python
import psycopg2
from psycopg2.extras import DictCursor

# Conexión
conn = psycopg2.connect(
    dbname="tdv",
    user="david",
    host="18.118.59.50",
    port=5432,
    sslmode="verify-ca",
    sslcert=r"C:\Users\siste\OneDrive\SAYA INVESTMENTS\calidad de venta\audios\piloto_abril\david (1).crt",
    sslkey=r"C:\Users\siste\OneDrive\SAYA INVESTMENTS\calidad de venta\audios\piloto_abril\david.pk8",
    sslrootcert=r"C:\Users\siste\OneDrive\SAYA INVESTMENTS\calidad de venta\audios\piloto_abril\root.crt"
)

cur = conn.cursor(cursor_factory=DictCursor)

# 1. Ver estructura de la tabla
print("=== ESTRUCTURA DE resumen_wip_por_prenda ===\n")
cur.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'resumen_wip_por_prenda'
    ORDER BY ordinal_position;
""")

for row in cur.fetchall():
    print(f"{row['column_name']:30} | {row['data_type']:15} | Nullable: {row['is_nullable']}")

# 2. Ver marcas disponibles
print("\n\n=== MARCAS DISPONIBLES ===\n")
cur.execute("""
    SELECT DISTINCT marca FROM silver.resumen_wip_por_prenda
    WHERE marca IS NOT NULL
    ORDER BY marca
    LIMIT 30;
""")

for row in cur.fetchall():
    print(f"  - {row['marca']}")

# 3. Ver sample de datos
print("\n\n=== MUESTRA DE DATOS (5 registros) ===\n")
cur.execute("""
    SELECT * FROM silver.resumen_wip_por_prenda LIMIT 5;
""")

rows = cur.fetchall()
if rows:
    first_row = rows[0]
    # Headers
    headers = list(first_row.keys())
    print(" | ".join(f"{h:20}" for h in headers))
    print("-" * 200)
    # Data
    for row in rows:
        print(" | ".join(f"{str(v)[:20]:20}" for v in row.values()))

cur.close()
conn.close()
print("\n✅ Done!")
