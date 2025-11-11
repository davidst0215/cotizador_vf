#!/usr/bin/env python3
"""Test de API para verificar que la normalizacion esta funcionando en el backend"""

import requests
import json

API_URL = "http://localhost:8000"

print("="*80)
print("TEST DE API - VERIFICACION DE NORMALIZACION EN BACKEND")
print("="*80)

# Parámetros del test
payload = {
    "codigo_estilo": "18420",
    "usuario": "Test Debug",
    "cliente_marca": "MONTAIGNE HONG KONG LIMITED",
    "tipo_prenda": "POLO BOX",
    "familia_producto": "Polos",
    "categoria_lote": "Lote Mediano",
    "cantidad_prendas": 750,
    "temporada": "Todas",
    "version_calculo": "FLUIDO"
}

print("\nPARÁMETROS DE COTIZACIÓN:")
print(json.dumps(payload, indent=2, ensure_ascii=False))

print("\n" + "="*80)
print("ENVIANDO SOLICITUD AL BACKEND...")
print("="*80)

try:
    response = requests.post(
        f"{API_URL}/cotizar",
        json=payload,
        timeout=30
    )

    if response.status_code == 200:
        resultado = response.json()

        print("\n[RESPUESTA DEL BACKEND - EXITOSA]")
        print(f"Status Code: {response.status_code}")

        # Extraer datos importantes
        print("\n" + "="*80)
        print("DETALLES DE LA COTIZACION")
        print("="*80)

        print(f"\nID Cotizacion: {resultado.get('id_cotizacion')}")
        print(f"Estilo: {resultado.get('codigo_estilo')}")
        print(f"Marca: {resultado.get('cliente_marca')}")
        print(f"Tipo Prenda: {resultado.get('tipo_prenda')}")
        print(f"Cantidad: {resultado.get('cantidad_prendas')} prendas")

        print(f"\nPrecio Final: ${resultado.get('precio_final'):.2f}")

        # Mostrar componentes
        if 'componentes' in resultado:
            print("\n[COMPONENTES DE COSTO]")
            for comp in resultado['componentes']:
                print(f"  {comp['nombre']:30} ${comp['costo_unitario']:10.4f}")
                if comp.get('detalles'):
                    if comp['detalles'].get('fue_ajustado'):
                        print(f"    (AJUSTADO de ${comp['detalles'].get('valor_original'):.4f})")

        # Alertas
        if resultado.get('alertas'):
            print("\n[ALERTAS/NOTAS]")
            for alerta in resultado['alertas'][:5]:  # Mostrar primeras 5
                print(f"  - {alerta}")

        print("\n" + "="*80)
        print("RESPUESTA COMPLETA JSON")
        print("="*80)
        print(json.dumps(resultado, indent=2, ensure_ascii=False, default=str))

    else:
        print(f"\n[ERROR] Status Code: {response.status_code}")
        print(f"Respuesta: {response.text}")

except requests.exceptions.ConnectionError:
    print("\n[ERROR] No se pudo conectar al backend en http://localhost:8000")
    print("Asegúrate de que el backend esté corriendo:")
    print("  cd C:\\Users\\siste\\backup_cotizadortdv_v7\\backend")
    print("  uvicorn src.smp.main:app --host 0.0.0.0 --port 8000")
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")

print("\n[COMPLETO]\n")
