import psycopg2

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

conn = psycopg2.connect(**conn_params)
cursor = conn.cursor()

estilo = '18420'
schema = 'silver'

print("=== Version Calculo y Fecha Corrida ===")
cursor.execute(f"""
    SELECT DISTINCT version_calculo, fecha_corrida, COUNT(*) 
    FROM {schema}.costo_op_detalle
    WHERE estilo_propio = %s
    GROUP BY version_calculo, fecha_corrida
    ORDER BY fecha_corrida DESC
""", (estilo,))
print("Version Calculo | Fecha Corrida | Count")
for row in cursor.fetchall():
    print(f"{row[0]:20} | {row[1]} | {row[2]}")

print("\n=== Max Fecha Corrida en BD (por version) ===")
cursor.execute(f"""
    SELECT DISTINCT version_calculo, MAX(fecha_corrida) 
    FROM {schema}.costo_op_detalle
    GROUP BY version_calculo
    ORDER BY version_calculo
""")
for row in cursor.fetchall():
    print(f"{row[0]:20} | {row[1]}")

print("\n=== Max Fecha Facturacion en BD (por version) ===")
cursor.execute(f"""
    SELECT DISTINCT version_calculo, MAX(fecha_facturacion) 
    FROM {schema}.costo_op_detalle
    GROUP BY version_calculo
    ORDER BY version_calculo
""")
for row in cursor.fetchall():
    print(f"{row[0]:20} | {row[1]}")

print("\n=== Prendas Requeridas para estilo 18420 ===")
cursor.execute(f"""
    SELECT COUNT(*) as prendas_zero, 
           COUNT(*) as prendas_ok
    FROM {schema}.costo_op_detalle
    WHERE estilo_propio = %s
    AND prendas_requeridas > 0
""", (estilo,))
row = cursor.fetchone()
print(f"Con prendas > 0: {row[1]}")

cursor.close()
conn.close()
