import asyncio
import sys
sys.path.insert(0, '/home/user/smp-dev/backend')

from src.smp.models import CotizacionInput, VersionCalculo
from src.smp.utils import CotizadorTDV

async def test():
    cotizador = CotizadorTDV()
    input_data = CotizacionInput(
        codigo_estilo="TEST-NUEVO-999",
        cliente_marca="LACOSTE",
        familia_producto="Camisa Casual",
        tipo_prenda="Camisa",
        categoria_lote="Lote Mediano",
        temporada="Primavera/Verano",
        esfuerzo_total=6,
        usuario="test",
        version_calculo=VersionCalculo.FLUIDO,
        wips_textiles=[],
        wips_manufactura=[]
    )
    
    try:
        result = await cotizador.procesar_cotizacion(input_data)
        print("SUCCESS:", result)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test())
