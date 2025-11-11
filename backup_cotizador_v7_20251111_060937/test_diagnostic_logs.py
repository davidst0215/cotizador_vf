"""
Test script para ver los logs diagnósticos
"""
import asyncio
import sys
sys.path.insert(0, r'C:\Users\siste\smp-dev\backend\src')

from smp.database import TDVQueries
from smp.config import settings
import logging

# Configurar logging para ver todo
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    tdv = TDVQueries()

    logger.info("=" * 100)
    logger.info("INICIANDO TEST: Llamando buscar_costos_estilo_especifico para estilo 18420")
    logger.info("=" * 100)

    try:
        costos_hist = await tdv.buscar_costos_estilo_especifico(
            codigo_estilo="18420",
            meses=24,
            version_calculo="FLUIDO"
        )

        logger.info("\n" + "=" * 100)
        logger.info("RESPUESTA RECIBIDA - Mostrando todos los valores:")
        logger.info("=" * 100)

        componentes = [
            "costo_textil",
            "costo_manufactura",
            "costo_avios",
            "costo_materia_prima",
            "costo_indirecto_fijo",
            "gasto_administracion",
            "gasto_ventas",
        ]

        for comp in componentes:
            val = costos_hist.get(comp)
            logger.info(f"\n{comp}:")
            logger.info(f"  Valor: {val}")
            logger.info(f"  Tipo: {type(val).__name__}")
            logger.info(f"  Es None: {val is None}")
            logger.info(f"  Es <= 0: {val <= 0 if val is not None else 'N/A'}")
            logger.info(f"  Float conversion: {float(val) if val is not None else 'N/A'}")

        logger.info("\n" + "=" * 100)
        logger.info(f"Registros encontrados: {costos_hist.get('registros_encontrados')}")
        logger.info("=" * 100)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

asyncio.run(main())
