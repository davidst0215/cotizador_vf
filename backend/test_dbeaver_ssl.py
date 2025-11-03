"""
Script para probar conexion con sslmode=verify-ca (como DBeaver)
"""
import psycopg2
from pathlib import Path
import os
import ssl
from dotenv import load_dotenv

load_dotenv()

def test_verify_ca():
    """
    Intenta conexion con sslmode=verify-ca (como DBeaver)
    """

    print("\n" + "="*70)
    print("INTENTANDO CONEXION CON sslmode=verify-ca (COMO DBEAVER)")
    print("="*70)

    try:
        cert_path = os.getenv('PGSSLCERT')
        key_path = os.getenv('PGSSLKEY')
        root_cert_path = os.getenv('PGSSLROOTCERT')

        print("\n[VERIFICANDO ARCHIVOS]")
        print(f"  Certificado cliente: {Path(cert_path).name if cert_path else 'NO CONFIG'}")
        print(f"    Existe: {Path(cert_path).exists() if cert_path else 'N/A'}")

        print(f"  Clave privada: {Path(key_path).name if key_path else 'NO CONFIG'}")
        print(f"    Existe: {Path(key_path).exists() if key_path else 'N/A'}")

        print(f"  CA Root: {Path(root_cert_path).name if root_cert_path else 'NO CONFIG'}")
        print(f"    Existe: {Path(root_cert_path).exists() if root_cert_path else 'N/A'}")

        # Configurar parametros exactamente como lo hace DBeaver
        connection_params = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT')),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'sslmode': 'verify-ca',  # EXACTO COMO DBEAVER
            'sslcert': cert_path,
            'sslkey': key_path,
            'sslrootcert': root_cert_path,
        }

        print(f"\n[PARAMETROS DE CONEXION]")
        print(f"  host: {connection_params['host']}")
        print(f"  port: {connection_params['port']}")
        print(f"  database: {connection_params['database']}")
        print(f"  user: {connection_params['user']}")
        print(f"  sslmode: {connection_params['sslmode']}")
        print(f"  sslcert: {Path(connection_params['sslcert']).name if connection_params.get('sslcert') else 'NO'}")
        print(f"  sslkey: {Path(connection_params['sslkey']).name if connection_params.get('sslkey') else 'NO'}")
        print(f"  sslrootcert: {Path(connection_params['sslrootcert']).name if connection_params.get('sslrootcert') else 'NO'}")

        print(f"\n[INTENTANDO CONECTAR]...")
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()

        cursor.execute("SELECT version();")
        version = cursor.fetchone()

        print(f"\n[EXITO] CONEXION ESTABLECIDA!")
        print(f"\nPostgreSQL Version:")
        print(f"  {version[0]}")

        # Listar todas las bases de datos
        cursor.execute("""
            SELECT datname FROM pg_database
            WHERE datistemplate = false
            ORDER BY datname;
        """)

        databases = cursor.fetchall()
        print(f"\n[BASES DE DATOS]")
        for db in databases:
            print(f"  - {db[0]}")

        # Listar tablas en la BD actual
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        print(f"\n[TABLAS EN SCHEMA 'public']: {len(tables)} tablas")
        for table in tables:
            print(f"  - {table[0]}")

        # Contar registros en tablas importantes
        important_tables = ['costo_op_detalle', 'historial_estilos', 'productos']

        print(f"\n[DATOS EN TABLAS IMPORTANTES]")
        for tabla in important_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {tabla};")
                count = cursor.fetchone()[0]
                print(f"  {tabla}: {count} registros")
            except Exception as e:
                print(f"  {tabla}: [ERROR] {str(e)[:50]}")

        cursor.close()
        conn.close()

        print(f"\n[OK] LA CONEXION FUNCIONA CORRECTAMENTE!")
        return True

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}")
        print(f"  Mensaje: {str(e)}")

        # Diagnostico detallado
        if "certificate verify failed" in str(e):
            print(f"\n[DIAGNOSTICO]")
            print(f"  El certificado raiz NO puede verificar el servidor")
            print(f"  Compara la configuracion con DBeaver:")
            print(f"    - ¿SSL Mode = verify-ca?")
            print(f"    - ¿El certificado raiz es el mismo?")
            print(f"    - ¿Los paths son identicos?")

        return False

if __name__ == "__main__":
    exito = test_verify_ca()

    if exito:
        print("\n" + "="*70)
        print("SIGUIENTE PASO")
        print("="*70)
        print("""
Ahora puedes:
  1. Actualizar .env con sslmode=verify-ca
  2. Ejecutar los scripts de SMP con confianza
  3. Usar la base de datos para desarrollo y pruebas
        """)
    else:
        print("\n[FALLO] Verifica la configuracion SSL en DBeaver vs los parametros")
