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

# Verificar si está en historial_estilos
print("=== Historial Estilos ===")
cursor.execute(f"""
    SELECT codigo_estilo, COUNT(*) FROM {schema}.historial_estilos 
    WHERE codigo_estilo = %s 
    GROUP BY codigo_estilo
""", (estilo,))
result = cursor.fetchone()
print(f"Estilo {estilo} en historial: {result}")

# Contar registros en costo_op_detalle para este estilo
print("\n=== Costo Op Detalle ===")
cursor.execute(f"""
    SELECT COUNT(*), 
           COUNT(DISTINCT estilo_propio),
           MIN(fecha_facturacion), 
           MAX(fecha_facturacion)
    FROM {schema}.costo_op_detalle
    WHERE estilo_propio = %s
""", (estilo,))
result = cursor.fetchone()
print(f"Registros para estilo {estilo}: {result[0]}")
print(f"Estilo encontrado: {result[1]}")
print(f"Rango fechas: {result[2]} a {result[3]}")

# Ver los primeros registros
print(f"\n=== Primeros registros (últimos 3) ===")
cursor.execute(f"""
    SELECT cod_ordpro, estilo_propio, familia_de_productos, costo_textil, 
           costo_manufactura, fecha_facturacion
    FROM {schema}.costo_op_detalle
    WHERE estilo_propio = %s
    ORDER BY fecha_facturacion DESC
    LIMIT 3
""", (estilo,))
for row in cursor.fetchall():
    print(f"  {row}")

cursor.close()
conn.close()
