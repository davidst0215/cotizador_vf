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

try:
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()

    estilo = '18420'
    version = 'FLUIDO'
    schema = 'silver'

    print(f"=== Registros históricos para estilo {estilo} (versión {version}) ===\n")

    # Query the same 5 records that the backend would use
    cursor.execute(f"""
        SELECT
            cod_ordpro, estilo_propio, version_calculo,
            costo_textil, costo_manufactura, costo_avios,
            costo_materia_prima, costo_indirecto_fijo,
            gasto_administracion, gasto_ventas,
            prendas_requeridas, fecha_facturacion, fecha_corrida
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
    print(f"Encontrados: {len(records)} registros\n")

    if records:
        print("Detalles de costos por registro:")
        print("-" * 100)
        print(f"{'#':<3} {'Prendas':<10} {'Textil':<12} {'Manufactura':<12} {'Avios':<12} {'Mat. Prima':<12} {'Ind. Fijo':<12}")
        print("-" * 100)

        for idx, row in enumerate(records, 1):
            cod_ordpro = row[0]
            costo_textil = row[3]
            costo_manufactura = row[4]
            costo_avios = row[5]
            costo_materia_prima = row[6]
            costo_indirecto_fijo = row[7]
            gasto_administracion = row[8]
            gasto_ventas = row[9]
            prendas_requeridas = row[10]
            fecha_facturacion = row[11]
            fecha_corrida = row[12]

            print(f"{idx:<3} {prendas_requeridas:<10} ${costo_textil:<11.4f} ${costo_manufactura:<11.4f} ${costo_avios:<11.4f} ${costo_materia_prima:<11.4f} ${costo_indirecto_fijo:<11.4f}")

        print("-" * 100)

        # Calculate totals and averages
        avg_textil = sum(r[3] for r in records) / len(records)
        avg_manufactura = sum(r[4] for r in records) / len(records)
        avg_avios = sum(r[5] for r in records) / len(records)
        avg_materia_prima = sum(r[6] for r in records) / len(records)
        avg_indirecto_fijo = sum(r[7] for r in records) / len(records)
        avg_administracion = sum(r[8] for r in records) / len(records)
        avg_ventas = sum(r[9] for r in records) / len(records)

        print(f"\nPromedios simples (5 registros):")
        print(f"  Textil:           ${avg_textil:.4f}")
        print(f"  Manufactura:      ${avg_manufactura:.4f}")
        print(f"  Avios:            ${avg_avios:.4f}")
        print(f"  Materia Prima:    ${avg_materia_prima:.4f}")
        print(f"  Indirecto Fijo:   ${avg_indirecto_fijo:.4f}")
        print(f"  Administración:   ${avg_administracion:.4f}")
        print(f"  Ventas:           ${avg_ventas:.4f}")

        costo_total = (avg_textil + avg_manufactura + avg_avios +
                      avg_materia_prima + avg_indirecto_fijo +
                      avg_administracion + avg_ventas)
        print(f"\nCosto Total (suma de promedios): ${costo_total:.4f}")

    else:
        print("❌ No se encontraron registros")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
