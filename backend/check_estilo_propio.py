"""
Verificar qué valores reales tiene estilo_propio en la BD para 17224, 17225, 18420
"""
import asyncio
import asyncpg
import ssl
from src.smp.config import settings

async def check_styles():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    conn = await asyncpg.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        ssl=ssl_context,
        server_settings={'application_name': 'check_estilo_propio'}
    )

    try:
        # Verificar cada estilo
        for estilo in [17224, 17225, 18420]:
            print(f"\n{'='*80}")
            print(f"BÚSQUEDA: estilo_propio = '{estilo}'")
            print(f"{'='*80}")

            # Como STRING
            query = f"""
            SELECT COUNT(*) as total, COUNT(DISTINCT cod_ordpro) as ops_dist
            FROM {settings.db_schema}.costo_op_detalle
            WHERE estilo_propio::text = '{estilo}'
            AND version_calculo = 'FLUIDA'
            """
            result = await conn.fetchrow(query)
            print(f"✓ Búsqueda como STRING: {result['total']} registros, {result['ops_dist']} OPs distintas")

            # Como INTEGER
            try:
                query2 = f"""
                SELECT COUNT(*) as total, COUNT(DISTINCT cod_ordpro) as ops_dist
                FROM {settings.db_schema}.costo_op_detalle
                WHERE estilo_propio = {estilo}
                AND version_calculo = 'FLUIDA'
                """
                result2 = await conn.fetchrow(query2)
                print(f"✓ Búsqueda como INTEGER: {result2['total']} registros, {result2['ops_dist']} OPs distintas")
            except:
                print(f"✗ Búsqueda como INTEGER: ERROR")

            # Ver valores ÚNICOS de estilo_propio que contengan ese número
            query3 = f"""
            SELECT DISTINCT estilo_propio, COUNT(*) as cantidad
            FROM {settings.db_schema}.costo_op_detalle
            WHERE estilo_propio::text LIKE '%{estilo}%'
            AND version_calculo = 'FLUIDA'
            GROUP BY estilo_propio
            ORDER BY cantidad DESC
            LIMIT 10
            """
            rows = await conn.fetch(query3)
            if rows:
                print(f"\nValores únicos de estilo_propio que contienen '{estilo}':")
                for row in rows:
                    print(f"  - '{row['estilo_propio']}' ({row['cantidad']} registros)")
            else:
                print(f"\n✗ No se encontró NINGÚN estilo_propio que contenga '{estilo}'")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_styles())
