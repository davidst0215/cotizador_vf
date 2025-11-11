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
    print("[*] Conectando a PostgreSQL...")
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    print("[OK] Conexión establecida\n")
    
    # Test schema silver
    print("=== Probando SCHEMA: silver ===")
    try:
        cursor.execute("SELECT COUNT(*) FROM silver.costo_op_detalle")
        count = cursor.fetchone()[0]
        print(f"[OK] silver.costo_op_detalle")
        print(f"     Total registros: {count:,}\n")
        
        # Get sample data
        cursor.execute("SELECT DISTINCT familia_de_productos FROM silver.costo_op_detalle LIMIT 3")
        familias = cursor.fetchall()
        print(f"     Familias (muestra):")
        for fam in familias:
            print(f"       - {fam[0]}")
        
        success = True
    except Exception as e:
        print(f"[ERROR] {str(e)}\n")
        success = False
    
    cursor.close()
    conn.close()
    
    if success:
        print("\n✅ ACCESO CONCEDIDO - Ahora sí tienes permisos!")
    else:
        print("\n❌ Aún SIN permisos - Solicita al admin que ejecute:")
        print("   GRANT SELECT ON ALL TABLES IN SCHEMA silver TO david;")
    
except Exception as e:
    print(f"[CONEXION ERROR] {e}")
