"""
Script para inspeccionar los certificados
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def inspect_cert_file(cert_path):
    """Inspecciona un archivo de certificado"""

    if not Path(cert_path).exists():
        print(f"[ERROR] Archivo no existe: {cert_path}")
        return

    print(f"\n[ARCHIVO] {cert_path}")
    stat = Path(cert_path).stat()
    print(f"  Tamanio: {stat.st_size} bytes")
    print(f"  Modificado: {datetime.fromtimestamp(stat.st_mtime)}")

    # Intentar leer como texto
    try:
        with open(cert_path, 'r') as f:
            contenido = f.read()

        # Verificar tipo de archivo
        if "-----BEGIN CERTIFICATE-----" in contenido:
            print(f"  Tipo: Certificado X.509 (PEM)")

            # Contar líneas
            lines = contenido.split('\n')
            print(f"  Lineas: {len(lines)}")

            # Encontrar Subject y Issuer si está en formato texto
            for line in lines:
                if 'CN=' in line or 'O=' in line or 'C=' in line:
                    print(f"  Info: {line.strip()[:80]}")

        elif "-----BEGIN PRIVATE KEY-----" in contenido or "-----BEGIN RSA PRIVATE KEY-----" in contenido:
            print(f"  Tipo: Clave privada (PEM)")

        elif "-----BEGIN RSA PRIVATE KEY-----" in contenido:
            print(f"  Tipo: Clave privada RSA (PEM)")

        else:
            print(f"  Tipo: Archivo PEM (otro formato)")

        print(f"  [OK] Archivo es legible")

    except Exception as e:
        print(f"  [ERROR] No se puede leer: {e}")

def main():
    print("="*70)
    print("INSPECCION DE CERTIFICADOS POSTGRESQL")
    print("="*70)

    pgsslcert = os.getenv('PGSSLCERT')
    pgsslkey = os.getenv('PGSSLKEY')
    pgsslrootcert = os.getenv('PGSSLROOTCERT')

    print("\n[CONFIGURACION]")
    print(f"  PGSSLCERT (certificado cliente): {pgsslcert}")
    print(f"  PGSSLKEY (clave privada): {pgsslkey}")
    print(f"  PGSSLROOTCERT (raiz CA): {pgsslrootcert}")

    # Inspeccionar cada certificado
    for cert_name, cert_path in [
        ("Cliente", pgsslcert),
        ("Clave Privada", pgsslkey),
        ("CA Raiz", pgsslrootcert)
    ]:
        if cert_path:
            print(f"\n[{cert_name.upper()}]")
            inspect_cert_file(cert_path)
        else:
            print(f"\n[{cert_name.upper()}]")
            print(f"  [VACIO] No configurado")

    # Diagnostico
    print("\n" + "="*70)
    print("DIAGNOSTICO")
    print("="*70)

    # Verificar si los archivos existen
    existe_cert = pgsslcert and Path(pgsslcert).exists()
    existe_key = pgsslkey and Path(pgsslkey).exists()
    existe_root = pgsslrootcert and Path(pgsslrootcert).exists()

    print(f"\n[EXISTENCIA]")
    print(f"  Certificado cliente: {'SI' if existe_cert else 'NO'}")
    print(f"  Clave privada: {'SI' if existe_key else 'NO'}")
    print(f"  CA Raiz: {'SI' if existe_root else 'NO'}")

    # Sugerencias
    print(f"\n[SUGERENCIAS]")

    if existe_root:
        print(f"  - El certificado raiz existe, pero podria no ser el correcto")
        print(f"  - El servidor PostgreSQL podria estar usando otro CA")
        print(f"  - Intenta con sslmode=prefer sin verificacion")

    if not existe_cert or not existe_key:
        print(f"  - Faltan certificados de cliente")
        print(f"  - Verifica que las rutas sean correctas")

    print(f"\n[SIGUIENTE PASO]")
    print(f"  Contacta al administrador de PostgreSQL para:")
    print(f"    1. Confirmar que el certificado raiz es correcto")
    print(f"    2. Obtener certificados actualizados si es necesario")
    print(f"    3. Configurar el CA correcto en el servidor")

if __name__ == "__main__":
    main()
