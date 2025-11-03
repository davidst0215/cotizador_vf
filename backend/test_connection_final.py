"""
Script para probar conexion - version final con soluciones practicas
"""
import psycopg2
from pathlib import Path
import os

from dotenv import load_dotenv
load_dotenv()

def test_con_sslmode_pragmatico():
    """
    Intenta conexion con diferentes enfoques pragmaticos
    """

    print("\n" + "="*70)
    print("INTENTANDO CONEXION CON ENFOQUE PRAGMATICO")
    print("="*70)

    # Opcion 1: Con certificados pero modo "prefer" (menos estricto)
    print("\n[OPCION 1] sslmode=prefer + certificados (menos estricto)")
    print("-"*70)

    try:
        connection_params = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT')),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'sslmode': 'prefer',  # Menos estricto que "require"
            'sslcert': os.getenv('PGSSLCERT'),
            'sslkey': os.getenv('PGSSLKEY'),
            # NO incluimos sslrootcert para que NO verifique el CA
        }

        print(f"[PARAMS]")
        for k, v in connection_params.items():
            if v and isinstance(v, str) and (k == 'sslcert' or k == 'sslkey'):
                print(f"  {k}: {Path(v).name}")
            else:
                print(f"  {k}: {v}")

        print(f"\n[CONECTANDO]...")
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()

        cursor.execute("SELECT version();")
        version = cursor.fetchone()

        print(f"\n[EXITO] CONEXION ESTABLECIDA!")
        print(f"\nPostgreSQL Version:")
        print(f"  {version[0]}")

        # Listar tablas
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        print(f"\nTablas en schema 'public': {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")

        # Listar esquema de tablas importantes
        for tabla in ['costo_op_detalle', 'historial_estilos']:
            cursor.execute(f"""
                SELECT COUNT(*) FROM {tabla};
            """)
            count = cursor.fetchone()[0]
            print(f"\n[TABLA] {tabla}: {count} registros")

        cursor.close()
        conn.close()

        print(f"\n[OK] La conexion funciona!")
        return True

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {str(e)[:100]}")
        return False

if __name__ == "__main__":
    exito = test_con_sslmode_pragmatico()

    if exito:
        print("\n" + "="*70)
        print("RECOMENDACION PARA PRODUCCION")
        print("="*70)
        print("""
La conexion funciona con sslmode=prefer.

IMPORTANTE:
  - Esta configuracion es SEGURA para desarrollo local
  - Para PRODUCCION, debes:
    1. Obtener el certificado raiz correcto del administrador
    2. Usar sslmode=verify-ca o verify-full
    3. Verificar la cadena de certificados

Actualiza el .env con:
  PGSSLMODE=prefer
  # Y mantén los certificados de cliente (PGSSLCERT, PGSSLKEY)
  # Pero NO uses PGSSLROOTCERT en desarrollo
        """)
    else:
        print("\n[FALLO] Intenta contactar al administrador de PostgreSQL")
