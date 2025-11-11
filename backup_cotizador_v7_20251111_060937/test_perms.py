import psycopg2
import os

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
    
    # List all schemas
    print("=== SCHEMAS disponibles ===")
    cursor.execute("""
        SELECT schema_name FROM information_schema.schemata 
        WHERE schema_name NOT LIKE 'pg_%' AND schema_name != 'information_schema'
        ORDER BY schema_name
    """)
    schemas = cursor.fetchall()
    for schema in schemas:
        print(f"  - {schema[0]}")
    
    # Test schema public
    print("\n=== Probando SCHEMA: public ===")
    try:
        cursor.execute("SELECT COUNT(*) FROM public.costo_op_detalle LIMIT 1")
        result = cursor.fetchone()
        print(f"[OK] public.costo_op_detalle: {result[0]} registros")
    except Exception as e:
        print(f"[ERROR] public.costo_op_detalle: {str(e)[:100]}")
    
    # Test schema silver
    print("\n=== Probando SCHEMA: silver ===")
    try:
        cursor.execute("SELECT COUNT(*) FROM silver.costo_op_detalle LIMIT 1")
        result = cursor.fetchone()
        print(f"[OK] silver.costo_op_detalle: {result[0]} registros")
    except Exception as e:
        print(f"[ERROR] silver.costo_op_detalle: {str(e)[:100]}")
    
    # Test schema bronze
    print("\n=== Probando SCHEMA: bronze ===")
    try:
        cursor.execute("SELECT COUNT(*) FROM bronze.costo_op_detalle LIMIT 1")
        result = cursor.fetchone()
        print(f"[OK] bronze.costo_op_detalle: {result[0]} registros")
    except Exception as e:
        print(f"[ERROR] bronze.costo_op_detalle: {str(e)[:100]}")
    
    cursor.close()
    conn.close()
    print("\n[CONEXION OK]")
    
except Exception as e:
    print(f"[CONEXION ERROR] {e}")
