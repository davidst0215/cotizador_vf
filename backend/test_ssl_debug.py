"""
Script con debug detallado del handshake SSL
"""
import psycopg2
import ssl
import logging
from pathlib import Path
import os
from dotenv import load_dotenv

# Habilitar debug para SSL
logging.basicConfig(level=logging.DEBUG)
ssl_logger = logging.getLogger('ssl')
ssl_logger.setLevel(logging.DEBUG)

load_dotenv()

def test_with_debug():
    """
    Intenta conexion con debug SSL habilitado
    """

    print("\n" + "="*70)
    print("PRUEBA CON DEBUG SSL HABILITADO")
    print("="*70)

    cert_path = os.getenv('PGSSLCERT')
    key_path = os.getenv('PGSSLKEY')
    root_cert_path = os.getenv('PGSSLROOTCERT')

    print(f"\n[ARCHIVOS]")
    print(f"  Certificado: {Path(cert_path).exists()} ({Path(cert_path).name})")
    print(f"  Clave: {Path(key_path).exists()} ({Path(key_path).name})")
    print(f"  CA Root: {Path(root_cert_path).exists()} ({Path(root_cert_path).name})")

    try:
        print(f"\n[INTENTANDO CONECTAR CON verify-ca Y DEBUG]...\n")

        connection_params = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT')),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'sslmode': 'verify-ca',
            'sslcert': cert_path,
            'sslkey': key_path,
            'sslrootcert': root_cert_path,
        }

        conn = psycopg2.connect(**connection_params)
        print("[EXITO] Conexion establecida")
        conn.close()

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}")
        print(f"  {str(e)}")

        # Intentar sin verificacion
        print(f"\n\n[INTENTANDO CON sslmode=require Y DEBUG]...\n")

        try:
            connection_params['sslmode'] = 'require'
            # Quitar sslrootcert para ver si es el problema
            del connection_params['sslrootcert']

            conn = psycopg2.connect(**connection_params)
            print("[EXITO] Conexion establecida sin verificacion")
            conn.close()

        except Exception as e2:
            print(f"\n[ERROR] {type(e2).__name__}")
            print(f"  {str(e2)}")

if __name__ == "__main__":
    test_with_debug()
