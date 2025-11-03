"""
Test the FULL flow through procesar_cotizacion to see diagnostic output
"""
import asyncio
import sys
sys.path.insert(0, r'C:\Users\siste\smp-dev\backend\src')

from smp.utils import CotizadorTDV
from smp.models import CotizacionInput, VersionCalculo
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def main():
    cotizador = CotizadorTDV()

    # Crear input como si viniera del frontend
    input_data = CotizacionInput(
        cliente_marca="TEST MARCA",
        temporada="SS2024",
        categoria_lote="Lote Mediano",
        familia_producto="Pantalón",
        tipo_prenda="Pantalón",
        codigo_estilo="18420",
        usuario="test_user",
        version_calculo=VersionCalculo.FLUIDO
    )

    print("\n" + "="*100, flush=True)
    print("INICIANDO FULL FLOW TEST para estilo 18420", flush=True)
    print("="*100 + "\n", flush=True)

    try:
        # Esto dispara el full flow a través de procesar_cotizacion -> _procesar_estilo_recurrente_mejorado
        resultado = await cotizador.procesar_cotizacion(input_data)

        print("\n" + "="*100, flush=True)
        print("RESULTADO DE COTIZACION:", flush=True)
        print("="*100, flush=True)
        print(f"Precio Final: ${resultado.precio_final:.2f}", flush=True)
        print(f"Costo Base Total: ${resultado.costo_base_total:.2f}", flush=True)
        print(f"\nComponentes (lista en respuesta):", flush=True)
        for comp in resultado.componentes:
            print(f"  {comp.nombre}: ${comp.costo_unitario:.2f} (fuente: {comp.fuente})", flush=True)

    except Exception as e:
        print(f"ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()

asyncio.run(main())
