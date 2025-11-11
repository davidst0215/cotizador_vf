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

schema = 'silver'

print("\n" + "="*80)
print("VALIDACION: FECHA_CORRIDA EN TABLA")
print("="*80)

# 1. Fechas de corrida disponibles
print("\n1. TODAS LAS FECHAS_CORRIDA DISPONIBLES (FLUIDO):")
cursor.execute(f"""
    SELECT DISTINCT fecha_corrida, COUNT(*) as registros
    FROM {schema}.costo_op_detalle
    WHERE version_calculo = 'FLUIDO'
    GROUP BY fecha_corrida
    ORDER BY fecha_corrida DESC
    LIMIT 10
""")
resultados = cursor.fetchall()
for fecha_corrida, count in resultados:
    print(f"  {fecha_corrida}: {count} registros")

# 2. Cuál es la MAX(fecha_corrida)
print("\n2. MAX(fecha_corrida) ACTUAL:")
cursor.execute(f"""
    SELECT MAX(fecha_corrida) FROM {schema}.costo_op_detalle
    WHERE version_calculo = 'FLUIDO'
""")
max_fecha_corrida = cursor.fetchone()[0]
print(f"  {max_fecha_corrida}")

# 3. ¿Está 18420 en la corrida más reciente?
print("\n3. ESTA ESTILO 18420 EN MAX(fecha_corrida)?:")
cursor.execute(f"""
    SELECT COUNT(*) FROM {schema}.costo_op_detalle
    WHERE estilo_propio = '18420'
      AND version_calculo = 'FLUIDO'
      AND fecha_corrida = (
        SELECT MAX(fecha_corrida)
        FROM {schema}.costo_op_detalle
        WHERE version_calculo = 'FLUIDO'
      )
""")
count_en_max = cursor.fetchone()[0]
print(f"  Registros: {count_en_max}")

if count_en_max == 0:
    print("  NO ESTA EN LA CORRIDA MAS RECIENTE!")
    
    # Ver en qué corrida SÍ está
    print("\n4. EN QUE fecha_corrida ESTA ESTILO 18420?:")
    cursor.execute(f"""
        SELECT DISTINCT fecha_corrida, COUNT(*) as registros
        FROM {schema}.costo_op_detalle
        WHERE estilo_propio = '18420'
          AND version_calculo = 'FLUIDO'
        GROUP BY fecha_corrida
        ORDER BY fecha_corrida DESC
    """)
    resultados = cursor.fetchall()
    for fecha_corrida, count in resultados:
        print(f"    {fecha_corrida}: {count} registros")
else:
    print(f"  SI ESTA ({count_en_max} registros)")

cursor.close()
conn.close()

print("\n" + "="*80 + "\n")
