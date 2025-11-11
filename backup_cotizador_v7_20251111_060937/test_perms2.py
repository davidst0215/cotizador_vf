import psycopg2

def test_schema(schema_name):
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
        
        # Test 1: Contar registros
        cursor.execute(f"SELECT COUNT(*) FROM {schema_name}.costo_op_detalle")
        count = cursor.fetchone()[0]
        
        # Test 2: Obtener familias distintas
        cursor.execute(f"SELECT DISTINCT familia_de_productos FROM {schema_name}.costo_op_detalle LIMIT 5")
        familias = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        print(f"[OK] {schema_name}.costo_op_detalle")
        print(f"    - Total registros: {count:,}")
        print(f"    - Familias (muestra): {[f[0] for f in familias]}")
        return True
        
    except Exception as e:
        print(f"[ERROR] {schema_name}.costo_op_detalle: {str(e)[:80]}")
        return False

print("=== Validando Acceso a Tablas ===\n")
for schema in ['public', 'bronze', 'silver']:
    test_schema(schema)
    print()
