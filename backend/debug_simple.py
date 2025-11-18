"""
Simple debug script using psycopg2 to inspect database values.
"""

import psycopg2
from src.smp.config import settings

def main():
    try:
        # Connect to database
        conn = psycopg2.connect(
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
            host=settings.db_host,
            port=settings.db_port
        )

        cursor = conn.cursor()

        # Query 1: Get OPs for style 18420
        print("=" * 80)
        print("QUERY 1: OPs for style 18420")
        print("=" * 80)

        cursor.execute(f"""
        SELECT
            cod_ordpro,
            cliente,
            tipo_de_producto,
            version_calculo,
            LENGTH(TRIM(cliente)) as cliente_len,
            LENGTH(TRIM(tipo_de_producto)) as tipo_len
        FROM costeo_cotizacion.costo_op_detalle
        WHERE codigo_estilo = 18420
        ORDER BY cod_ordpro
        """)

        rows = cursor.fetchall()
        cliente_value = None
        tipo_value = None

        for row in rows:
            cod_ordpro, cliente, tipo_de_producto, version_calculo, cliente_len, tipo_len = row
            print(f"OP: {cod_ordpro}")
            print(f"  cliente: '{cliente}' (len={cliente_len})")
            print(f"  tipo_de_producto: '{tipo_de_producto}' (len={tipo_len})")
            print(f"  version_calculo: '{version_calculo}'")
            print()

            if cliente_value is None:
                cliente_value = cliente
                tipo_value = tipo_de_producto

        if cliente_value:
            # Query 2: Search by ILIKE
            print("=" * 80)
            print(f"QUERY 2: Search by cliente ILIKE '%{cliente_value.strip()}%'")
            print("=" * 80)

            cursor.execute(f"""
            SELECT cod_ordpro, cliente, tipo_de_producto
            FROM costeo_cotizacion.costo_op_detalle
            WHERE cliente ILIKE %s
            ORDER BY cod_ordpro
            LIMIT 10
            """, (f"%{cliente_value.strip()}%",))

            rows2 = cursor.fetchall()
            print(f"Found {len(rows2)} OPs")
            for row in rows2:
                print(f"  OP: {row[0]}, cliente: {row[1]}, tipo: {row[2]}")

            # Query 3: Search with exact TRIM UPPER
            print()
            print("=" * 80)
            print(f"QUERY 3: Search by TRIM(UPPER(cliente)) = TRIM(UPPER(%s))")
            print("=" * 80)

            cursor.execute(f"""
            SELECT cod_ordpro, cliente, tipo_de_producto
            FROM costeo_cotizacion.costo_op_detalle
            WHERE TRIM(UPPER(cliente)) = TRIM(UPPER(%s))
            ORDER BY cod_ordpro
            LIMIT 10
            """, (cliente_value,))

            rows3 = cursor.fetchall()
            print(f"Found {len(rows3)} OPs")
            for row in rows3:
                print(f"  OP: {row[0]}")

            # Query 4: All unique clientes with MONTAIGNE
            print()
            print("=" * 80)
            print("QUERY 4: All unique clientes with 'MONTAIGNE'")
            print("=" * 80)

            cursor.execute(f"""
            SELECT DISTINCT cliente
            FROM costeo_cotizacion.costo_op_detalle
            WHERE cliente ILIKE '%MONTAIGNE%'
            ORDER BY cliente
            """)

            rows4 = cursor.fetchall()
            print(f"Found {len(rows4)} unique clientes:")
            for row in rows4:
                print(f"  '{row[0]}'")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
