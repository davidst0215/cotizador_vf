import asyncio
import sys
sys.path.insert(0, r'C:\Users\siste\smp-dev\backend\src')

from smp.database import TDVQueries
from smp.config import settings

async def main():
    tdv = TDVQueries()

    # Simular lo que hace utils.py
    costos_hist = await tdv.buscar_costos_estilo_especifico(
        codigo_estilo="18420",
        meses=24,
        version_calculo="FLUIDO"
    )

    print("=== RESPUESTA DE buscar_costos_estilo_especifico ===\n")
    for key, value in costos_hist.items():
        print(f"{key}: {value}")

    print("\n\n=== EXTRAYENDO VALORES COMO LO HACE utils.py ===\n")
    componentes_esperados = [
        "costo_textil",
        "costo_manufactura",
        "costo_avios",
        "costo_materia_prima",
        "costo_indirecto_fijo",
        "gasto_administracion",
        "gasto_ventas",
    ]

    costos_validados = {}
    for componente in componentes_esperados:
        valor = costos_hist.get(componente, 0)
        print(f"{componente}: {valor} (type: {type(valor).__name__})")
        costos_validados[componente] = valor

    total = sum(costos_validados.values())
    print(f"\nTotal de costos: ${total:.2f}")

asyncio.run(main())
