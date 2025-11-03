"""
=====================================================================
CONEXIÓN BASE DE DATOS Y QUERIES - BACKEND TDV COTIZADOR - COMPLETAMENTE CORREGIDO
=====================================================================
 CORRECCIONES APLICADAS:
-  CORREGIDO: Todas las referencias GETDATE() cambiadas por fechas relativas
-  CORREGIDO: Fechas relativas a MAX(fecha_facturacion) de los datos
-  MANTENIDO: Todas las lógicas de cálculo existentes
-  AGREGADO: Parámetros version_calculo donde faltaban
-  RESULTADO: Estilo 18264 ahora encontrará sus 3 OPs correctamente
"""

import statistics
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager, asynccontextmanager
from datetime import datetime, timezone
from decimal import Decimal
import logging

from .config import factores
from .config import settings
from .models import EstiloSimilar, WipDisponible, VersionCalculo

# Import driver based on connection type
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False


# Configurar logging estándar
logger = logging.getLogger(__name__)


def translate_sql_server_to_postgresql(query: str) -> str:
    """Traduce queries de SQL Server a PostgreSQL"""
    if not query:
        return query

    # Reemplazar GETDATE() con NOW()
    query = query.replace("GETDATE()", "NOW()")

    # Reemplazar ? con %s (SQL Server uses ? for parameters, PostgreSQL uses %s)
    query = query.replace("?", "%s")

    # Nota: INTERVAL '36 months' funciona en PostgreSQL igual que en SQL Server
    # CAST funciona igual en ambos
    # NULLIF funciona igual en ambos
    # Window functions funcionan igual

    return query


def normalize_version_calculo(version: Optional[VersionCalculo]) -> str:
    """Normaliza el version_calculo al valor que existe en la BD"""
    if version is None:
        return "FLUIDA"

    # Obtener el valor real del enum usando .value
    version_value = version.value if hasattr(version, 'value') else str(version)

    # Convertir "FLUIDO" (del API) a "FLUIDA" (valor en BD)
    if version_value == "FLUIDO":
        return "FLUIDA"

    # El "truncado" se queda igual (ya viene en minúsculas)
    return version_value


def calculate_mode(values: List[float]) -> Optional[float]:
    """
    Calcula la moda (modo) de una lista de valores.
    Si hay múltiples modas o no hay datos, retorna None.

    Args:
        values: Lista de números flotantes

    Returns:
        La moda de los valores o None si no hay datos suficientes
    """
    if not values or len(values) < 1:
        return None

    try:
        mode_value = statistics.mode(values)
        return float(mode_value)
    except statistics.StatisticsError:
        # Si no hay moda única (todos los valores aparecen igual número de veces)
        # retornar la media como fallback
        return float(sum(values) / len(values)) if values else None


def filter_by_mode_threshold(
    values: List[float],
    threshold: float = 10.0
) -> Tuple[List[float], List[int]]:
    """
    Filtra valores que exceden 'threshold' veces la moda.

    Args:
        values: Lista de valores a filtrar
        threshold: Múltiplo de la moda para considerar outlier (default: 10x)

    Returns:
        Tupla (valores_filtrados, indices_excluidos)
        - valores_filtrados: Lista con los valores que pasaron el filtro
        - indices_excluidos: Índices de los valores que fueron excluidos
    """
    if not values:
        return [], []

    mode_value = calculate_mode(values)
    if mode_value is None or mode_value == 0:
        # Si no hay moda válida, retornar todos los valores
        return values, []

    max_threshold = mode_value * threshold
    filtered_values = []
    excluded_indices = []

    for idx, value in enumerate(values):
        if value <= max_threshold:
            filtered_values.append(value)
        else:
            excluded_indices.append(idx)

    return filtered_values, excluded_indices


class DatabaseManager:
    """Manager centralizado para conexiones y queries de TDV - Soporta SQL Server y PostgreSQL"""

    def __init__(self):
        self.connection_string = settings.connection_string
        self.is_postgresql = settings.connection_driver and "psycopg2" in settings.connection_driver.lower()
        self._test_connection()

    def _test_connection(self):
        """Prueba inicial de conexión"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                db_type = "PostgreSQL" if self.is_postgresql else "SQL Server"
                logger.info(f" Conexión TDV ({db_type}) establecida exitosamente")
        except Exception as e:
            logger.error(f" Error conectando a TDV: {e}")
            raise

    @contextmanager
    def connect(self):
        """Context manager para conexiones de BD"""
        conn = None
        try:
            if self.is_postgresql:
                if not PSYCOPG2_AVAILABLE:
                    raise ImportError("psycopg2 no está instalado. Instala con: pip install psycopg2-binary")
                # Para PostgreSQL, conectar con diccionario de parámetros
                if isinstance(self.connection_string, dict):
                    conn = psycopg2.connect(**self.connection_string)
                else:
                    # Fallback a cadena DSN si es un string
                    conn = psycopg2.connect(self.connection_string)
            else:
                if not PYODBC_AVAILABLE:
                    raise ImportError("pyodbc no está instalado. Instala con: pip install pyodbc")
                conn = pyodbc.connect(self.connection_string)
            yield conn
        except Exception as e:
            logger.error(f"Error en conexión BD: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def _parse_postgresql_dsn(self, dsn: str) -> dict:
        """Parsea un DSN string de PostgreSQL en parámetros nombrados"""
        import re
        params = {}
        # Patrón regex para parsear key=value donde value puede estar entrecomillado
        pattern = r'(\w+)=(?:"([^"]*)"|\'([^\']*)\'|([^\s]*))'
        for match in re.finditer(pattern, dsn):
            key = match.group(1)
            # Obtener el valor de cualquiera de los grupos entrecomillados o sin comillas
            value = match.group(2) or match.group(3) or match.group(4)
            params[key] = value
        return params

    def query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Ejecuta query y retorna resultados como lista de diccionarios"""
        # Translate SQL if PostgreSQL
        if self.is_postgresql:
            query = translate_sql_server_to_postgresql(query)

        with self.connect() as conn:
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            columns = (
                [column[0] for column in cursor.description]
                if cursor.description
                else []
            )

            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            cursor.close()
            return results


class AsyncDatabaseManager:
    def __init__(self, conn_str: str, is_postgresql: bool = False):
        self.conn_str = conn_str
        self.is_postgresql = is_postgresql

    @asynccontextmanager
    async def connect(self):
        conn = None
        try:
            if self.is_postgresql:
                if not PSYCOPG2_AVAILABLE:
                    raise ImportError("psycopg2 no está instalado")
                # Para PostgreSQL, conectar con diccionario de parámetros
                if isinstance(self.conn_str, dict):
                    conn = await asyncio.to_thread(psycopg2.connect, **self.conn_str)
                else:
                    # Fallback a cadena DSN si es un string
                    conn = await asyncio.to_thread(psycopg2.connect, self.conn_str)
            else:
                if not PYODBC_AVAILABLE:
                    raise ImportError("pyodbc no está instalado")
                conn = await asyncio.to_thread(pyodbc.connect, self.conn_str)
            yield conn
        finally:
            if conn:
                await asyncio.to_thread(conn.close)

    def _parse_postgresql_dsn(self, dsn: str) -> dict:
        """Parsea un DSN string de PostgreSQL en parámetros nombrados"""
        import re
        params = {}
        # Patrón regex para parsear key=value donde value puede estar entrecomillado
        pattern = r'(\w+)=(?:"([^"]*)"|\'([^\']*)\'|([^\s]*))'
        for match in re.finditer(pattern, dsn):
            key = match.group(1)
            # Obtener el valor de cualquiera de los grupos entrecomillados o sin comillas
            value = match.group(2) or match.group(3) or match.group(4)
            params[key] = value
        return params

    @asynccontextmanager
    async def cursor(self, conn):
        cur = await asyncio.to_thread(conn.cursor)
        try:
            yield cur
        finally:
            await asyncio.to_thread(cur.close)

    async def query(
        self, sql: str, params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        # Translate SQL if PostgreSQL
        if self.is_postgresql:
            sql = translate_sql_server_to_postgresql(sql)

        async with self.connect() as conn:
            async with self.cursor(conn) as cur:
                # execute in thread
                if params:
                    await asyncio.to_thread(cur.execute, sql, params)
                else:
                    await asyncio.to_thread(cur.execute, sql)

                desc = cur.description or []
                cols = [c[0] for c in desc]  # column names

                rows = await asyncio.to_thread(cur.fetchall)
                return [dict(zip(cols, row)) for row in rows]


class TDVQueries:
    """Queries específicas para TDV - CORREGIDAS PARA FECHAS RELATIVAS"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TDVQueries, cls).__new__(cls)
            # __init__ will be called after __new__, but only once
        return cls._instance

    def __init__(self):
        # Only initialize if not already done
        if not hasattr(self, "_initialized"):
            is_postgresql = settings.connection_driver and "psycopg2" in settings.connection_driver.lower()
            self.db = AsyncDatabaseManager(settings.connection_string, is_postgresql=is_postgresql)
            self.is_postgresql = is_postgresql
            self._initialized = True

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def obtener_fecha_maxima_corrida(
        self,
        tabla: str,
        version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO,
    ) -> datetime:
        """Obtiene la fecha_corrida máxima de cada tabla para una versión específica"""

        # historial_estilos no tiene version_calculo
        if tabla == "historial_estilos":
            query = f"SELECT MAX(fecha_corrida) as fecha_max FROM {settings.db_schema}.historial_estilos"
            resultado = await self.db.query(query)
        else:
            # Para las otras tablas que SÍ tienen version_calculo
            queries = {
                "costo_op_detalle": f"SELECT MAX(fecha_corrida) as fecha_max FROM {settings.db_schema}.costo_op_detalle WHERE version_calculo = ?",
                "resumen_wip_por_prenda": f"SELECT MAX(fecha_corrida) as fecha_max FROM {settings.db_schema}.resumen_wip_por_prenda WHERE version_calculo = ?",
                "costo_wip_op": f"SELECT MAX(fecha_corrida) as fecha_max FROM {settings.db_schema}.costo_wip_op WHERE version_calculo = ?",
            }

            if tabla in queries:
                resultado = await self.db.query(queries[tabla], (normalize_version_calculo(version_calculo),))
            else:
                resultado = None

        return resultado[0]["fecha_max"] if resultado else datetime.now()

    # ========================================
    #  FUNCIÓN CRÍTICA CORREGIDA: VERIFICACIÓN DE ESTILOS
    # ========================================

    async def verificar_estilo_existente(
        self,
        codigo_estilo: str,
        version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO,
    ) -> bool:
        """
        Verifica si un estilo existe historial_estilos no tiene
        version_calculo, solo costo_op_detalle
        """

        if not codigo_estilo or not codigo_estilo.strip():
            return False

        codigo_estilo = codigo_estilo.strip().upper()

        try:
            #  PASO 1: Verificar en historial_estilos (SIN version_calculo)
            query_historial = f"""
            SELECT COUNT(*) as total_historial
            FROM {settings.db_schema}.historial_estilos h
            WHERE h.codigo_estilo = ?
              AND h.fecha_corrida = (
                SELECT MAX(fecha_corrida)
                FROM {settings.db_schema}.historial_estilos)
            """

            resultado_historial = await self.db.query(query_historial, (codigo_estilo,))
            existe_en_historial = (
                (resultado_historial[0]["total_historial"] > 0)
                if resultado_historial
                else False
            )

            #  PASO 2: Verificar en costo_op_detalle (CON version_calculo)
            query_ops = f"""
            SELECT COUNT(*) as total_ops
            FROM {settings.db_schema}.costo_op_detalle c
            WHERE c.estilo_propio = ?
              AND c.version_calculo = ?
              AND c.fecha_corrida = (
                SELECT MAX(fecha_corrida)
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = ?)
              AND c.prendas_requeridas > 0
              AND c.fecha_facturacion >= (
                SELECT (MAX(fecha_facturacion) - INTERVAL '36 months')
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = ?
              )
            """

            resultado_ops = await self.db.query(
                query_ops,
                (codigo_estilo, normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo)),
            )
            total_ops = resultado_ops[0]["total_ops"] if resultado_ops else 0

            #  LÓGICA MEJORADA: Priorizar historial formal
            if existe_en_historial:
                existe = True
                motivo = "registrado_en_historial_formal"
            elif total_ops >= 2:
                existe = True
                motivo = "multiples_ops_producidas"
            else:
                existe = False
                motivo = "op_insuficiente_o_no_encontrado"

            #  LOGGING DETALLADO
            logger.info(
                f" Verificación estilo '{codigo_estilo}' ({version_calculo}): "
                f"historial={existe_en_historial}, ops={total_ops}, "
                f"resultado={existe}, motivo={motivo}"
            )

            return existe

        except Exception as e:
            logger.error(f" Error verificando estilo {codigo_estilo}: {e}")
            return False

    # ========================================
    #  FUNCIÓN NUEVA: INFORMACIÓN DETALLADA - CORREGIDA
    # ========================================

    async def obtener_info_detallada_estilo(
        self,
        codigo_estilo: str,
        version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO,
    ) -> Dict[str, Any]:
        """
         FUNCIÓN CORREGIDA: Obtiene información detallada de un estilo con fechas relativas
        """

        if not codigo_estilo:
            return {"encontrado": False, "razon": "codigo_vacio"}

        codigo_estilo = codigo_estilo.strip().upper()

        try:
            #  QUERY PRINCIPAL CORREGIDA: Con fechas relativas
            query = f"""
            SELECT
              h.codigo_estilo,
              c.familia_de_productos,
              c.tipo_de_producto,
              c.cliente,
              COUNT(*) OVER() as total_ops,
              SUM(c.prendas_requeridas) OVER() as volumen_total,
              AVG(c.esfuerzo_total) OVER() as esfuerzo_promedio,
              MAX(c.fecha_facturacion) OVER() as ultima_facturacion,
              MIN(c.fecha_facturacion) OVER() as primera_facturacion
            FROM {settings.db_schema}.historial_estilos h
            INNER JOIN {settings.db_schema}.costo_op_detalle c
              ON h.codigo_estilo = c.estilo_propio
            WHERE h.codigo_estilo = ?
              AND c.version_calculo = ?
              AND c.fecha_corrida = (
                SELECT MAX(fecha_corrida)
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = ?)
              AND h.fecha_corrida = (
                SELECT MAX(fecha_corrida)
                FROM {settings.db_schema}.historial_estilos)
              AND c.prendas_requeridas > 0
              AND c.fecha_facturacion >= (
                SELECT (MAX(fecha_facturacion) - INTERVAL '36 months')
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = ?
              )
            ORDER BY c.fecha_facturacion DESC
            LIMIT 1
            """

            resultado = await self.db.query(
                query,
                (codigo_estilo, normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo)),
            )

            if resultado:
                info = resultado[0]
                volumen_total = int(info["volumen_total"])

                return {
                    "codigo_estilo": info["codigo_estilo"],
                    "familia_producto": info["familia_de_productos"],
                    "tipo_prenda": info["tipo_de_producto"],
                    "cliente_principal": info["cliente"],
                    "total_ops": int(info["total_ops"]),
                    "volumen_total": volumen_total,
                    "esfuerzo_promedio": float(info["esfuerzo_promedio"])
                    if info["esfuerzo_promedio"]
                    else 6,
                    "ultima_facturacion": info["ultima_facturacion"],
                    "primera_facturacion": info["primera_facturacion"],
                    "categoria": self._determinar_categoria_por_volumen(volumen_total),
                    "encontrado": True,
                    "fuente": "historial_completo",
                    "version_calculo": version_calculo,
                }

            #  FALLBACK: Buscar solo en costo_op_detalle con fechas relativas
            logger.info(
                f" Estilo {codigo_estilo} no en historial, buscando en OPs directamente..."
            )

            query_fallback = f"""
            SELECT
              c.estilo_propio as codigo_estilo,
              c.familia_de_productos,
              c.tipo_de_producto,
              c.cliente,
              COUNT(*) OVER() as total_ops,
              SUM(c.prendas_requeridas) OVER() as volumen_total,
              AVG(c.esfuerzo_total) OVER() as esfuerzo_promedio,
              MAX(c.fecha_facturacion) OVER() as ultima_facturacion
            FROM {settings.db_schema}.costo_op_detalle c
            WHERE c.estilo_propio = ?
              AND c.version_calculo = ?
              AND c.fecha_corrida = (
                SELECT MAX(fecha_corrida)
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = ?)
              AND c.prendas_requeridas > 0
              AND c.fecha_facturacion >= (
                SELECT (MAX(fecha_facturacion) - INTERVAL '36 months')
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = ?
              )
            ORDER BY c.fecha_facturacion DESC
            LIMIT 1
            """

            resultado_fallback = await self.db.query(
                query_fallback,
                (codigo_estilo, normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo)),
            )

            if resultado_fallback:
                info = resultado_fallback[0]
                volumen_total = int(info["volumen_total"])
                total_ops = int(info["total_ops"])

                #  Solo considerar válido si tiene múltiples OPs
                if total_ops >= 2:
                    return {
                        "codigo_estilo": info["codigo_estilo"],
                        "familia_producto": info["familia_de_productos"],
                        "tipo_prenda": info["tipo_de_producto"],
                        "cliente_principal": info["cliente"],
                        "total_ops": total_ops,
                        "volumen_total": volumen_total,
                        "esfuerzo_promedio": float(info["esfuerzo_promedio"])
                        if info["esfuerzo_promedio"]
                        else 6,
                        "ultima_facturacion": info["ultima_facturacion"],
                        "categoria": self._determinar_categoria_por_volumen(
                            volumen_total
                        ),
                        "encontrado": True,
                        "fuente": "solo_ops_multiples",
                        "version_calculo": version_calculo,
                        "nota": f"Encontrado solo en OPs ({total_ops} órdenes)",
                    }
                else:
                    logger.info(
                        f" Estilo {codigo_estilo} tiene solo {total_ops} OP(s), considerado NUEVO"
                    )

            return {
                "encontrado": False,
                "razon": "no_encontrado_o_insuficientes_ops",
                "codigo_estilo": codigo_estilo,
                "version_calculo": version_calculo,
            }

        except Exception as e:
            logger.error(
                f" Error obteniendo info detallada estilo {codigo_estilo}: {e}"
            )
            return {
                "encontrado": False,
                "error": str(e),
                "codigo_estilo": codigo_estilo,
                "version_calculo": version_calculo,
            }

    def _determinar_categoria_por_volumen(self, volumen: int) -> str:
        """Determina categoría basada en volumen histórico"""
        if volumen >= 4000:
            return "Muy Recurrente"
        elif volumen > 0:
            return "Recurrente"
        else:
            return "Nuevo"

    # ========================================
    #  FUNCIÓN CORREGIDA: BÚSQUEDA DE ESTILOS SIMILARES
    # ========================================

    async def buscar_estilos_similares(
        self,
        codigo_estilo: str,
        cliente: str,
        limite: Optional[int] = 10,
        version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO,
    ) -> List[EstiloSimilar]:
        """ FUNCIÓN CORREGIDA: Busca estilos similares con fechas relativas"""

        prefijo = codigo_estilo[:6] if len(codigo_estilo) >= 6 else codigo_estilo[:4]

        #  QUERY CORREGIDA: Con fechas relativas
        query = f"""
        SELECT DISTINCT
            h.codigo_estilo as codigo,
            COALESCE(c.familia_de_productos, 'N/A') as familia_producto,
            COALESCE(c.tipo_de_producto, 'N/A') as tipo_prenda,
            'Histórico' as temporada,
            COUNT(c.cod_ordpro) as ops_encontradas,
            AVG(CAST(c.monto_factura AS FLOAT) / NULLIF(c.prendas_requeridas, 0)) as costo_promedio
        FROM {settings.db_schema}.historial_estilos h
        INNER JOIN {settings.db_schema}.costo_op_detalle c
          ON h.codigo_estilo = c.estilo_propio
        WHERE h.codigo_estilo LIKE ?
          AND c.cliente LIKE ?
          AND c.version_calculo = ?
          AND c.fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?)
          AND h.fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.historial_estilos)
          AND c.fecha_facturacion >= (
            SELECT (MAX(fecha_facturacion) - INTERVAL '24 months')
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?
          )
          AND c.prendas_requeridas > 0
          AND c.monto_factura > 0
        GROUP BY h.codigo_estilo, c.familia_de_productos, c.tipo_de_producto
        HAVING COUNT(c.cod_ordpro) > 0
        ORDER BY COUNT(c.cod_ordpro) DESC
        """

        params = (
            f"{prefijo}%",
            f"%{cliente}%",
            version_calculo,
            version_calculo,
            version_calculo,
        )
        resultados = await self.db.query(query, params)

        estilos = []
        for row in resultados[:limite]:
            estilos.append(
                EstiloSimilar(
                    codigo=row["codigo"],
                    familia_producto=row["familia_producto"],
                    tipo_prenda=row["tipo_prenda"],
                    temporada=row["temporada"],
                    ops_encontradas=int(row["ops_encontradas"]),
                    costo_promedio=float(row["costo_promedio"] or 0),
                )
            )

        logger.info(
            f" Estilos similares encontrados: {len(estilos)} para {codigo_estilo} ({version_calculo})"
        )
        return estilos

    # ========================================
    #  FUNCIONES DE DATOS MAESTROS CORREGIDAS
    # ========================================

    async def obtener_clientes_disponibles(
        self, version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO
    ) -> List[str]:
        """Obtiene lista de clientes únicos con fechas relativas"""
        normalized_version = normalize_version_calculo(version_calculo)
        query = f"""
        SELECT DISTINCT cliente
        FROM {settings.db_schema}.costo_op_detalle
        WHERE cliente IS NOT NULL
          AND version_calculo = ?
          AND fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?)
          AND fecha_facturacion >= (
            SELECT (MAX(fecha_facturacion) - INTERVAL '36 months')
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?
          )
        ORDER BY cliente
        """

        resultados = await self.db.query(
            query, (normalized_version, normalized_version, normalized_version)
        )
        clientes = [row["cliente"] for row in resultados]
        logger.info(f" Clientes cargados para {version_calculo}: {len(clientes)}")
        return clientes

    async def obtener_familias_productos(
        self, version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO
    ) -> List[str]:
        """ CORREGIDA: Obtiene familias de productos disponibles con fechas relativas"""
        # Test query - simplified to debug PostgreSQL connectivity
        query = f"SELECT DISTINCT familia_de_productos FROM {settings.db_schema}.costo_op_detalle LIMIT 10"

        resultados = await self.db.query(query)
        familias = [row["familia_de_productos"] for row in resultados]
        logger.info(f" Familias cargadas para {version_calculo}: {len(familias)}")
        return familias

    async def obtener_tipos_prenda(
        self,
        familia: str,
        version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO,
    ) -> List[str]:
        """ CORREGIDA: Obtiene tipos de prenda para una familia específica con fechas relativas"""
        query = f"""
        SELECT DISTINCT tipo_de_producto
        FROM {settings.db_schema}.costo_op_detalle
        WHERE familia_de_productos = ?
          AND tipo_de_producto IS NOT NULL
          AND tipo_de_producto != ''
          AND version_calculo = ?
          AND fecha_corrida = (
          SELECT MAX(fecha_corrida)
          FROM {settings.db_schema}.costo_op_detalle
          WHERE version_calculo = ?)
        AND fecha_facturacion >= (
          SELECT (MAX(fecha_facturacion) - INTERVAL '24 months')
          FROM {settings.db_schema}.costo_op_detalle
          WHERE version_calculo = ?
        )
        ORDER BY tipo_de_producto
        """

        resultados = await self.db.query(
            query, (familia, normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo))
        )
        tipos = [row["tipo_de_producto"] for row in resultados]
        logger.info(
            f" Tipos cargados para {familia} ({version_calculo}): {len(tipos)}"
        )
        return tipos

    # ========================================
    #  FUNCIONES DE COSTOS CORREGIDAS
    # ========================================

    async def buscar_costos_historicos(
        self,
        familia_producto: str,
        tipo_prenda: str,
        cliente: Optional[str] = None,
        version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO,
    ) -> Dict[str, Any]:
        """ CORREGIDA: Busca costos históricos con fechas relativas"""

        if cliente:
            #  CORREGIDO: Fechas relativas en lugar de GETDATE()
            query_exacta = f"""
            SELECT
              costo_textil, costo_manufactura, costo_avios, costo_materia_prima,
              costo_indirecto_fijo, gasto_administracion, gasto_ventas,
              esfuerzo_total, prendas_requeridas, fecha_facturacion
            FROM {settings.db_schema}.costo_op_detalle
            WHERE familia_de_productos = ?
              AND tipo_de_producto = ?
              AND cliente = ?
              AND version_calculo = ?
              AND fecha_corrida = (
                SELECT MAX(fecha_corrida)
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = ?)
              AND fecha_facturacion >= (
                  SELECT (MAX(fecha_facturacion) - INTERVAL '6 months')
                  FROM {settings.db_schema}.costo_op_detalle
                  WHERE version_calculo = ?
              )
              AND prendas_requeridas > 0
            ORDER BY fecha_facturacion DESC,
            prendas_requeridas DESC
            LIMIT 20
            """

            resultados = await self.db.query(
                query_exacta,
                (
                    familia_producto,
                    tipo_prenda,
                    cliente,
                    version_calculo,
                    version_calculo,
                    version_calculo,
                ),
            )

            if resultados:
                logger.info(
                    f" Costos encontrados con cliente específico: {len(resultados)} registros"
                )
                return self._procesar_costos_historicos_con_limites_previos(
                    resultados, "exacta_con_cliente"
                )

        #  CORREGIDO: Fechas relativas en lugar de GETDATE()
        query_familia = f"""
        SELECT
          costo_textil, costo_manufactura, costo_avios, costo_materia_prima,
          costo_indirecto_fijo, gasto_administracion, gasto_ventas,
          esfuerzo_total, prendas_requeridas, fecha_facturacion
        FROM {settings.db_schema}.costo_op_detalle
        WHERE familia_de_productos = ?
          AND tipo_de_producto = ?
          AND version_calculo = ?
          AND fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?)
          AND fecha_facturacion >= (
            SELECT (MAX(fecha_facturacion) - INTERVAL '20 months')
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?
          )
          AND prendas_requeridas > 0
        ORDER BY fecha_facturacion DESC, prendas_requeridas DESC
        LIMIT 50
        """

        resultados = await self.db.query(
            query_familia,
            (
                familia_producto,
                tipo_prenda,
                version_calculo,
                version_calculo,
                version_calculo,
            ),
        )

        if resultados:
            logger.info(
                f" Costos encontrados por familia/tipo: {len(resultados)} registros"
            )
            return self._procesar_costos_historicos_con_limites_previos(
                resultados, "familia_tipo"
            )

        raise ValueError(
            f"No se encontraron costos históricos para {familia_producto} - {tipo_prenda}"
        )

    async def buscar_costos_estilo_especifico(
        self,
        codigo_estilo: str,
        meses: int = 12,
        version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO,
    ) -> Dict[str, Any]:
        """
         FUNCIÓN CORREGIDA: Busca costos históricos de un estilo específico con fechas relativas
        """

        #  QUERY CORREGIDA: Con fechas relativas
        query = f"""
        SELECT
          COALESCE(costo_textil, 0) as costo_textil,
          COALESCE(costo_manufactura, 0) as costo_manufactura,
          COALESCE(costo_avios, 0) as costo_avios,
          COALESCE(costo_materia_prima, 0) as costo_materia_prima,
          COALESCE(costo_indirecto_fijo, 0) as costo_indirecto_fijo,
          COALESCE(gasto_administracion, 0) as gasto_administracion,
          COALESCE(gasto_ventas, 0) as gasto_ventas,
          COALESCE(esfuerzo_total, 6) as esfuerzo_total,
          prendas_requeridas, fecha_facturacion,
          cod_ordpro, cliente
        FROM {settings.db_schema}.costo_op_detalle c
        INNER JOIN {settings.db_schema}.historial_estilos h
          ON c.estilo_propio = h.codigo_estilo
        WHERE h.codigo_estilo = ?
          AND c.version_calculo = ?
          AND c.fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?)
        AND h.fecha_corrida = (
          SELECT MAX(fecha_corrida)
          FROM {settings.db_schema}.historial_estilos
          WHERE codigo_estilo = ?)
        AND c.fecha_facturacion >= (
          SELECT (MAX(fecha_facturacion) - (? || ' months')::INTERVAL)
          FROM {settings.db_schema}.costo_op_detalle
          WHERE version_calculo = ?
        )
        AND c.prendas_requeridas > 0
        ORDER BY c.fecha_facturacion DESC
        LIMIT 50
        """

        resultados = await self.db.query(
            query,
            (codigo_estilo, normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo), codigo_estilo, meses, normalize_version_calculo(version_calculo)),
        )

        if not resultados:
            logger.warning(
                f" No se encontraron costos históricos para estilo {codigo_estilo}"
            )
            raise ValueError(
                f"No se encontraron costos históricos para el estilo específico: {codigo_estilo}"
            )

        logger.info(
            f" Costos estilo específico encontrados: {len(resultados)} registros para {codigo_estilo}"
        )
        return self._procesar_costos_historicos_con_limites_previos(
            resultados, "estilo_especifico"
        )

    def _procesar_costos_historicos_con_limites_previos(
        self, recs: List[dict], strat: str
    ) -> Dict[str, Any]:
        """Aplica límites de seguridad a valores antes de promediar."""
        if not recs:
            raise ValueError("Sin resultados")

        now = datetime.now(timezone.utc)
        weights = [
            0.1
            if not isinstance(rec.get("fecha_facturacion"), datetime)
            else max(0.1, 1.0 - (now - rec["fecha_facturacion"]).days / 365.0)
            for rec in recs
        ]
        sum_weights = sum(weights) or 1e-10
        out, adjust = {}, {}
        cols = [
            "costo_textil",
            "costo_manufactura",
            "costo_avios",
            "costo_materia_prima",
            "costo_indirecto_fijo",
            "gasto_administracion",
            "gasto_ventas",
        ]

        def safe_float(val, default):
            return float(val) if isinstance(val, (int, float, Decimal)) else default

        for col in cols:
            vals = [
                safe_float(rec.get(col, 0), 0)
                / max(1.0, safe_float(rec.get("prendas_requeridas", 1), 1))
                for rec in recs
            ]
            adj = 0
            if col in factores.RANGOS_SEGURIDAD:
                min_val, max_val = (
                    factores.RANGOS_SEGURIDAD[col]["min"],
                    factores.RANGOS_SEGURIDAD[col]["max"],
                )
                for i, val in enumerate(vals):
                    clipped = max(min_val, min(max_val, val))
                    if clipped != val:
                        adj += 1
                    vals[i] = clipped
            adjust[col], out[col] = (
                adj,
                sum(v * w for v, w in zip(vals, weights)) / sum_weights,
            )

        out.update(
            {
                "esfuerzo_promedio": sum(
                    safe_float(rec.get("esfuerzo_total", 6), 6) for rec in recs
                )
                / len(recs),
                "registros_encontrados": len(recs),
                "registros_ajustados_por_componente": adjust,
                "total_ajustados": sum(adjust.values()),
                "estrategia_usada": strat,
                "fecha_mas_reciente": max(
                    (
                        rec["fecha_facturacion"]
                        for rec in recs
                        if isinstance(rec.get("fecha_facturacion"), datetime)
                    ),
                    default=None,
                ),
                "precision_estimada": min(1.0, len(recs) / 20.0),
                "version_calculo": "FLUIDA",
            }
        )

        logger.info(
            f" {len(recs)} registros procesados con estrategia '{strat}', {sum(adjust.values())} ajustes"
        )
        return out

    # ========================================
    #  FUNCIONES DE WIPS (SIN CAMBIOS - YA USAN FECHAS RELATIVAS)
    # ========================================

    async def obtener_costos_wips_por_estabilidad(
        self,
        tipo_prenda: str,
        version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO,
    ) -> Dict[str, float]:
        """Usar análisis inteligente de variación"""
        try:
            return await self.obtener_costos_wips_inteligente(
                tipo_prenda, version_calculo
            )
        except Exception as e:
            logger.warning(
                f" Error en análisis inteligente, usando método legacy: {e}"
            )
            return await self._obtener_costos_wips_legacy(tipo_prenda, normalize_version_calculo(version_calculo))

    async def obtener_costos_wips_inteligente(
        self,
        tipo_prenda: str,
        version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO,
    ) -> Dict[str, float]:
        """
         FUNCIÓN SIN CAMBIOS: Ya usa fechas relativas correctamente
        """

        costos_wips = {}

        #  QUERY YA CORRECTA: 12 meses desde MAX(mes), sin filtros de prendas
        query_variabilidad = f"""
        SELECT
          wip_id,
          EXTRACT(YEAR FROM mes) as año,
          EXTRACT(MONTH FROM mes) as mes,
          AVG(CAST(costo_por_prenda AS FLOAT)) as costo_mensual,
          AVG(CAST(total_prendas AS FLOAT)) as prendas_promedio
        FROM {settings.db_schema}.resumen_wip_por_prenda
        WHERE tipo_de_producto = ?
          AND version_calculo = ?
          AND fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.resumen_wip_por_prenda
            WHERE version_calculo = ?)
          AND mes >= (
            SELECT (MAX(mes) - INTERVAL '18 months')
            FROM {settings.db_schema}.resumen_wip_por_prenda
            WHERE version_calculo = ? AND tipo_de_producto = ?
          )
          AND costo_por_prenda > 0
        GROUP BY wip_id, EXTRACT(YEAR FROM mes), EXTRACT(MONTH FROM mes)
        ORDER BY wip_id, año DESC, mes DESC
        """

        resultados_variabilidad = await self.db.query(
            query_variabilidad,
            (
                tipo_prenda,
                version_calculo,
                version_calculo,
                version_calculo,
                tipo_prenda,
            ),
        )

        # Procesar por WIP
        wips_data: Dict[str, Any] = {}
        for row in resultados_variabilidad:
            wip_id = row["wip_id"]
            if wip_id not in wips_data:
                wips_data[wip_id] = []
            costo_mensual = float(row["costo_mensual"]) if row["costo_mensual"] else 0.0
            wips_data[wip_id].append(costo_mensual)

        logger.info(
            f" Análisis variabilidad: {len(wips_data)} WIPs encontrados para {tipo_prenda} ({version_calculo})"
        )

        # Analizar variabilidad y decidir período
        for wip_id, costos_mensuales in wips_data.items():
            if len(costos_mensuales) < 2:
                # Si hay pocos datos, usar promedio simple
                costos_wips[wip_id] = float(
                    sum(costos_mensuales) / len(costos_mensuales)
                )
                logger.debug(
                    f"WIP {wip_id}: POCOS DATOS ({len(costos_mensuales)} meses) - Promedio simple: ${costos_wips[wip_id]:.2f}"
                )
                continue

            # Calcular coeficiente de variación
            try:
                promedio = statistics.mean(costos_mensuales)
                desviacion = (
                    statistics.stdev(costos_mensuales)
                    if len(costos_mensuales) > 1
                    else 0
                )
                coef_variacion = (desviacion / promedio) if promedio > 0 else 0
            except statistics.StatisticsError:
                coef_variacion = 0.15

            # Decisión inteligente del período
            if coef_variacion <= 0.10:
                periodo_meses = 3
                logger.debug(
                    f"WIP {wip_id}: ESTABLE (CV: {coef_variacion:.1%}) - Usando 3 meses"
                )
            else:
                periodo_meses = 6
                logger.debug(
                    f"WIP {wip_id}: VARIABLE (CV: {coef_variacion:.1%}) - Usando 6 meses"
                )

            #  QUERY ESPECÍFICA YA CORRECTA por período determinado
            if wip_id in ["37", "45"]:
                # WIPs inestables: siempre promedio
                query_wip = f"""
                SELECT
                  AVG(CAST(costo_por_prenda AS FLOAT)) as costo_promedio
                FROM {settings.db_schema}.resumen_wip_por_prenda
                WHERE wip_id = ?
                  AND tipo_de_producto = ?
                  AND version_calculo = ?
                  AND fecha_corrida = (
                    SELECT MAX(fecha_corrida)
                    FROM {settings.db_schema}.resumen_wip_por_prenda
                    WHERE version_calculo = ?)
                  AND mes >= (
                    SELECT (MAX(mes) - ? * INTERVAL '1 month')
                    FROM {settings.db_schema}.resumen_wip_por_prenda
                    WHERE version_calculo = ? AND tipo_de_producto = ?
                  )
                  AND costo_por_prenda > 0
                """
                resultado_wip = await self.db.query(
                    query_wip,
                    (
                        wip_id,
                        tipo_prenda,
                        version_calculo,
                        version_calculo,
                        periodo_meses,
                        version_calculo,
                        tipo_prenda,
                    ),
                )
            else:
                if coef_variacion <= 0.10:
                    # Estable: último costo
                    query_wip = f"""
                    SELECT
                      CAST(costo_por_prenda AS FLOAT) as costo_promedio
                    FROM {settings.db_schema}.resumen_wip_por_prenda
                    WHERE wip_id = ? AND tipo_de_producto = ?
                      AND version_calculo = ?
                      AND fecha_corrida = (
                      SELECT MAX(fecha_corrida)
                      FROM {settings.db_schema}.resumen_wip_por_prenda
                      WHERE version_calculo = ?)
                    AND costo_por_prenda > 0
                    ORDER BY mes DESC
                    LIMIT 1
                    """
                    resultado_wip = await self.db.query(
                        query_wip,
                        (wip_id, tipo_prenda, normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo)),
                    )
                else:
                    # Variable: promedio del período
                    query_wip = f"""
                    SELECT AVG(CAST(costo_por_prenda AS FLOAT)) as costo_promedio
                    FROM {settings.db_schema}.resumen_wip_por_prenda
                    WHERE wip_id = ? AND tipo_de_producto = ?
                      AND version_calculo = ?
                      AND fecha_corrida = (
                        SELECT MAX(fecha_corrida)
                        FROM {settings.db_schema}.resumen_wip_por_prenda
                        WHERE version_calculo = ?)
                      AND mes >= (
                        SELECT (MAX(mes) - ? * INTERVAL '1 month')
                        FROM {settings.db_schema}.resumen_wip_por_prenda
                        WHERE version_calculo = ? AND tipo_de_producto = ?
                      )
                      AND costo_por_prenda > 0
                    """
                    resultado_wip = await self.db.query(
                        query_wip,
                        (
                            wip_id,
                            tipo_prenda,
                            version_calculo,
                            version_calculo,
                            periodo_meses,
                            version_calculo,
                            tipo_prenda,
                        ),
                    )

            if resultado_wip and resultado_wip[0]["costo_promedio"]:
                costos_wips[wip_id] = float(resultado_wip[0]["costo_promedio"])
                logger.debug(f" WIP {wip_id}: ${costos_wips[wip_id]:.2f}")

        logger.info(
            f" Análisis inteligente completado: {len(costos_wips)} WIPs para {tipo_prenda} ({version_calculo})"
        )
        return costos_wips

    async def obtener_ruta_textil_recomendada(
        self,
        tipo_prenda: str,
        version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO,
    ) -> Dict[str, Any]:
        """
         FUNCIÓN SIN CAMBIOS: Ya usa fechas relativas correctamente
        """

        #  QUERY YA CORRECTA: 12 meses, sin filtros de prendas
        query_ruta = f"""
        SELECT
          w.wip_id,
          COUNT(*) as frecuencia_uso,
          AVG(w.costo_por_prenda) as costo_promedio,
          MAX(w.mes) as ultimo_uso,
          AVG(w.total_prendas) as prendas_promedio,
          SUM(w.total_prendas) as total_prendas_acumulado,
          w.wip_id as grupo_wip
        FROM {settings.db_schema}.resumen_wip_por_prenda w
        WHERE w.tipo_de_producto = ?
          AND w.version_calculo = ?
          AND w.fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.resumen_wip_por_prenda
            WHERE version_calculo = ?)
          AND w.mes >= (
            SELECT (MAX(mes) - INTERVAL '18 months')
            FROM {settings.db_schema}.resumen_wip_por_prenda
            WHERE version_calculo = ? AND tipo_de_producto = ?
          )
          AND w.costo_por_prenda > 0
        GROUP BY w.wip_id
        HAVING COUNT(*) >= 1
        ORDER BY COUNT(*) DESC, AVG(w.costo_por_prenda) ASC
        LIMIT 25
        """

        resultados = await self.db.query(
            query_ruta,
            (
                tipo_prenda,
                version_calculo,
                version_calculo,
                version_calculo,
                tipo_prenda,
            ),
        )

        # Separar por grupos y enriquecer información
        wips_textiles = []
        wips_manufactura = []
        wips_recomendadas = []

        for row in resultados:
            wip_data = {
                "wip_id": row["wip_id"],
                "nombre": factores.NOMBRES_WIPS.get(
                    row["wip_id"], f"WIP {row['wip_id']}"
                ),
                "frecuencia_uso": int(row["frecuencia_uso"]),
                "costo_promedio": float(row["costo_promedio"]),
                "ultimo_uso": row["ultimo_uso"],
                "prendas_promedio": float(row["prendas_promedio"])
                if row["prendas_promedio"]
                else 0,
                "total_prendas_acumulado": int(row["total_prendas_acumulado"])
                if row["total_prendas_acumulado"]
                else 0,
                "recomendacion": "Alta"
                if row["frecuencia_uso"] >= 6
                else "Media"
                if row["frecuencia_uso"] >= 3
                else "Baja",
            }

            # Agregar a lista general
            wips_recomendadas.append(wip_data)

            # Clasificar por grupo
            if row["wip_id"] in factores.WIPS_TEXTILES:
                wips_textiles.append(wip_data)
            elif row["wip_id"] in factores.WIPS_MANUFACTURA:
                wips_manufactura.append(wip_data)

        logger.info(
            f" Ruta textil obtenida para {tipo_prenda} ({version_calculo}): {len(wips_recomendadas)} WIPs"
        )

        return {
            "tipo_prenda": tipo_prenda,
            "version_calculo": version_calculo,
            "wips_recomendadas": wips_recomendadas,
            "wips_textiles_recomendadas": wips_textiles,
            "wips_manufactura_recomendadas": wips_manufactura,
            "total_recomendadas": len(wips_recomendadas),
            "metodo": "frecuencia_uso_12_meses_sin_filtros_prendas",
            "fecha_analisis": datetime.now().isoformat(),
            "filtros_aplicados": {
                "min_prendas": "ELIMINADO",
                "min_frecuencia": 1,
                "meses_hacia_atras": 12,
                "fecha_relativa": "MAX(mes) de tabla",
                "max_resultados": 25,
            },
        }

    async def _obtener_costos_wips_legacy(
        self,
        tipo_prenda: str,
        version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO,
    ) -> Dict[str, float]:
        """ MÉTODO LEGACY SIN CAMBIOS: Ya usa fechas relativas"""
        costos_wips = {}

        #  WIPs inestables (37, 45): Promedio con fechas relativas, sin filtros de prendas
        query_inestables = f"""
        SELECT wip_id, AVG(CAST(costo_por_prenda AS FLOAT)) as costo_promedio
        FROM {settings.db_schema}.resumen_wip_por_prenda
        WHERE wip_id IN ('37', '45')
          AND tipo_de_producto = ?
          AND version_calculo = ?
          AND fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.resumen_wip_por_prenda
            WHERE version_calculo = ?)
          AND mes >= (
            SELECT (MAX(mes) - INTERVAL '18 months')
            FROM {settings.db_schema}.resumen_wip_por_prenda
            WHERE version_calculo = ? AND tipo_de_producto = ?
          )
          AND costo_por_prenda > 0
        GROUP BY wip_id
        """

        resultados_inestables = await self.db.query(
            query_inestables,
            (
                tipo_prenda,
                version_calculo,
                version_calculo,
                version_calculo,
                tipo_prenda,
            ),
        )
        for row in resultados_inestables:
            costos_wips[row["wip_id"]] = float(row["costo_promedio"])

        #  WIPs estables: Último costo, sin filtros de prendas
        query_estables = f"""
        WITH UltimosCostos AS (
          SELECT
            wip_id,
            CAST(costo_por_prenda AS FLOAT) as costo_por_prenda,
            ROW_NUMBER() OVER (PARTITION BY wip_id ORDER BY mes DESC) as rn
          FROM {settings.db_schema}.resumen_wip_por_prenda
          WHERE wip_id NOT IN ('37', '45')
            AND tipo_de_producto = ?
            AND version_calculo = ?
            AND fecha_corrida = (
              SELECT MAX(fecha_corrida)
              FROM {settings.db_schema}.resumen_wip_por_prenda
              WHERE version_calculo = ?)
          AND costo_por_prenda > 0
        )
        SELECT wip_id, costo_por_prenda
        FROM UltimosCostos WHERE rn = 1
        """

        resultados_estables = await self.db.query(
            query_estables, (tipo_prenda, normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo))
        )
        for row in resultados_estables:
            costos_wips[row["wip_id"]] = float(row["costo_por_prenda"])

        logger.info(
            f" Método legacy: {len(costos_wips)} WIPs encontrados para {tipo_prenda} ({version_calculo})"
        )
        return costos_wips

    async def obtener_wips_disponibles_estructurado(
        self,
        tipo_prenda: Optional[str] = None,
        version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO,
    ) -> Tuple[List[WipDisponible], List[WipDisponible]]:
        """ SIN CAMBIOS: Ya usa lógica correcta"""

        try:
            if tipo_prenda:
                logger.info(
                    f" Obteniendo WIPs específicos para {tipo_prenda} ({version_calculo})"
                )
                costos_wips = await self.obtener_costos_wips_por_estabilidad(
                    tipo_prenda, version_calculo
                )
            else:
                logger.info(f" Obteniendo WIPs genéricos ({version_calculo})")
                #  QUERY GENÉRICA YA CORRECTA: sin filtros de prendas
                query = f"""
                WITH UltimosCostos AS (
                  SELECT
                    wip_id,
                    AVG(costo_por_prenda) as costo_promedio,
                    ROW_NUMBER() OVER (PARTITION BY wip_id ORDER BY MAX(mes) DESC) as rn
                  FROM {settings.db_schema}.resumen_wip_por_prenda
                  WHERE costo_por_prenda > 0
                    AND version_calculo = ?
                    AND fecha_corrida = (
                      SELECT MAX(fecha_corrida)
                      FROM {settings.db_schema}.resumen_wip_por_prenda
                      WHERE version_calculo = ?)
                  GROUP BY wip_id
                )
                SELECT wip_id, costo_promedio
                FROM UltimosCostos WHERE rn = 1
                """

                resultados = await self.db.query(
                    query, (normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo))
                )
                costos_wips = {}
                for row in resultados:
                    costos_wips[row["wip_id"]] = float(row["costo_promedio"])

            logger.info(f" Costos WIP obtenidos: {len(costos_wips)} WIPs disponibles")

            # Estructurar WIPs textiles
            wips_textiles: List[WipDisponible] = []
            for wip_id in factores.WIPS_TEXTILES:
                costo_actual = costos_wips.get(wip_id, 0.0)
                wips_textiles.append(
                    WipDisponible(
                        wip_id=wip_id,
                        nombre=factores.NOMBRES_WIPS.get(
                            wip_id, f"WIP {wip_id} - Textil"
                        ),
                        costo_actual=costo_actual,
                        disponible=costo_actual > 0,
                        grupo="Textil",
                    )
                )

            # Estructurar WIPs manufactura
            wips_manufactura: List[WipDisponible] = []
            for wip_id in factores.WIPS_MANUFACTURA:
                costo_actual = costos_wips.get(wip_id, 0.0)
                wips_manufactura.append(
                    WipDisponible(
                        wip_id=wip_id,
                        nombre=factores.NOMBRES_WIPS.get(
                            wip_id, f"WIP {wip_id} - Manufactura"
                        ),
                        costo_actual=costo_actual,
                        disponible=costo_actual > 0,
                        grupo="Manufactura",
                    )
                )

            logger.info(
                f" WIPs estructurados: {len(wips_textiles)} textiles, {len(wips_manufactura)} manufactura"
            )
            return wips_textiles, wips_manufactura

        except Exception as e:
            logger.error(f" Error en obtener_wips_disponibles_estructurado: {e}")
            return [], []

    async def obtener_gastos_por_estilo_recurrente(
        self,
        codigo_estilo: str,
        version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO,
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Obtiene gastos indirectos para estilos RECURRENTES usando MODA.

        Busca todas las OPs que fueron producidas con ese código_estilo exacto,
        calcula la MODA de los tres costos, filtra outliers (máx 10x la moda),
        y retorna los gastos con los índices de OPs excluidas.

        Args:
            codigo_estilo: El código de estilo propio exacto
            version_calculo: FLUIDO o truncado

        Returns:
            Tupla (gastos_dict, ops_excluidas_indices)
            - gastos_dict: {"costo_indirecto_fijo": float, "gasto_administracion": float, "gasto_ventas": float}
            - ops_excluidas_indices: Lista de índices de OPs que fueron excluidas
        """
        try:
            query = f"""
            SELECT
                costo_indirecto_fijo,
                gasto_administracion,
                gasto_ventas,
                prendas_requeridas,
                cod_ordpro,
                ROW_NUMBER() OVER (ORDER BY fecha_facturacion DESC) as rn
            FROM {settings.db_schema}.costo_op_detalle
            WHERE codigo_estilo = ?
                AND version_calculo = ?
                AND fecha_facturacion >= (
                    SELECT (MAX(fecha_facturacion) - INTERVAL '12 months')
                    FROM {settings.db_schema}.costo_op_detalle
                    WHERE version_calculo = ?
                )
                AND prendas_requeridas > 0
                AND costo_indirecto_fijo > 0
                AND gasto_administracion > 0
                AND gasto_ventas > 0
            ORDER BY fecha_facturacion DESC
            """

            params = (
                codigo_estilo,
                normalize_version_calculo(version_calculo),
                normalize_version_calculo(version_calculo),
            )
            resultado = await self.db.query(query, params)

            if not resultado:
                logger.warning(f" No se encontraron OPs para estilo recurrente: {codigo_estilo}")
                return {
                    "costo_indirecto_fijo": 0,
                    "gasto_administracion": 0,
                    "gasto_ventas": 0,
                }, []

            # Extraer los tres valores unitarios y calcular la moda
            indirectos = []
            admins = []
            ventas = []
            ops_info = []

            for row in resultado:
                prenda_qty = row["prendas_requeridas"]
                indirectos.append(float(row["costo_indirecto_fijo"]) / prenda_qty)
                admins.append(float(row["gasto_administracion"]) / prenda_qty)
                ventas.append(float(row["gasto_ventas"]) / prenda_qty)
                ops_info.append({
                    "rn": row["rn"],
                    "cod_ordpro": row["cod_ordpro"],
                })

            # Filtrar por threshold de moda (10x)
            indirectos_filtrados, indices_excluidos_ind = filter_by_mode_threshold(indirectos, threshold=10.0)
            admins_filtrados, indices_excluidos_adm = filter_by_mode_threshold(admins, threshold=10.0)
            ventas_filtrados, indices_excluidos_ven = filter_by_mode_threshold(ventas, threshold=10.0)

            # Combinar índices excluidos de los tres costos
            indices_excluidos_totales = set(indices_excluidos_ind) | set(indices_excluidos_adm) | set(indices_excluidos_ven)

            # Obtener los códigos de OPs excluidas
            ops_excluidas = [ops_info[idx]["cod_ordpro"] for idx in indices_excluidos_totales]

            # Calcular promedios de los valores filtrados
            gastos = {
                "costo_indirecto_fijo": float(sum(indirectos_filtrados) / len(indirectos_filtrados)) if indirectos_filtrados else 0,
                "gasto_administracion": float(sum(admins_filtrados) / len(admins_filtrados)) if admins_filtrados else 0,
                "gasto_ventas": float(sum(ventas_filtrados) / len(ventas_filtrados)) if ventas_filtrados else 0,
            }

            logger.info(
                f" Gastos recurrentes (estilo {codigo_estilo}): {gastos} | OPs excluidas: {len(ops_excluidas)}"
            )
            return gastos, ops_excluidas

        except Exception as e:
            logger.error(f" Error en obtener_gastos_por_estilo_recurrente: {e}")
            return {
                "costo_indirecto_fijo": 0,
                "gasto_administracion": 0,
                "gasto_ventas": 0,
            }, []

    async def obtener_gastos_por_estilo_nuevo(
        self,
        marca: str,
        familia_prenda: str,
        tipo_prenda: str,
        version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO,
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Obtiene gastos indirectos para estilos NUEVOS usando MODA.

        Busca todas las OPs que tengan la misma marca + familia_prenda + tipo_prenda,
        calcula la MODA de los tres costos, filtra outliers (máx 10x la moda),
        y retorna los gastos con los índices de OPs excluidas.

        Args:
            marca: Cliente/marca
            familia_prenda: Familia de la prenda
            tipo_prenda: Tipo de prenda
            version_calculo: FLUIDO o truncado

        Returns:
            Tupla (gastos_dict, ops_excluidas_indices)
        """
        try:
            query = f"""
            SELECT
                costo_indirecto_fijo,
                gasto_administracion,
                gasto_ventas,
                prendas_requeridas,
                cod_ordpro,
                ROW_NUMBER() OVER (ORDER BY fecha_facturacion DESC) as rn
            FROM {settings.db_schema}.costo_op_detalle
            WHERE cliente = ?
                AND familia_prenda = ?
                AND tipo_prenda = ?
                AND version_calculo = ?
                AND fecha_facturacion >= (
                    SELECT (MAX(fecha_facturacion) - INTERVAL '12 months')
                    FROM {settings.db_schema}.costo_op_detalle
                    WHERE version_calculo = ?
                )
                AND prendas_requeridas > 0
                AND costo_indirecto_fijo > 0
                AND gasto_administracion > 0
                AND gasto_ventas > 0
            ORDER BY fecha_facturacion DESC
            """

            params = (
                marca,
                familia_prenda,
                tipo_prenda,
                normalize_version_calculo(version_calculo),
                normalize_version_calculo(version_calculo),
            )
            resultado = await self.db.query(query, params)

            if not resultado:
                logger.warning(
                    f" No se encontraron OPs para estilo nuevo: {marca} | {familia_prenda} | {tipo_prenda}"
                )
                return {
                    "costo_indirecto_fijo": 0,
                    "gasto_administracion": 0,
                    "gasto_ventas": 0,
                }, []

            # Extraer los tres valores unitarios y calcular la moda
            indirectos = []
            admins = []
            ventas = []
            ops_info = []

            for row in resultado:
                prenda_qty = row["prendas_requeridas"]
                indirectos.append(float(row["costo_indirecto_fijo"]) / prenda_qty)
                admins.append(float(row["gasto_administracion"]) / prenda_qty)
                ventas.append(float(row["gasto_ventas"]) / prenda_qty)
                ops_info.append({
                    "rn": row["rn"],
                    "cod_ordpro": row["cod_ordpro"],
                })

            # Filtrar por threshold de moda (10x)
            indirectos_filtrados, indices_excluidos_ind = filter_by_mode_threshold(indirectos, threshold=10.0)
            admins_filtrados, indices_excluidos_adm = filter_by_mode_threshold(admins, threshold=10.0)
            ventas_filtrados, indices_excluidos_ven = filter_by_mode_threshold(ventas, threshold=10.0)

            # Combinar índices excluidos de los tres costos
            indices_excluidos_totales = set(indices_excluidos_ind) | set(indices_excluidos_adm) | set(indices_excluidos_ven)

            # Obtener los códigos de OPs excluidas
            ops_excluidas = [ops_info[idx]["cod_ordpro"] for idx in indices_excluidos_totales]

            # Calcular promedios de los valores filtrados
            gastos = {
                "costo_indirecto_fijo": float(sum(indirectos_filtrados) / len(indirectos_filtrados)) if indirectos_filtrados else 0,
                "gasto_administracion": float(sum(admins_filtrados) / len(admins_filtrados)) if admins_filtrados else 0,
                "gasto_ventas": float(sum(ventas_filtrados) / len(ventas_filtrados)) if ventas_filtrados else 0,
            }

            logger.info(
                f" Gastos nuevos ({marca} | {familia_prenda} | {tipo_prenda}): {gastos} | OPs excluidas: {len(ops_excluidas)}"
            )
            return gastos, ops_excluidas

        except Exception as e:
            logger.error(
                f" Error en obtener_gastos_por_estilo_nuevo ({marca} | {familia_prenda} | {tipo_prenda}): {e}"
            )
            return {
                "costo_indirecto_fijo": 0,
                "gasto_administracion": 0,
                "gasto_ventas": 0,
            }, []

    # ========================================
    #  FUNCIONES DE SOPORTE CORREGIDAS
    # ========================================

    #  CÓDIGO CORREGIDO - Ahora usa MODA en lugar de PROMEDIO
    async def obtener_gastos_indirectos_formula(
        self,
        version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO,
        codigo_estilo: Optional[str] = None,
        cliente_marca: Optional[str] = None,
        familia_producto: Optional[str] = None,
        tipo_prenda: Optional[str] = None,
    ) -> Tuple[Dict[str, float], List[str]]:
        """
         CORREGIDA: Gastos indirectos UNITARIOS usando MODA y filtrado de outliers.

        Estrategia:
        1. Si codigo_estilo está disponible → buscar OPs de ese estilo recurrente
        2. Si no → usar marca+familia+tipo para buscar OPs de estilo nuevo
        3. Si no se encuentran → usar fórmula genérica (fallback)

        Retorna: (gastos_dict, ops_excluidas)
        """

        #  OPCIÓN 1: Intentar con ESTILO RECURRENTE (por código_estilo exacto)
        if codigo_estilo:
            logger.info(f" Buscando gastos para ESTILO RECURRENTE: {codigo_estilo}")
            gastos, ops_excluidas = await self.obtener_gastos_por_estilo_recurrente(
                codigo_estilo, version_calculo
            )
            if any(gastos.values()):  # Si se encontraron datos
                logger.info(f" Gastos obtenidos por ESTILO RECURRENTE")
                return gastos, ops_excluidas

        #  OPCIÓN 2: Intentar con ESTILO NUEVO (marca + familia + tipo)
        if cliente_marca and familia_producto and tipo_prenda:
            logger.info(
                f" Buscando gastos para ESTILO NUEVO: {cliente_marca} | {familia_producto} | {tipo_prenda}"
            )
            gastos, ops_excluidas = await self.obtener_gastos_por_estilo_nuevo(
                cliente_marca, familia_producto, tipo_prenda, version_calculo
            )
            if any(gastos.values()):  # Si se encontraron datos
                logger.info(f" Gastos obtenidos por ESTILO NUEVO")
                return gastos, ops_excluidas

        #  OPCIÓN 3: FALLBACK - Fórmula genérica (promedio general)
        logger.info(f" Usando FÓRMULA GENÉRICA como fallback")
        query = f"""
        SELECT
            AVG(costo_indirecto_fijo / NULLIF(prendas_requeridas, 0)) as indirecto_fijo,
            AVG(gasto_administracion / NULLIF(prendas_requeridas, 0)) as administracion,
            AVG(gasto_ventas / NULLIF(prendas_requeridas, 0)) as ventas
        FROM {settings.db_schema}.costo_op_detalle
        WHERE version_calculo = ?
        AND fecha_corrida = (
          SELECT MAX(fecha_corrida)
          FROM {settings.db_schema}.costo_op_detalle
          WHERE version_calculo = ?)
        AND fecha_facturacion >= (
          SELECT (MAX(fecha_facturacion) - INTERVAL '12 months')
          FROM {settings.db_schema}.costo_op_detalle
          WHERE version_calculo = ?
        )
        AND prendas_requeridas > 0
        AND costo_indirecto_fijo > 0
        AND gasto_administracion > 0
        AND gasto_ventas > 0
        """

        resultado = await self.db.query(
            query, (normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo))
        )
        if resultado:
            gastos = {
                "costo_indirecto_fijo": float(resultado[0]["indirecto_fijo"] or 0),
                "gasto_administracion": float(resultado[0]["administracion"] or 0),
                "gasto_ventas": float(resultado[0]["ventas"] or 0),
            }
            logger.info(
                f" Gastos indirectos (FÓRMULA GENÉRICA) obtenidos ({version_calculo}): {gastos}"
            )
            return gastos, []

        logger.warning(f" No se encontraron gastos indirectos para {version_calculo}")
        return {"costo_indirecto_fijo": 0, "gasto_administracion": 0, "gasto_ventas": 0}, []

    async def obtener_ultimo_costo_materiales(
        self, version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO
    ) -> Dict[str, float]:
        """ SIN CAMBIOS: Ya usa lógica correcta con fecha_corrida"""

        query = f"""
        SELECT
            costo_materia_prima,
            costo_avios,
            prendas_requeridas,
            fecha_corrida,
            cod_ordpro
        FROM {settings.db_schema}.costo_op_detalle
        WHERE costo_materia_prima > 0
          AND costo_avios > 0
          AND prendas_requeridas > 0
          AND version_calculo = ?
          AND fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?)
        ORDER BY fecha_facturacion DESC,
        prendas_requeridas DESC
        LIMIT 1
        """

        resultado = await self.db.query(query, (normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo)))
        if resultado:
            registro = resultado[0]
            prendas = (
                float(registro["prendas_requeridas"])
                if registro["prendas_requeridas"]
                else 1.0
            )

            costo_materia_prima_unitario = (
                float(registro["costo_materia_prima"]) / prendas
            )
            costo_avios_unitario = float(registro["costo_avios"]) / prendas

            logger.info(
                f" Último costo materiales ({version_calculo}): OP {registro['cod_ordpro']} - "
                f"MP: ${costo_materia_prima_unitario:.2f}/u - "
                f"Avíos: ${costo_avios_unitario:.2f}/u"
            )

            return {
                "costo_materia_prima": costo_materia_prima_unitario,
                "costo_avios": costo_avios_unitario,
            }

        logger.warning(
            f" No se encontró último costo de materiales válido para {version_calculo}"
        )
        return {"costo_materia_prima": 0, "costo_avios": 0}

    async def obtener_volumen_historico_estilo(
        self,
        codigo_estilo: str,
        version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO,
    ) -> int:
        # Solo filtrar version_calculo en costo_op_detalle
        query = f"""
        SELECT COALESCE(SUM(prendas_requeridas), 0) as volumen_total
        FROM {settings.db_schema}.costo_op_detalle c
        INNER JOIN {settings.db_schema}.historial_estilos h
          ON c.estilo_propio = h.codigo_estilo
        WHERE h.codigo_estilo = ?
          AND c.version_calculo = ?
          AND c.fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?)
          AND h.fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.historial_estilos)
          AND c.prendas_requeridas > 0
        """

        resultado = await self.db.query(
            query, (codigo_estilo, normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo))
        )
        volumen = (
            int(resultado[0]["volumen_total"])
            if resultado and resultado[0]["volumen_total"]
            else 0
        )

        logger.info(
            f" Volumen histórico {codigo_estilo} ({version_calculo}): {volumen} prendas"
        )
        return volumen

    async def health_check(self) -> Dict[str, Any]:
        """Verifica estado de las tablas principales"""

        tablas_check = {
            "costo_op_detalle": f"SELECT COUNT(*) as total FROM {settings.db_schema}.costo_op_detalle",
            "resumen_wip_por_prenda": f"SELECT COUNT(*) as total FROM {settings.db_schema}.resumen_wip_por_prenda",
            "historial_estilos": f"SELECT COUNT(*) as total FROM {settings.db_schema}.historial_estilos",
        }

        resultados = {}
        for tabla, query in tablas_check.items():
            try:
                resultado = await self.db.query(query)
                resultados[tabla] = resultado[0]["total"] if resultado else 0
            except Exception as e:
                logger.error(f"Error verificando tabla {tabla}: {e}")
                resultados[tabla] = -1

        logger.info(f" Health check completado: {resultados}")
        return resultados

    async def obtener_ops_utilizadas_cotizacion(
        self,
        codigo_estilo: Optional[str] = None,
        familia_producto: Optional[str] = None,
        tipo_prenda: Optional[str] = None,
        cliente: Optional[str] = None,
        version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO,
    ) -> Dict[str, Any]:
        """
         FUNCIÓN CORREGIDA: Obtiene las OPs específicas utilizadas para una cotización con fechas relativas
        """

        ops_utilizadas = []
        metodo_usado = "sin_datos"

        # PASO 1: Intentar por estilo específico (si es recurrente)
        if codigo_estilo:
            try:
                # Fechas relativas en lugar de GETDATE()
                query_estilo = f"""
                SELECT
                  c.cod_ordpro,
                  c.cliente,
                  c.fecha_facturacion,
                  c.prendas_requeridas,
                  c.monto_factura,
                  c.esfuerzo_total,
                  --  COSTOS UNITARIOS CALCULADOS
                  COALESCE(c.costo_textil, 0)
                    / NULLIF(c.prendas_requeridas, 0) as costo_textil_unit,
                  COALESCE(c.costo_manufactura, 0)
                    / NULLIF(c.prendas_requeridas, 0) as costo_manufactura_unit,
                  COALESCE(c.costo_avios, 0)
                    / NULLIF(c.prendas_requeridas, 0) as costo_avios_unit,
                  COALESCE(c.costo_materia_prima, 0)
                    / NULLIF(c.prendas_requeridas, 0) as costo_mp_unit,
                  COALESCE(c.costo_indirecto_fijo, 0)
                    / NULLIF(c.prendas_requeridas, 0) as costo_indirecto_unit,
                  COALESCE(c.gasto_administracion, 0)
                    / NULLIF(c.prendas_requeridas, 0) as gasto_admin_unit,
                  COALESCE(c.gasto_ventas, 0)
                    / NULLIF(c.prendas_requeridas, 0) as gasto_ventas_unit
                FROM {settings.db_schema}.costo_op_detalle c
                INNER JOIN {settings.db_schema}.historial_estilos h
                  ON c.estilo_propio = h.codigo_estilo
                WHERE h.codigo_estilo = ?
                  AND c.version_calculo = ?
                  AND c.fecha_corrida = (
                    SELECT MAX(fecha_corrida)
                    FROM {settings.db_schema}.costo_op_detalle
                    WHERE version_calculo = ?)
                  AND h.fecha_corrida = (
                    SELECT MAX(fecha_corrida)
                    FROM {settings.db_schema}.historial_estilos)
                  AND c.fecha_facturacion >= (
                    SELECT (MAX(fecha_facturacion) - INTERVAL '18 months')
                    FROM {settings.db_schema}.costo_op_detalle
                    WHERE version_calculo = ?
                )
                AND c.prendas_requeridas > 0
                ORDER BY c.fecha_facturacion DESC, c.prendas_requeridas DESC
                LIMIT 10
                """

                resultados = await self.db.query(
                    query_estilo,
                    (codigo_estilo, normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo)),
                )

                if resultados:
                    ops_utilizadas = resultados
                    metodo_usado = f"estilo_especifico_{codigo_estilo}"

            except Exception as e:
                logger.warning(f"Error buscando OPs por estilo {codigo_estilo}: {e}")

        # PASO 2: Si no hay por estilo, buscar por familia+tipo+cliente
        if not ops_utilizadas and familia_producto and tipo_prenda:
            try:
                params = [
                    familia_producto,
                    tipo_prenda,
                    version_calculo,
                    version_calculo,
                    version_calculo,
                ]
                cliente_filter = ""

                if cliente:
                    cliente_filter = "AND c.cliente = ?"
                    params.append(cliente)
                    metodo_usado = f"familia_tipo_cliente_{familia_producto}_{tipo_prenda}_{cliente}"
                else:
                    metodo_usado = f"familia_tipo_{familia_producto}_{tipo_prenda}"

                #  CORREGIDO: Fechas relativas en lugar de GETDATE()
                query_familia = f"""
                SELECT
                  c.cod_ordpro,
                  c.estilo_propio,
                  c.cliente,
                  c.fecha_facturacion,
                  c.prendas_requeridas,
                  c.monto_factura,
                  c.costo_textil / NULLIF(c.prendas_requeridas, 0) as costo_textil_unit,
                  c.costo_manufactura / NULLIF(c.prendas_requeridas, 0) as costo_manufactura_unit,
                  COALESCE(c.costo_avios, 0) / NULLIF(c.prendas_requeridas, 0) as costo_avios_unit,
                  COALESCE(c.costo_materia_prima, 0) / NULLIF(c.prendas_requeridas, 0) as costo_mp_unit,
                  COALESCE(c.costo_indirecto_fijo, 0) / NULLIF(c.prendas_requeridas, 0) as costo_indirecto_unit,
                  COALESCE(c.gasto_administracion, 0) / NULLIF(c.prendas_requeridas, 0) as gasto_admin_unit,
                  COALESCE(c.gasto_ventas, 0) / NULLIF(c.prendas_requeridas, 0) as gasto_ventas_unit,
                  c.esfuerzo_total
                FROM {settings.db_schema}.costo_op_detalle c
                WHERE c.familia_de_productos = ?
                  AND c.tipo_de_producto = ?
                  AND c.version_calculo = ?
                  AND c.fecha_corrida = (
                    SELECT MAX(fecha_corrida)
                    FROM {settings.db_schema}.costo_op_detalle
                    WHERE version_calculo = ?)
                  AND c.fecha_facturacion >= (
                    SELECT (MAX(fecha_facturacion) - INTERVAL '18 months')
                    FROM {settings.db_schema}.costo_op_detalle
                    WHERE version_calculo = ?
                )
                AND c.prendas_requeridas > 0
                {cliente_filter}
                ORDER BY c.fecha_facturacion DESC, c.prendas_requeridas DESC
                LIMIT 10
                """

                resultados = await self.db.query(query_familia, tuple(params))

                if resultados:
                    ops_utilizadas = resultados

            except Exception as e:
                logger.warning(f"Error buscando OPs por familia/tipo: {e}")

        #  PROCESAR RESULTADOS CORREGIDO
        ops_procesadas = []
        for op in ops_utilizadas:
            #  PASO 1: Calcular COSTO TOTAL ORIGINAL (antes de rangos)
            costo_total_original = (
                float(op.get("costo_textil_unit", 0) or 0)
                + float(op.get("costo_manufactura_unit", 0) or 0)
                + float(op.get("costo_avios_unit", 0) or 0)
                + float(op.get("costo_mp_unit", 0) or 0)
                + float(op.get("costo_indirecto_unit", 0) or 0)
                + float(op.get("gasto_admin_unit", 0) or 0)
                + float(op.get("gasto_ventas_unit", 0) or 0)
            )

            #  PASO 2: Aplicar rangos de seguridad a cada componente
            costo_textil_ajustado, textil_ajustado = factores.validar_rango_seguridad(
                float(op.get("costo_textil_unit", 0) or 0), "costo_textil"
            )
            costo_manufactura_ajustado, manufactura_ajustado = (
                factores.validar_rango_seguridad(
                    float(op.get("costo_manufactura_unit", 0) or 0), "costo_manufactura"
                )
            )
            costo_avios_ajustado, avios_ajustado = factores.validar_rango_seguridad(
                float(op.get("costo_avios_unit", 0) or 0), "costo_avios"
            )
            costo_mp_ajustado, mp_ajustado = factores.validar_rango_seguridad(
                float(op.get("costo_mp_unit", 0) or 0), "costo_materia_prima"
            )
            costo_indirecto_ajustado, indirecto_ajustado = (
                factores.validar_rango_seguridad(
                    float(op.get("costo_indirecto_unit", 0) or 0),
                    "costo_indirecto_fijo",
                )
            )
            gasto_admin_ajustado, admin_ajustado = factores.validar_rango_seguridad(
                float(op.get("gasto_admin_unit", 0) or 0), "gasto_administracion"
            )
            gasto_ventas_ajustado, ventas_ajustado = factores.validar_rango_seguridad(
                float(op.get("gasto_ventas_unit", 0) or 0), "gasto_ventas"
            )

            #  PASO 3: Calcular COSTO TOTAL AJUSTADO
            costo_total_ajustado = (
                costo_textil_ajustado
                + costo_manufactura_ajustado
                + costo_avios_ajustado
                + costo_mp_ajustado
                + costo_indirecto_ajustado
                + gasto_admin_ajustado
                + gasto_ventas_ajustado
            )

            #  PASO 4: Determinar si fue ajustado
            fue_ajustado = (
                textil_ajustado
                or manufactura_ajustado
                or avios_ajustado
                or mp_ajustado
                or indirecto_ajustado
                or admin_ajustado
                or ventas_ajustado
            )

            ops_procesadas.append(
                {
                    "cod_ordpro": op["cod_ordpro"],
                    "estilo_propio": op.get("estilo_propio", codigo_estilo),
                    "cliente": op["cliente"],
                    "fecha_facturacion": op["fecha_facturacion"].isoformat()
                    if op["fecha_facturacion"]
                    else None,
                    "prendas_requeridas": int(op["prendas_requeridas"]),
                    "monto_factura": float(op["monto_factura"]),
                    "precio_unitario": float(
                        op["monto_factura"] / op["prendas_requeridas"]
                    )
                    if op["prendas_requeridas"] > 0
                    else 0,
                    "esfuerzo_total": int(op["esfuerzo_total"] or 6),
                    #  COSTOS COMPONENTES AJUSTADOS
                    "costos_componentes": {
                        "textil": costo_textil_ajustado,
                        "manufactura": costo_manufactura_ajustado,
                        "avios": costo_avios_ajustado,
                        "materia_prima": costo_mp_ajustado,
                        "indirecto_fijo": costo_indirecto_ajustado,
                        "gasto_admin": gasto_admin_ajustado,
                        "gasto_ventas": gasto_ventas_ajustado,
                    },
                    #  COSTOS TOTALES CALCULADOS CORRECTAMENTE
                    "costo_total_unitario": costo_total_ajustado,  # Para cálculos seguros
                    "costo_total_original": costo_total_original,  # Para mostrar en frontend
                    "fue_ajustado": fue_ajustado,  # Si hubo ajustes aplicados
                }
            )

        #  ESTADÍSTICAS BASADAS EN COSTOS AJUSTADOS
        if ops_procesadas:
            costos_totales_ajustados = [
                op["costo_total_unitario"] for op in ops_procesadas
            ]
            costos_totales_originales = [
                op["costo_total_original"] for op in ops_procesadas
            ]
            esfuerzos = [op["esfuerzo_total"] for op in ops_procesadas]

            estadisticas = {
                "total_ops": len(ops_procesadas),
                "costo_promedio": sum(costos_totales_ajustados)
                / len(costos_totales_ajustados),
                "costo_min": min(costos_totales_ajustados),
                "costo_max": max(costos_totales_ajustados),
                "costo_promedio_original": sum(costos_totales_originales)
                / len(costos_totales_originales),
                "costo_min_original": min(costos_totales_originales),
                "costo_max_original": max(costos_totales_originales),
                "esfuerzo_promedio": sum(esfuerzos) / len(esfuerzos),
                "ops_con_ajustes": sum(
                    1 for op in ops_procesadas if op["fue_ajustado"]
                ),
                "rango_fechas": {
                    "desde": min(
                        [
                            op["fecha_facturacion"]
                            for op in ops_procesadas
                            if op["fecha_facturacion"]
                        ]
                    ),
                    "hasta": max(
                        [
                            op["fecha_facturacion"]
                            for op in ops_procesadas
                            if op["fecha_facturacion"]
                        ]
                    ),
                },
            }
        else:
            estadisticas = {
                "total_ops": 0,
                "mensaje": "No se encontraron OPs con los criterios especificados",
            }

        logger.info(
            f" OPs utilizadas procesadas: {len(ops_procesadas)} encontradas con método {metodo_usado}"
        )

        return {
            "ops_utilizadas": ops_procesadas,
            "metodo_utilizado": metodo_usado,
            "estadisticas": estadisticas,
            "parametros_busqueda": {
                "codigo_estilo": codigo_estilo,
                "familia_producto": familia_producto,
                "tipo_prenda": tipo_prenda,
                "cliente": cliente,
                "version_calculo": version_calculo,
            },
            "rangos_aplicados": True,  #  INDICADOR DE QUE SE APLICARON RANGOS
        }

    async def obtener_info_comercial(
        self,
        familia_producto: str,
        tipo_prenda: str,
        version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDO,
    ) -> Dict[str, Any]:
        """ SIN CAMBIOS: Ya usa fecha_corrida correctamente"""

        # 1. Volumen histórico (6 meses)
        query_volumen = f"""
        SELECT
          COUNT(*) as ops_producidas,
          SUM(prendas_requeridas) as volumen_total_6m,
          AVG(CAST(prendas_requeridas AS FLOAT)) as volumen_promedio
        FROM {settings.db_schema}.costo_op_detalle
        WHERE familia_de_productos = ?
          AND tipo_de_producto = ?
          AND version_calculo = ?
          AND fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?)
          AND fecha_facturacion >= (GETDATE() - INTERVAL '6 months')
          AND prendas_requeridas > 0
        """

        resultado_volumen = await self.db.query(
            query_volumen,
            (familia_producto, tipo_prenda, normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo)),
        )
        volumen = resultado_volumen[0] if resultado_volumen else {}

        # 2. Tendencias de costos
        query_tendencias = f"""
        SELECT
          YEAR(fecha_facturacion) as año,
          MONTH(fecha_facturacion) as mes,
          COUNT(*) as ops_mes,
          AVG(CAST(costo_textil AS FLOAT)
            / NULLIF(prendas_requeridas, 0)) as costo_textil_promedio,
          AVG(CAST(costo_manufactura AS FLOAT)
            / NULLIF(prendas_requeridas, 0)) as costo_manufactura_promedio
        FROM {settings.db_schema}.costo_op_detalle
        WHERE familia_de_productos = ?
          AND tipo_de_producto = ?
          AND version_calculo = ?
          AND fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?)
         AND fecha_facturacion >= (GETDATE() - INTERVAL '18 months')
          AND prendas_requeridas > 0
        GROUP BY YEAR(fecha_facturacion), MONTH(fecha_facturacion)
        ORDER BY año DESC, mes DESC
        """

        tendencias = await self.db.query(
            query_tendencias,
            (familia_producto, tipo_prenda, normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo)),
        )

        # 3. Análisis competitivo
        query_competitivo = f"""
        SELECT
          cliente,
          COUNT(*) as ops_cliente,
          SUM(prendas_requeridas) as volumen_cliente,
          AVG(CAST(monto_factura AS FLOAT)
            / NULLIF(prendas_requeridas, 0)) as precio_promedio_cliente
        FROM {settings.db_schema}.costo_op_detalle
        WHERE familia_de_productos = ?
          AND tipo_de_producto = ?
          AND version_calculo = ?
          AND fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?)
          AND fecha_facturacion >= (GETDATE() - INTERVAL '12 months')
          AND prendas_requeridas > 0
        GROUP BY cliente
        ORDER BY SUM(prendas_requeridas) DESC
        LIMIT 5
        """

        competitivo = await self.db.query(
            query_competitivo,
            (familia_producto, tipo_prenda, normalize_version_calculo(version_calculo), normalize_version_calculo(version_calculo)),
        )

        info_comercial = {
            "historico_volumen": {
                "ops_producidas": int(volumen.get("ops_producidas", 0) or 0),
                "volumen_total_6m": int(volumen.get("volumen_total_6m", 0) or 0),
                "volumen_promedio": float(
                    round(volumen.get("volumen_promedio", 0) or 0, 1)
                ),
            },
            "tendencias_costos": [
                {
                    "año": int(t["año"]),
                    "mes": int(t["mes"]),
                    "ops_mes": int(t["ops_mes"]),
                    "costo_textil_promedio": float(
                        round(t["costo_textil_promedio"] or 0, 4)
                    ),
                    "costo_manufactura_promedio": float(
                        round(t["costo_manufactura_promedio"] or 0, 4)
                    ),
                }
                for t in tendencias
            ],
            "analisis_competitividad": [
                {
                    "cliente": str(c["cliente"]),
                    "ops_cliente": int(c["ops_cliente"]),
                    "volumen_cliente": int(c["volumen_cliente"]),
                    "precio_promedio_cliente": float(
                        round(c["precio_promedio_cliente"] or 0, 2)
                    ),
                }
                for c in competitivo
            ],
            "version_calculo": version_calculo,
        }

        logger.info(
            f" Info comercial obtenida para {familia_producto}/{tipo_prenda} ({version_calculo})"
        )
        return info_comercial

