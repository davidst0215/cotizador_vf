"""
Extraer el certificado del servidor PostgreSQL para comparacion
"""
import ssl
import socket
from pathlib import Path

def extract_server_certificate():
    """
    Conecta al servidor y extrae su certificado para comparacion
    """

    print("\n" + "="*70)
    print("EXTRAYENDO CERTIFICADO DEL SERVIDOR")
    print("="*70)

    host = '18.118.59.50'
    port = 5432

    print(f"\n[CONECTANDO A] {host}:{port}")

    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # No verificar por ahora

        with socket.create_connection((host, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                # Obtener certificado binario
                try:
                    cert = ssock.getpeercert(binary_form=True)
                except:
                    cert = None

                if cert:
                    print(f"\n[EXITO] Certificado extraido: {len(cert)} bytes")

                    # Guardar el certificado
                    cert_output = Path("C:/Users/siste/smp-dev/backend/server_cert.der")
                    with open(cert_output, 'wb') as f:
                        f.write(cert)

                    print(f"[GUARDADO] {cert_output}")

                    # Intentar convertir a PEM
                    import base64
                    pem_output = Path("C:/Users/siste/smp-dev/backend/server_cert.pem")
                    with open(pem_output, 'w') as f:
                        f.write("-----BEGIN CERTIFICATE-----\n")
                        f.write(base64.b64encode(cert).decode() + "\n")
                        f.write("-----END CERTIFICATE-----\n")

                    print(f"[CONVERTIDO] {pem_output}")

                    # Mostrar info del certificado
                    cert_info = ssock.getpeercert()
                    print(f"\n[INFO DEL CERTIFICADO]")
                    for key, value in cert_info.items():
                        if key == 'subject':
                            print(f"  Subject: {value}")
                        elif key == 'issuer':
                            print(f"  Issuer: {value}")
                        elif key == 'version':
                            print(f"  Version: {value}")
                        elif key == 'serialNumber':
                            print(f"  Serial: {value}")
                        elif key == 'notBefore':
                            print(f"  Not Before: {value}")
                        elif key == 'notAfter':
                            print(f"  Not After: {value}")

                    return True
                else:
                    print(f"[ERROR] No se pudo obtener el certificado")
                    return False

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {str(e)[:80]}")
        return False

if __name__ == "__main__":
    extract_server_certificate()

    print(f"\n[SIGUIENTE]")
    print(f"  Ahora puedes comparar el certificado del servidor con root.crt")
    print(f"  Archivos creados: server_cert.pem, server_cert.der")
