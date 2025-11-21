"""
=====================================================================
APLICACIN FASTAPI PRINCIPAL - BACKEND TDV COTIZADOR - COMPLETAMENTE CORREGIDO
=====================================================================
[OK] Nuevos endpoints agregados:
- /verificar-estilo-completo/{codigo_estilo} - Auto-completado completo
- /ops-utilizadas-cotizacion - OPs reales utilizadas
[OK] Todos los endpoints corregidos con version_calculo
[OK] Manejo mejorado de errores y logging
"""

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse as FastAPIJSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json
import pyodbc
from decimal import Decimal

# Imports locales
from .config import settings, factores
from .models import (
    CotizacionInput,
    CotizacionResponse,
    EstiloSimilar,
    HealthCheck,
    ConfiguracionResponse,
    WipsDisponiblesResponse,
    VersionCalculo,
)
from .database import TDVQueries
from .utils import cotizador_tdv

logger = logging.getLogger(__name__)


# =====================================================================
# VALIDADOR PARA version_calculo EN QUERY PARAMS
# =====================================================================
def normalize_version_calculo(version_str: Optional[str]) -> str:
    """
    Normaliza version_calculo de query parameters a valor de BD.
    Acepta "FLUIDO" o "FLUIDA" (del frontend/API) y retorna "FLUIDA" (valor en BD)
    Acepta "truncado" y retorna "truncado" (valor en BD)
    """
    if not version_str:
        return "FLUIDA"

    version_upper = version_str.upper()

    # Aceptar tanto "FLUIDO" como "FLUIDA" pero retornar "FLUIDA" (valor en BD)
    if version_upper in ("FLUIDO", "FLUIDA"):
        return "FLUIDA"
    elif version_upper == "TRUNCADO":
        return "truncado"
    else:
        # Si no es válido, retornar FLUIDA por defecto
        logger.warning(f"version_calculo no válida: {version_str}, usando FLUIDA")
        return "FLUIDA"


tdv_queries: TDVQueries = TDVQueries.get_instance()


# SERIALIZADOR JSON PERSONALIZADO
class JSONEncoder(json.JSONEncoder):
    """Encoder JSON personalizado para manejar datetime y Decimal"""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


# RESPUESTA JSON PERSONALIZADA
class CustomJSONResponse(FastAPIJSONResponse):
    """JSONResponse personalizada que maneja datetime y Decimal"""

    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=JSONEncoder,
        ).encode("utf-8")


# =====================================================================
# CONFIGURACIN FASTAPI
# =====================================================================

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Sistema de cotizacin inteligente basado en metodologa WIP para TDV - COMPLETAMENTE CORREGIDO",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS
origins = settings.cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# MANEJADORES DE ERRORES CORREGIDOS
# =====================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Manejador de excepciones HTTP corregido"""
    error_response = {
        "error": "HTTP_ERROR",
        "mensaje": exc.detail,
        "detalles": {"status_code": exc.status_code},
        "timestamp": datetime.now().isoformat(),
    }
    return CustomJSONResponse(status_code=exc.status_code, content=error_response)


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Manejador de errores de valor corregido"""
    error_response = {
        "error": "VALUE_ERROR",
        "mensaje": str(exc),
        "detalles": {"tipo": "ValueError"},
        "timestamp": datetime.now().isoformat(),
    }
    return CustomJSONResponse(status_code=400, content=error_response)


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Manejador general de excepciones corregido"""
    logger.error(f"Error no manejado: {exc}")
    error_response = {
        "error": "INTERNAL_ERROR",
        "mensaje": "Error interno del servidor",
        "detalles": {"tipo": type(exc).__name__},
        "timestamp": datetime.now().isoformat(),
    }
    return CustomJSONResponse(status_code=500, content=error_response)


# =====================================================================
# ENDPOINTS PRINCIPALES
# =====================================================================


@app.get("/", tags=["General"])
async def root():
    """Endpoint raz con informacin del sistema"""
    return {
        "sistema": "Cotizador TDV Expert",
        "version": settings.api_version,
        "status": "activo",
        "arquitectura": "TDV Real Database",
        "features": [
            "[OK] CORREGIDO: Bsqueda mejorada en costo_op_detalle",
            "[OK] CORREGIDO: Configurador WIPs desde resumen_wip_por_prenda",
            "[OK] CORREGIDO: Categorizacin automtica de estilos",
            "[OK] NUEVO: Auto-completado inteligente para estilos recurrentes",
            "[OK] NUEVO: Endpoint OPs reales utilizadas",
            "[OK] CORREGIDO: Manejo completo de versiones de clculo",
            "[OK] CORREGIDO: Rutas textiles restauradas",
            "Factores de ajuste basados en anlisis TDV",
            "Informacin comercial avanzada",
            "Anlisis inteligente WIPs por estabilidad + fecha_corrida",
        ],
        "versiones_calculo_soportadas": ["FLUIDO", "truncado"],
        "endpoints_nuevos": [
            "/verificar-estilo-completo/{codigo_estilo}",
            "/ops-utilizadas-cotizacion",
        ],
        "timestamp": datetime.now(),
    }


@app.get("/health", response_model=HealthCheck, tags=["General"])
async def health_check():
    """Verificacin de estado del sistema y BD"""
    try:
        tablas_status = await tdv_queries.health_check()

        estado_general = (
            "healthy"
            if all(count >= 0 for count in tablas_status.values())
            else "degraded"
        )
        estado_bd = (
            "connected"
            if all(count >= 0 for count in tablas_status.values())
            else "error"
        )

        return HealthCheck(
            status=estado_general,
            database=estado_bd,
            tablas=tablas_status,
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Error en health check: {e}")
        raise HTTPException(status_code=503, detail=f"Sistema no disponible: {str(e)}")


# =====================================================================
#  NUEVOS ENDPOINTS CRTICOS
# =====================================================================


@app.get("/verificar-estilo-completo/{codigo_estilo}", tags=["Bsqueda"])
async def verificar_estilo_completo_con_autocompletado(
    codigo_estilo: str,
    version_calculo: Optional[str] = None,
):
    """
    [OK] NUEVO ENDPOINT: Verificacin completa de estilo con auto-completado

    Este endpoint proporciona:
    1. Verificacin si es nuevo/recurrente
    2. Auto-completado de familia_producto y tipo_prenda
    3. Informacin detallada del estilo
    4. Volumen histrico y categorizacin
    """
    try:
        # Normalizar version_calculo (acepta FLUIDO, FLUIDA, truncado, etc)
        version_calculo_normalizada = normalize_version_calculo(version_calculo)

        # Normalizar version_calculo (acepta FLUIDO, FLUIDA, truncado, etc)
        version_calculo_normalizada = normalize_version_calculo(version_calculo)

        # PASO 1: Verificacin bsica
        existe = await tdv_queries.verificar_estilo_existente(
            codigo_estilo, version_calculo_normalizada
        )
        es_nuevo = not existe

        # PASO 2: Informacin detallada si existe
        info_detallada = None
        autocompletado_disponible = False
        campos_sugeridos = {}

        if not es_nuevo:
            try:
                info_detallada = await tdv_queries.obtener_info_detallada_estilo(
                    codigo_estilo, version_calculo_normalizada
                )

                if info_detallada.get("encontrado", False):
                    autocompletado_disponible = True
                    campos_sugeridos = {
                        "familia_producto": info_detallada.get("familia_producto"),
                        "tipo_prenda": info_detallada.get("tipo_prenda"),
                    }

                    logger.info(
                        f"[OK] Auto-completado disponible para {codigo_estilo}: {campos_sugeridos}"
                    )

            except Exception as e:
                logger.warning(
                    f"[WARN] Error obteniendo info detallada para {codigo_estilo}: {e}"
                )
                info_detallada = None

        # PASO 3: Volumen y categorizacin
        volumen_historico = 0
        categoria = "Nuevo"

        if not es_nuevo and info_detallada and info_detallada.get("encontrado"):
            volumen_historico = info_detallada.get("volumen_total", 0)
            categoria = info_detallada.get("categoria", "Recurrente")
        elif not es_nuevo:
            # Fallback: obtener volumen directamente
            try:
                volumen_historico = await tdv_queries.obtener_volumen_historico_estilo(
                    codigo_estilo, version_calculo_normalizada
                )
                categoria = (
                    "Muy Recurrente"
                    if volumen_historico >= 4000
                    else "Recurrente"
                    if volumen_historico > 0
                    else "Nuevo"
                )
            except pyodbc.Error:
                volumen_historico = 0
                categoria = "Nuevo"

        # PASO 4: Respuesta estructurada
        respuesta = {
            "codigo_estilo": codigo_estilo,
            "existe_en_bd": existe,
            "es_estilo_nuevo": es_nuevo,
            "categoria": categoria,
            "volumen_historico": volumen_historico,
            "version_calculo": version_calculo,
            "autocompletado": {
                "disponible": autocompletado_disponible,
                "familia_producto": campos_sugeridos.get("familia_producto"),
                "tipo_prenda": campos_sugeridos.get("tipo_prenda"),
            },
            "info_detallada": info_detallada,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"[OK] Verificacin completa {codigo_estilo}: existe={existe}, auto-completado={autocompletado_disponible}"
        )
        return respuesta

    except Exception as e:
        logger.error(f"[ERROR] Error en verificacin completa {codigo_estilo}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error verificando estilo: {str(e)}"
        )


# ✨ v2.0: ENDPOINT GENÉRICO para ambos tipos de búsqueda (estilo_propio y estilo_cliente)
@app.get("/verificar-estilo/{codigo}", tags=["Bsqueda"])
async def verificar_estilo_generico(
    codigo: str,
    tipo: str = "estilo_propio",  # "estilo_propio" o "estilo_cliente"
    version_calculo: Optional[str] = None,
):
    """
    [v2.0] ENDPOINT GENÉRICO: Verifica estilo (propio o cliente) con auto-completado

    Parámetros:
    - codigo: Código del estilo a buscar
    - tipo: "estilo_propio" o "estilo_cliente" (default: estilo_propio)
    - version_calculo: Versión de cálculo (FLUIDA, FLUIDO, truncado, etc)

    Retorna información de auto-completado para ambos tipos
    """
    try:
        # Normalizar version_calculo
        version_calculo_normalizada = normalize_version_calculo(version_calculo)

        logger.info(f"🔍 [v2.0] Verificando {tipo}: {codigo}, version: {version_calculo_normalizada}")

        # Inicializar variables
        info_detallada = None
        autocompletado_disponible = False
        campos_sugeridos = {}
        volumen_historico = 0
        categoria = "Nuevo"
        existe = False

        # RAMA 1: Buscar por ESTILO_PROPIO
        if tipo == "estilo_propio":
            # PASO 1: Verificación básica
            existe = await tdv_queries.verificar_estilo_existente(
                codigo, version_calculo_normalizada
            )
            es_nuevo = not existe

            # PASO 2: Información detallada si existe
            if not es_nuevo:
                try:
                    info_detallada = await tdv_queries.obtener_info_detallada_estilo(
                        codigo, version_calculo_normalizada
                    )

                    if info_detallada.get("encontrado", False):
                        autocompletado_disponible = True
                        campos_sugeridos = {
                            "familia_producto": info_detallada.get("familia_producto"),
                            "tipo_prenda": info_detallada.get("tipo_prenda"),
                            "cliente_principal": info_detallada.get("cliente_principal"),  # ✨ v2.0: Auto-completar cliente
                        }
                        logger.info(f"✅ Auto-completado encontrado para {codigo}: {campos_sugeridos}")

                except Exception as e:
                    logger.warning(f"[WARN] Error obteniendo info para {codigo}: {e}")
                    info_detallada = None

            # PASO 3: Volumen y categorización
            if not es_nuevo and info_detallada and info_detallada.get("encontrado"):
                volumen_historico = info_detallada.get("volumen_total", 0)
                categoria = info_detallada.get("categoria", "Recurrente")
            elif not es_nuevo:
                try:
                    volumen_historico = await tdv_queries.obtener_volumen_historico_estilo(
                        codigo, version_calculo_normalizada
                    )
                    categoria = (
                        "Muy Recurrente"
                        if volumen_historico >= 4000
                        else "Recurrente"
                        if volumen_historico > 0
                        else "Nuevo"
                    )
                except pyodbc.Error:
                    volumen_historico = 0
                    categoria = "Nuevo"

        # RAMA 2: Buscar por ESTILO_CLIENTE (v2.0)
        elif tipo == "estilo_cliente":
            try:
                # Obtener información del estilo_cliente
                info_detallada = await tdv_queries.obtener_info_detallada_estilo_cliente(
                    codigo, version_calculo_normalizada
                )

                if info_detallada and info_detallada.get("encontrado", False):
                    existe = True
                    autocompletado_disponible = True
                    campos_sugeridos = {
                        "familia_producto": info_detallada.get("familia_producto"),
                        "tipo_prenda": info_detallada.get("tipo_prenda"),
                        "cliente_principal": info_detallada.get("cliente_principal"),
                    }
                    logger.info(f"✅ [v2.0] Auto-completado encontrado para {codigo}: {campos_sugeridos}")

                    # Obtener volumen histórico
                    volumen_historico = await tdv_queries.obtener_volumen_historico_estilo_cliente(
                        codigo, version_calculo_normalizada
                    )

                    categoria = (
                        "Muy Recurrente"
                        if volumen_historico >= 4000
                        else "Recurrente"
                        if volumen_historico > 0
                        else "Nuevo"
                    )
            except Exception as e:
                logger.warning(f"[WARN] Error obteniendo info estilo_cliente {codigo}: {e}")
                info_detallada = None

        # PASO 4: Respuesta estructurada (igual para ambos tipos)
        respuesta = {
            "codigo": codigo,
            "tipo": tipo,
            "existe_en_bd": existe,
            "es_estilo_nuevo": categoria == "Nuevo",
            "categoria": categoria,
            "volumen_historico": volumen_historico,
            "version_calculo": version_calculo_normalizada,
            "autocompletado": {
                "disponible": autocompletado_disponible,
                "familia_producto": campos_sugeridos.get("familia_producto"),
                "tipo_prenda": campos_sugeridos.get("tipo_prenda"),
                "cliente_principal": campos_sugeridos.get("cliente_principal"),
            },
            "info_detallada": info_detallada,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"✅ Verificación {tipo} {codigo} completada: existe={existe}")
        return respuesta

    except Exception as e:
        logger.error(f"❌ [ERROR] Error verificando {tipo} {codigo}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error verificando {tipo}: {str(e)}"
        )


@app.post("/ops-utilizadas-cotizacion", tags=["Anlisis"])
async def obtener_ops_utilizadas_cotizacion(input_data: CotizacionInput):
    """
    [OK] NUEVO ENDPOINT: Obtiene las OPs reales utilizadas para una cotizacin

    Retorna las rdenes de produccin especficas que se usaron como base
    para calcular los costos de la cotizacin.
    """
    try:
        logger.info(
            f" Obteniendo OPs utilizadas para: {input_data.codigo_estilo} ({input_data.version_calculo})"
        )

        # Obtener OPs utilizadas desde database
        ops_data = await tdv_queries.obtener_ops_utilizadas_cotizacion(
            codigo_estilo=input_data.codigo_estilo
            if input_data.codigo_estilo
            else None,
            familia_producto=input_data.familia_producto,
            tipo_prenda=input_data.tipo_prenda,
            cliente=input_data.cliente_marca,
            version_calculo=input_data.version_calculo,
        )

        # Estructura de respuesta
        respuesta = {
            "ops_data": ops_data,
            "timestamp": datetime.now().isoformat(),
            "total_ops_encontradas": len(ops_data.get("ops_utilizadas", [])),
            "parametros_entrada": {
                "codigo_estilo": input_data.codigo_estilo,
                "familia_producto": input_data.familia_producto,
                "tipo_prenda": input_data.tipo_prenda,
                "cliente": input_data.cliente_marca,
                "version_calculo": input_data.version_calculo,
            },
        }

        logger.info(
            f"[OK] OPs encontradas: {respuesta['total_ops_encontradas']} para {input_data.codigo_estilo}"
        )
        return respuesta

    except Exception as e:
        logger.error(f"[ERROR] Error obteniendo OPs utilizadas: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo OPs: {str(e)}")


# =====================================================================
# ENDPOINTS DE CONFIGURACIN - CORREGIDOS CON VERSION_CALCULO
# =====================================================================


@app.get("/configuracion", response_model=ConfiguracionResponse, tags=["Configuracin"])
async def obtener_configuracion():
    """Obtiene configuracin completa del sistema"""
    return ConfiguracionResponse(
        rangos_lote=factores.RANGOS_LOTE,
        factores_esfuerzo=factores.FACTORES_ESFUERZO,
        factores_estilo=factores.FACTORES_ESTILO,
        factores_marca=factores.FACTORES_MARCA,
        wips_disponibles={
            "textiles": factores.WIPS_TEXTILES,
            "manufactura": factores.WIPS_MANUFACTURA,
        },
        rangos_seguridad=factores.RANGOS_SEGURIDAD,
    )


@app.get(
    "/wips-disponibles", response_model=WipsDisponiblesResponse, tags=["Configuracin"]
)
async def obtener_wips_disponibles(
    tipo_prenda: Optional[str] = None,
    version_calculo: Optional[str] = None,
):
    """[OK] CORREGIDO: Obtiene WIPs disponibles con costos actuales - ANLISIS INTELIGENTE CON VERSION_CALCULO"""
    try:
        # Normalizar version_calculo (acepta FLUIDO, FLUIDA, truncado, etc)
        version_calculo_normalizada = normalize_version_calculo(version_calculo)

        logger.info(
            f" Obteniendo WIPs disponibles: tipo_prenda={tipo_prenda}, version={version_calculo}"
        )

        (
            wips_textiles,
            wips_manufactura,
        ) = await tdv_queries.obtener_wips_disponibles_estructurado(
            tipo_prenda, version_calculo
        )

        metodo_usado = "analisis_inteligente_variacion" if tipo_prenda else "generico"

        respuesta = WipsDisponiblesResponse(
            wips_textiles=wips_textiles,
            wips_manufactura=wips_manufactura,
            total_disponibles=len(
                [w for w in wips_textiles + wips_manufactura if w.disponible]
            ),
            fuente="resumen_wip_por_prenda",
            fecha_actualizacion=datetime.now(),
            metodo_analisis=metodo_usado,
            tipo_prenda_filtro=tipo_prenda,
            version_calculo=version_calculo,
        )

        logger.info(
            f"[OK] WIPs obtenidas: {respuesta.total_disponibles} disponibles para {tipo_prenda or 'genrico'} ({version_calculo})"
        )
        return respuesta

    except Exception as e:
        logger.error(f"[ERROR] Error obteniendo WIPs: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo WIPs: {str(e)}")


@app.get("/ruta-textil-recomendada/{tipo_prenda}", tags=["Configuracin"])
async def obtener_ruta_textil_recomendada(
    tipo_prenda: str,
    version_calculo: Optional[str] = None,
):
    """[OK] CORREGIDO: Obtiene ruta textil recomendada para un tipo de prenda especfico"""
    try:
        # Normalizar version_calculo (acepta FLUIDO, FLUIDA, truncado, etc)
        version_calculo_normalizada = normalize_version_calculo(version_calculo)

        logger.info(
            f" Obteniendo ruta textil para: {tipo_prenda} ({version_calculo})"
        )

        ruta_textil = await tdv_queries.obtener_ruta_textil_recomendada(
            tipo_prenda, version_calculo
        )

        # Enriquecer respuesta con version_calculo
        if isinstance(ruta_textil, dict):
            ruta_textil["version_calculo"] = version_calculo
            ruta_textil["timestamp"] = datetime.now().isoformat()
        else:
            # Si es una lista, crear respuesta estructurada
            ruta_textil = {
                "ruta_textil": ruta_textil,
                "tipo_prenda": tipo_prenda,
                "version_calculo": version_calculo,
                "timestamp": datetime.now().isoformat(),
            }

        logger.info(
            f"[OK] Ruta textil obtenida: {len(ruta_textil.get('wips_recomendadas', []))} WIPs recomendadas"
        )
        return ruta_textil

    except Exception as e:
        logger.error(f"[ERROR] Error obteniendo ruta textil para {tipo_prenda}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo ruta textil: {str(e)}"
        )


# =====================================================================
# ENDPOINTS DE DATOS MAESTROS - CORREGIDOS CON VERSION_CALCULO
# =====================================================================


@app.get("/clientes", tags=["Datos Maestros"])
async def obtener_clientes(
    version_calculo: Optional[str] = None,
):
    """[OK] CORREGIDO: Obtiene lista de clientes disponibles CON VERSION_CALCULO"""
    try:
        # Normalizar version_calculo (acepta FLUIDO, FLUIDA, truncado, etc)
        version_calculo_normalizada = normalize_version_calculo(version_calculo)

        logger.info(f" Cargando clientes para versin: {version_calculo}")

        clientes = await tdv_queries.obtener_clientes_disponibles(version_calculo_normalizada)

        respuesta = {
            "clientes": clientes,
            "total": len(clientes),
            "fuente": "costo_op_detalle",
            "version_calculo": version_calculo,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"[OK] Clientes cargados: {len(clientes)} para {version_calculo}")
        return respuesta

    except Exception as e:
        logger.error(f"[ERROR] Error obteniendo clientes: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo clientes: {str(e)}"
        )


@app.get("/tipos-prenda", tags=["Datos Maestros"])
async def obtener_tipos_prenda(
    version_calculo: Optional[str] = None,
):
    """[OK] Obtiene lista de tipos prenda disponibles"""
    try:
        logger.info(f" Cargando tipos para version: {version_calculo}")

        # La normalización se hace dentro de database.py
        tipos = await tdv_queries.obtener_todos_tipos_prenda(version_calculo)

        respuesta = {
            "tipos": tipos,
            "total": len(tipos),
            "fuente": "costo_op_detalle",
            "version_calculo": version_calculo,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"[OK] Tipos cargados: {len(tipos)} para {version_calculo}")
        return respuesta

    except Exception as e:
        logger.error(f"[ERROR] Error obteniendo tipos: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo tipos: {str(e)}"
        )


# ENDPOINT CONSOLIDADO - OPTIMIZADO PARA CARGA INICIAL
# =====================================================================
@app.get("/inicializar", tags=["Datos Maestros"])
async def inicializar_datos(
    version_calculo: Optional[str] = None,
):
    """
    [OPTIMIZADO] Carga todos los datos iniciales en UNA SOLA LLAMADA
    Retorna: clientes, tipos de prenda, y WIPs disponibles
    Reduce 3 requests HTTP a 1 único request
    """
    try:
        # Normalizar version_calculo
        version_calculo_normalizada = normalize_version_calculo(version_calculo)

        logger.info(f"📦 [INICIALIZAR] Cargando datos consolidados para versión: {version_calculo_normalizada}")

        # Ejecutar las 3 queries en paralelo
        clientes = await tdv_queries.obtener_clientes_disponibles(version_calculo_normalizada)
        tipos = await tdv_queries.obtener_todos_tipos_prenda(version_calculo_normalizada)

        # Obtener WIPs sin filtro de tipo_prenda (devuelve todos)
        wips_textiles, wips_manufactura = await tdv_queries.obtener_wips_disponibles_estructurado(
            tipo_prenda=None, version_calculo=version_calculo_normalizada
        )
        wips = {
            "textiles": wips_textiles,
            "manufactura": wips_manufactura,
        }

        respuesta = {
            "clientes": clientes,
            "tipos": tipos,
            "wips": wips,
            "total_clientes": len(clientes),
            "total_tipos": len(tipos),
            "total_wips": len(wips),
            "version_calculo": version_calculo_normalizada,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"✅ [INICIALIZAR] Datos cargados: {len(clientes)} clientes, "
            f"{len(tipos)} tipos, {len(wips)} WIPs en versión {version_calculo_normalizada}"
        )
        return respuesta

    except Exception as e:
        logger.error(f"❌ [INICIALIZAR] Error cargando datos consolidados: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error cargando datos iniciales: {str(e)}"
        )


# =====================================================================
# ENDPOINTS DE BSQUEDA - CORREGIDOS CON VERSION_CALCULO
# =====================================================================


@app.get(
    "/buscar-estilos/{codigo_estilo}",
    response_model=List[EstiloSimilar],
    tags=["Bsqueda"],
)
async def buscar_estilos_similares(
    codigo_estilo: str,
    cliente: Optional[str] = None,
    limite: Optional[int] = 10,
    version_calculo: Optional[str] = None,
):
    """[OK] CORREGIDO: Busca estilos similares por cdigo y cliente CON VERSION_CALCULO"""
    try:
        # Normalizar version_calculo (acepta FLUIDO, FLUIDA, truncado, etc)
        version_calculo_normalizada = normalize_version_calculo(version_calculo)

        logger.info(
            f" Buscando estilos similares: {codigo_estilo} para {cliente or 'cualquier cliente'} ({version_calculo})"
        )

        estilos = await tdv_queries.buscar_estilos_similares(
            codigo_estilo, cliente or "", limite, version_calculo
        )

        logger.info(
            f"[OK] Estilos similares encontrados: {len(estilos)} para {codigo_estilo} ({version_calculo})"
        )
        return estilos

    except Exception as e:
        logger.error(f"[ERROR] Error buscando estilos: {e}")
        raise HTTPException(status_code=500, detail=f"Error en bsqueda: {str(e)}")


@app.get("/verificar-estilo/{codigo_estilo}", tags=["Bsqueda"])
async def verificar_estilo_existente(
    codigo_estilo: str,
    version_calculo: Optional[str] = None,
):
    """[OK] MANTENIDO: Verificacin bsica de estilo (compatibilidad)"""
    try:
        # Normalizar version_calculo (acepta FLUIDO, FLUIDA, truncado, etc)
        version_calculo_normalizada = normalize_version_calculo(version_calculo)

        existe = await tdv_queries.verificar_estilo_existente(
            codigo_estilo, version_calculo
        )
        es_nuevo = not existe

        # Determinar categora especfica si es recurrente
        categoria = "Nuevo"
        volumen_historico = 0

        if not es_nuevo:
            try:
                # Normalizar version_calculo (acepta FLUIDO, FLUIDA, truncado, etc)
                version_calculo_normalizada = normalize_version_calculo(version_calculo)

                volumen_total = await tdv_queries.obtener_volumen_historico_estilo(
                    codigo_estilo, version_calculo
                )
                volumen_historico = volumen_total

                if volumen_total >= 4000:
                    categoria = "Muy Recurrente"
                elif volumen_total > 0:
                    categoria = "Recurrente"
                else:
                    categoria = "Nuevo"
            except pyodbc.Error:
                categoria = "Recurrente"  # Fallback si no se puede obtener volumen

        logger.info(
            f"[OK] Verificacin bsica {codigo_estilo}: existe={existe}, categora={categoria}, volumen={volumen_historico}"
        )

        return {
            "codigo_estilo": codigo_estilo,
            "existe_en_bd": existe,
            "es_estilo_nuevo": es_nuevo,
            "categoria": categoria,
            "volumen_historico": volumen_historico,
            "version_calculo": version_calculo,
        }

    except Exception as e:
        logger.error(f"[ERROR] Error verificando estilo: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error verificando estilo: {str(e)}"
        )


# =====================================================================
# NUEVO ENDPOINT: OBTENER OPS DETALLADAS PARA TABLA INTERACTIVA
# =====================================================================

@app.get("/obtener-ops-detalladas/{codigo_estilo}", tags=["Bsqueda"])
async def obtener_ops_detalladas(
    codigo_estilo: str,
    version_calculo: Optional[str] = None,
    meses: int = 12,
    marca: Optional[str] = None,
    tipo_prenda: Optional[str] = None,
    tipo_estilo: str = "estilo_propio",  # v2.0: "estilo_propio" o "estilo_cliente"
):
    """
    Obtiene lista detallada de OPs para un estilo sin aplicar factor de seguridad.
    Retorna todos los datos unitarios para mostrar en tabla interactiva.

    v2.0: Soporta búsqueda por estilo_propio o estilo_cliente
    FALLBACK INTEGRADO:
    1. Primero intenta buscar por tipo_estilo especificado
    2. Si no encuentra y tipo_estilo="estilo_cliente", intenta por estilo_propio
    3. Si no encuentra OPs y marca + tipo_prenda están disponibles, intenta buscar por esos
    4. Si tampoco encuentra, retorna es_estilo_nuevo = true
    """
    logger.info(f" [LLAMADA] obtener_ops_detalladas - estilo={codigo_estilo}, tipo_estilo={tipo_estilo}, marca={marca}, tipo_prenda={tipo_prenda}, version={version_calculo}")
    try:
        # Normalizar version_calculo (acepta FLUIDO, FLUIDA, truncado, etc)
        version_normalizada = normalize_version_calculo(version_calculo)

        # Paso 1: Intentar búsqueda con tipo_estilo especificado
        ops_detalladas = await tdv_queries.obtener_ops_detalladas_para_tabla(
            codigo_estilo, meses, version_normalizada, tipo_estilo
        )

        # Paso 2: v2.0 - Si no encontró por estilo_cliente, intentar por estilo_propio como fallback
        if len(ops_detalladas) == 0 and tipo_estilo == "estilo_cliente":
            logger.info(f" [ENDPOINT] No hay OPs por estilo_cliente {codigo_estilo}, intentando fallback por estilo_propio...")
            ops_detalladas = await tdv_queries.obtener_ops_detalladas_para_tabla(
                codigo_estilo, meses, version_normalizada, "estilo_propio"
            )
            logger.info(f" [ENDPOINT] Fallback estilo_propio retornó {len(ops_detalladas)} OPs")

        # Paso 3: Si no hay OPs y tenemos marca+tipo_prenda, intentar búsqueda alternativa
        if len(ops_detalladas) == 0 and marca and tipo_prenda:
            logger.info(f" [ENDPOINT] No hay OPs por estilo, intentando por marca+tipo_prenda...")
            logger.info(f" [ENDPOINT] marca='{marca}', tipo_prenda='{tipo_prenda}', version='{version_normalizada}'")
            ops_detalladas = await tdv_queries.obtener_ops_estilo_nuevo(
                marca, tipo_prenda, meses, version_normalizada
            )
            logger.info(f" [ENDPOINT] Fallback marca+tipo_prenda retornó {len(ops_detalladas)} OPs")

        es_estilo_nuevo = len(ops_detalladas) == 0

        logger.info(
            f" OPs obtenidas para {codigo_estilo} ({tipo_estilo}): {len(ops_detalladas)} registros, es_nuevo={es_estilo_nuevo}"
        )

        return {
            "codigo_estilo": codigo_estilo,
            "version_calculo": version_normalizada,
            "es_estilo_nuevo": es_estilo_nuevo,
            "ops_encontradas": len(ops_detalladas),
            "ops": ops_detalladas,
        }

    except Exception as e:
        logger.error(f"Error obteniendo OPs detalladas para {codigo_estilo}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo OPs: {str(e)}"
        )


@app.get("/obtener-hilos-detalladas", tags=["Búsqueda"])
async def obtener_hilos_detalladas(
    version_calculo: Optional[str] = None,
    estilo_cliente: Optional[str] = None,
    codigo_estilo: Optional[str] = None,
    cliente_marca: Optional[str] = None,
    tipo_prenda: Optional[str] = None,
):
    """
    Obtiene lista detallada de hilos para un estilo (NO filtra por OPs).
    Retorna TODOS los hilos del estilo especificado con sus costos.

    Parámetros:
    - version_calculo: Versión de cálculo (FLUIDA o truncado)
    - estilo_cliente: Estilo ingresado por el usuario
    - codigo_estilo: Código interno del estilo
    - cliente_marca: Marca del cliente (para búsqueda fallback si no hay estilo)
    - tipo_prenda: Tipo de prenda (para búsqueda fallback si no hay estilo)

    También calcula la frecuencia de uso (en cuántas OPs del estilo aparece cada hilo).
    """
    logger.info(f" [LLAMADA] obtener_hilos_detalladas - version={version_calculo}, estilo_cliente={estilo_cliente}, codigo_estilo={codigo_estilo}, cliente_marca={cliente_marca}, tipo_prenda={tipo_prenda}")
    try:
        # Normalizar version_calculo
        version_normalizada = normalize_version_calculo(version_calculo)

        # Validar que al menos un estilo fue proporcionado
        if not estilo_cliente and not codigo_estilo:
            return {
                "codigo_estilo": "N/A",
                "version_calculo": version_normalizada,
                "total_ops": 0,
                "hilos_encontrados": 0,
                "hilos": [],
            }

        # Obtener hilos del estilo (sin filtrar por OPs)
        try:
            hilos_detallados, total_ops = await tdv_queries.obtener_hilos_para_estilo(
                estilo_cliente=estilo_cliente,
                codigo_estilo=codigo_estilo,
                cliente_marca=cliente_marca,
                tipo_prenda=tipo_prenda,
                version_calculo=version_normalizada,
            )
        except Exception as e:
            logger.warning(f"Error obteniendo hilos: {e}")
            hilos_detallados = []
            total_ops = 0

        logger.info(
            f" Hilos obtenidos para estilo: {len(hilos_detallados)} registros, total_ops: {total_ops}"
        )

        return {
            "codigo_estilo": codigo_estilo or estilo_cliente or "N/A",
            "version_calculo": version_normalizada,
            "total_ops": total_ops,
            "hilos_encontrados": len(hilos_detallados),
            "hilos": hilos_detallados,
        }

    except Exception as e:
        logger.error(f"Error obteniendo hilos detallados: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo hilos: {str(e)}"
        )


@app.get("/obtener-avios-detalladas", tags=["Búsqueda"])
async def obtener_avios_detalladas(
    version_calculo: Optional[str] = None,
    estilo_cliente: Optional[str] = None,
    codigo_estilo: Optional[str] = None,
    cliente_marca: Optional[str] = None,
    tipo_prenda: Optional[str] = None,
):
    """
    Obtiene lista detallada de avios para un estilo (NO filtra por OPs).
    Retorna TODOS los avios del estilo especificado con sus costos.

    Parámetros:
    - version_calculo: Versión de cálculo (FLUIDA o truncado)
    - estilo_cliente: Estilo ingresado por el usuario
    - codigo_estilo: Código interno del estilo
    - cliente_marca: Marca del cliente (para búsqueda fallback si no hay estilo)
    - tipo_prenda: Tipo de prenda (para búsqueda fallback si no hay estilo)

    También calcula la frecuencia de uso (en cuántas OPs del estilo aparece cada avio).
    Incluye la última fecha_corrida disponible.
    """
    logger.info(f" [LLAMADA] obtener_avios_detalladas - version={version_calculo}, estilo_cliente={estilo_cliente}, codigo_estilo={codigo_estilo}, cliente_marca={cliente_marca}, tipo_prenda={tipo_prenda}")
    try:
        # Normalizar version_calculo
        version_normalizada = normalize_version_calculo(version_calculo)

        # Validar que al menos un estilo fue proporcionado
        if not estilo_cliente and not codigo_estilo:
            return {
                "codigo_estilo": "N/A",
                "version_calculo": version_normalizada,
                "total_ops": 0,
                "avios_encontrados": 0,
                "fecha_corrida": "",
                "avios": [],
            }

        # Obtener avios del estilo (sin filtrar por OPs)
        try:
            avios_detallados, fecha_corrida, total_ops = await tdv_queries.obtener_avios_para_estilo(
                estilo_cliente=estilo_cliente,
                codigo_estilo=codigo_estilo,
                cliente_marca=cliente_marca,
                tipo_prenda=tipo_prenda,
                version_calculo=version_normalizada,
            )
        except Exception as e:
            logger.warning(f"Error obteniendo avios: {e}")
            avios_detallados = []
            fecha_corrida = ""
            total_ops = 0

        logger.info(
            f" Avios obtenidos para estilo: {len(avios_detallados)} registros, fecha_corrida: {fecha_corrida}, total_ops: {total_ops}"
        )

        return {
            "codigo_estilo": codigo_estilo or estilo_cliente or "N/A",
            "version_calculo": version_normalizada,
            "total_ops": total_ops,
            "avios_encontrados": len(avios_detallados),
            "fecha_corrida": fecha_corrida,
            "avios": avios_detallados,
        }

    except Exception as e:
        logger.error(f"Error obteniendo avios detallados: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo avios: {str(e)}"
        )


@app.get("/debug-estilo/{estilo}", tags=["Debug"])
async def debug_estilo(estilo: str, tipo_estilo: str = "estilo_propio"):
    """Debug: Verificar qué valores de estilo_propio o estilo_cliente existen"""
    try:
        columna = "estilo_cliente" if tipo_estilo == "estilo_cliente" else "estilo_propio"

        # Buscar exactamente (con TRIM para eliminar espacios)
        query_exacto = f"""
        SELECT COUNT(*) as total, COUNT(DISTINCT cod_ordpro) as ops_dist
        FROM {settings.db_schema}.costo_op_detalle
        WHERE TRIM({columna}::text) = %s
        AND version_calculo = 'FLUIDA'
        """
        result_exact = await tdv_queries.db.query(query_exacto, (estilo.strip(),))

        # Ver similares
        query_similares = f"""
        SELECT DISTINCT {columna}, COUNT(*) as cantidad
        FROM {settings.db_schema}.costo_op_detalle
        WHERE {columna}::text LIKE '%{estilo}%'
        AND version_calculo = 'FLUIDA'
        GROUP BY {columna}
        ORDER BY cantidad DESC
        LIMIT 10
        """
        result_sim = await tdv_queries.db.query(query_similares)

        return {
            "estilo_buscado": estilo,
            "tipo_busqueda": tipo_estilo,
            "busqueda_exacta": {
                "total_registros": result_exact[0]['total'] if result_exact else 0,
                "ops_distintas": result_exact[0]['ops_dist'] if result_exact else 0
            },
            "similares_encontrados": [
                {
                    "estilo": row[columna],
                    "cantidad": row['cantidad']
                } for row in result_sim
            ]
        }
    except Exception as e:
        logger.error(f"Error en debug_estilo: {e}")
        return {"error": str(e)}

@app.get("/debug-montaigne", tags=["Debug"])
async def debug_montaigne():
    """Debug: Mostrar todos los OPs de MONTAIGNE en la BD"""
    try:
        result = await tdv_queries.db.query(f"""
        SELECT DISTINCT
            cliente,
            tipo_de_producto,
            COUNT(*) as cantidad
        FROM {settings.db_schema}.costo_op_detalle
        WHERE cliente ILIKE '%MONTAIGNE%'
        GROUP BY cliente, tipo_de_producto
        ORDER BY cliente, tipo_de_producto
        """)

        return {
            "total_grupos": len(result),
            "grupos": result
        }
    except Exception as e:
        logger.error(f"Error en debug_montaigne: {e}")
        return {"error": str(e)}


@app.get("/listar-clientes-tipos", tags=["Debug"])
async def debug_ops_marcas_tipos(version_calculo: Optional[str] = None):
    """
    SOLO PARA DEBUG: Retorna todas las combinaciones únicas de marca + tipo_prenda
    que existen en la BD para que el usuario vea exactamente qué buscar.
    """
    try:
        version_normalizada = normalize_version_calculo(version_calculo)

        query = f"""
        SELECT DISTINCT
          (cliente) as cliente,
          (tipo_de_producto) as tipo_prenda,
          COUNT(*) as cantidad_ops
        FROM {settings.db_schema}.costo_op_detalle c
        WHERE c.version_calculo = %s
          AND c.fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = %s)
        GROUP BY (cliente), (tipo_de_producto)
        ORDER BY cliente, tipo_prenda
        
        """

        resultados = await tdv_queries.db.query(query, (version_normalizada, version_normalizada))

        return {
            "version_calculo": version_normalizada,
            "total_combinaciones": len(resultados),
            "combinaciones": [
                {
                    "cliente": row["cliente"],
                    "tipo_prenda": row["tipo_prenda"],
                    "cantidad_ops": row["cantidad_ops"]
                }
                for row in resultados
            ]
        }

    except Exception as e:
        logger.error(f"Error en debug_ops_marcas_tipos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/calcular-promedios-ops-seleccionadas", tags=["Bsqueda"])
async def calcular_promedios_ops_seleccionadas(ops_seleccionadas: List[Dict[str, Any]]):
    """
    Calcula promedios sin factor de seguridad basado en OPs seleccionadas.
    Recibe lista de OPs con flag 'seleccionado' indicando cules usar.
    """
    try:
        # Filtrar solo las OPs que estn seleccionadas
        ops_activas = [op for op in ops_seleccionadas if op.get("seleccionado", False)]

        if not ops_activas:
            logger.warning("No hay OPs seleccionadas para calcular promedios")
            return {
                "error": "No hay OPs seleccionadas",
                "ops_usadas": 0,
                "promedios": {},
            }

        # Calcular promedios sin aplicar factor de seguridad
        promedios = {
            "textil_unitario": sum(op.get("textil_unitario", 0) for op in ops_activas) / len(ops_activas),
            "manufactura_unitario": sum(op.get("manufactura_unitario", 0) for op in ops_activas) / len(ops_activas),
            "materia_prima_unitario": sum(op.get("materia_prima_unitario", 0) for op in ops_activas) / len(ops_activas),
            "avios_unitario": sum(op.get("avios_unitario", 0) for op in ops_activas) / len(ops_activas),
            "indirecto_fijo_unitario": sum(op.get("indirecto_fijo_unitario", 0) for op in ops_activas) / len(ops_activas),
            "administracion_unitario": sum(op.get("administracion_unitario", 0) for op in ops_activas) / len(ops_activas),
            "ventas_unitario": sum(op.get("ventas_unitario", 0) for op in ops_activas) / len(ops_activas),
        }

        # Calcular subtotal
        subtotal = sum(promedios.values())

        logger.info(
            f" Promedios calculados sin factor de seguridad: {len(ops_activas)} OPs usadas, subtotal=${subtotal:.4f}"
        )

        return {
            "ops_usadas": len(ops_activas),
            "promedios": promedios,
            "subtotal": subtotal,
        }

    except Exception as e:
        logger.error(f"Error calculando promedios: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error calculando promedios: {str(e)}"
        )


@app.post("/desglose-wip-ops", tags=["Bsqueda"])
async def desglose_wip_ops(data: Dict[str, Any] = Body(...)):
    """
    Obtiene desglose de costos por WIP para OPs seleccionadas.
    Retorna costo_textil y costo_manufactura promedio por cada WIP.
    """
    try:
        cod_ordpros = data.get("cod_ordpros", [])
        version_calculo = data.get("version_calculo", "FLUIDO")

        logger.info(f" [ENDPOINT-DESGLOSE-WIP] Request recibida")
        logger.info(f" [ENDPOINT-DESGLOSE-WIP] cod_ordpros recibidos: {cod_ordpros} (tipo: {type(cod_ordpros)}, len: {len(cod_ordpros) if cod_ordpros else 0})")
        logger.info(f" [ENDPOINT-DESGLOSE-WIP] version_calculo: {version_calculo}")

        if not cod_ordpros:
            logger.warning(f" [ENDPOINT-DESGLOSE-WIP] No se proporcionaron OPs")
            return {
                "error": "No se proporcionaron OPs",
                "desgloses": [],
            }

        # DEBUG: Obtener desglose de WIPs
        logger.info(f" [ENDPOINT-DESGLOSE-WIP] Llamando a obtener_desglose_wip_por_ops con {len(cod_ordpros)} OPs")
        resultado_desglose = await tdv_queries.obtener_desglose_wip_por_ops(
            cod_ordpros, version_calculo
        )

        # La función ahora retorna un diccionario con estructura completa
        logger.info(f" [ENDPOINT-DESGLOSE-WIP] Resultado: {len(resultado_desglose['desgloses_total'])} WIPs encontrados")
        logger.info(f" [ENDPOINT-DESGLOSE-WIP] Desglose WIP: {len(resultado_desglose['desgloses_textil'])} WIPs textil, {len(resultado_desglose['desgloses_manufactura'])} WIPs manufactura")

        # Retornar la estructura completa del resultado
        return resultado_desglose

    except Exception as e:
        logger.error(f" [ENDPOINT-DESGLOSE-WIP] Error obteniendo desglose WIP: {e}")
        import traceback
        logger.error(f" [ENDPOINT-DESGLOSE-WIP] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo desglose WIP: {str(e)}"
        )


# =====================================================================
# ENDPOINT PRINCIPAL DE COTIZACIN - YA MANEJA VERSION_CALCULO VIA INPUT_DATA
# =====================================================================


@app.post("/cotizar", response_model=CotizacionResponse, tags=["Cotizacin"])
async def crear_cotizacion(input_data: CotizacionInput):
    """[OK] CORREGIDO: Endpoint principal para crear cotizaciones - CON SOPORTE COMPLETO VERSION_CALCULO"""
    try:
        logger.info(
            f" Nueva cotizacin: {input_data.usuario} | {input_data.codigo_estilo} | Versin: {input_data.version_calculo} | OPs: {input_data.cod_ordpros}"
        )

        # DEBUG: Log de datos de entrada - DETALLADO
        logger.info(f"[COTIZAR-LOG] ==================== INICIANDO COTIZACION ====================")
        logger.info(f"[COTIZAR-LOG] Cliente: '{input_data.cliente_marca}' (tipo: {type(input_data.cliente_marca).__name__})")
        logger.info(f"[COTIZAR-LOG] Estilo: '{input_data.codigo_estilo}' (tipo: {type(input_data.codigo_estilo).__name__})")
        logger.info(f"[COTIZAR-LOG] Tipo Prenda: '{input_data.tipo_prenda}' (tipo: {type(input_data.tipo_prenda).__name__})")
        logger.info(f"[COTIZAR-LOG] Categoria Lote: '{input_data.categoria_lote}' (tipo: {type(input_data.categoria_lote).__name__})")
        logger.info(f"[COTIZAR-LOG] Version Calculo: '{input_data.version_calculo}' (tipo: {type(input_data.version_calculo).__name__})")
        logger.info(f"[COTIZAR-LOG] OPs: {input_data.cod_ordpros} (tipo: {type(input_data.cod_ordpros).__name__})")
        logger.info(f"[COTIZAR-LOG] WIPs Textiles: {input_data.wips_textiles}")
        logger.info(f"[COTIZAR-LOG] WIPs Manufactura: {input_data.wips_manufactura}")
        logger.info(f"[COTIZAR-LOG] Cantidad Prendas: {input_data.cantidad_prendas}")
        logger.info(f"[COTIZAR-LOG] Esfuerzo Total: {input_data.esfuerzo_total}")
        logger.info(f"[COTIZAR-LOG] Margen Adicional: {input_data.margen_adicional}")

        # Validar version_calculo - el validador de Pydantic en models.py ya lo valida
        if not hasattr(input_data, "version_calculo") or not input_data.version_calculo:
            # Asignar default si no viene en input
            logger.warning(f"[COTIZAR-LOG] version_calculo no está definido, asignando default FLUIDO")
            input_data.version_calculo = VersionCalculo.FLUIDO

        # Rutear a método optimizado si hay OPs seleccionadas
        if input_data.cod_ordpros and len(input_data.cod_ordpros) > 0:
            logger.info(f"[COTIZAR-LOG] RUTA: COTIZACION RAPIDA - {len(input_data.cod_ordpros)} OPs seleccionadas")
            logger.info(f"[COTIZAR-LOG] OPs: {input_data.cod_ordpros}")
            logger.info(f"[COTIZAR-LOG] Llamando procesar_cotizacion_rapida_por_ops...")
            resultado = await cotizador_tdv.procesar_cotizacion_rapida_por_ops(input_data)
        else:
            # Usar método estándar si no hay OPs seleccionadas
            logger.info(f"[COTIZAR-LOG] RUTA: COTIZACION ESTANDAR - Sin OPs seleccionadas")
            logger.info(f"[COTIZAR-LOG] Llamando procesar_cotizacion...")
            resultado = await cotizador_tdv.procesar_cotizacion(input_data)

        logger.info(
            f"[OK] Cotizacin completada: {resultado.id_cotizacion} | ${resultado.precio_final:.2f} | Versin: {resultado.version_calculo_usada}"
        )
        return resultado

    except ValueError as e:
        logger.warning(f"[WARN] Error de validacin: {e}")
        import traceback
        logger.error(f"[TRACEBACK ValueError] {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=f"Error de validacion: {str(e)}")
    except Exception as e:
        logger.error(f"[ERROR] Error procesando cotizacin: {e}")
        import traceback
        tb_lines = traceback.format_exc().split('\n')
        logger.error(f"[TRACEBACK] Linea de error: {tb_lines[-3] if len(tb_lines) > 2 else 'N/A'}")
        logger.error(f"[TRACEBACK] Tipo error: {type(e).__name__}")
        logger.error(f"[TRACEBACK] Mensaje: {str(e)}")
        logger.error(f"[TRACEBACK COMPLETO] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error interno: {type(e).__name__}: {str(e)}")


# =====================================================================
# ENDPOINTS DE ANLISIS - CORREGIDOS CON VERSION_CALCULO
# =====================================================================


@app.get("/analisis-historico", tags=["Anlisis"])
async def obtener_analisis_historico(
    familia: str,
    tipo: Optional[str] = None,
    meses: Optional[int] = 12,
    version_calculo: Optional[str] = None,
):
    """[OK] CORREGIDO: Anlisis histrico para benchmarking CON VERSION_CALCULO"""
    try:
        # Normalizar version_calculo (acepta FLUIDO, FLUIDA, truncado, etc)
        version_calculo_normalizada = normalize_version_calculo(version_calculo)

        logger.info(f"[DATA] Anlisis histrico: {familia}/{tipo} ({version_calculo})")

        # Query base actualizada CON VERSION_CALCULO
        base_params = [familia, version_calculo, meses]
        base_query = f"""
        SELECT
            COUNT(*) as total_ops,
            SUM(prendas_requeridas) as total_prendas,
            AVG(monto_factura / NULLIF(prendas_requeridas, 0)) as precio_promedio,
            AVG((costo_textil + costo_manufactura + costo_avios
                 + costo_materia_prima + costo_indirecto_fijo
                 + gasto_administracion + gasto_ventas)
                 / NULLIF(prendas_requeridas, 0)) as costo_promedio,
            AVG(CAST(esfuerzo_total AS FLOAT)) as esfuerzo_promedio,
            COUNT(DISTINCT cliente) as clientes_unicos
        FROM {settings.db_schema}.costo_op_detalle
        WHERE familia_de_productos = ?
          AND version_calculo = ?
          AND fecha_corrida >= DATEADD(month, -?,
              (SELECT MAX(fecha_corrida)
               FROM {settings.db_schema}.costo_op_detalle
               WHERE version_calculo = ?))
          AND prendas_requeridas > 0
        """
        base_params.append(version_calculo)  # Para el subquery

        if tipo:
            base_query += " AND tipo_de_producto = ?"
            base_params.append(tipo)

        resultado = await tdv_queries.db.query(base_query, tuple(base_params))

        respuesta = {
            "analisis": resultado[0] if resultado else {},
            "parametros": {
                "familia": familia,
                "tipo": tipo,
                "meses": meses,
                "version_calculo": version_calculo,
            },
            "fuente": "costo_op_detalle",
            "metodo": "fecha_corrida_maxima_con_version_calculo",
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"[OK] Anlisis histrico completado para {familia}/{tipo} ({version_calculo})"
        )
        return respuesta

    except Exception as e:
        logger.error(f"[ERROR] Error en anlisis histrico: {e}")
        raise HTTPException(status_code=500, detail=f"Error en anlisis: {str(e)}")


# =====================================================================
# ENDPOINTS DE UTILIDAD - MANTENER ORIGINALES
# =====================================================================


@app.get("/categoria-lote/{cantidad}", tags=["Utilidades"])
async def categorizar_lote_por_cantidad(cantidad: int):
    """Categoriza un lote basndose en cantidad de prendas"""
    try:
        categoria, factor = factores.categorizar_lote(cantidad)
        return {
            "cantidad_prendas": cantidad,
            "categoria": categoria,
            "factor": factor,
            "rango": factores.RANGOS_LOTE[categoria],
        }
    except Exception as e:
        logger.error(f"Error categorizando lote: {e}")
        raise HTTPException(status_code=500, detail=f"Error categorizando: {str(e)}")


@app.get("/factor-marca/{cliente}", tags=["Utilidades"])
async def obtener_factor_marca(cliente: str):
    """Obtiene factor de marca para un cliente especfico"""
    try:
        factor = factores.obtener_factor_marca(cliente)
        return {
            "cliente": cliente,
            "factor_marca": factor,
            "estrategia": "Aumentar Margen"
            if factor > 1.0
            else "Mantener Volumen"
            if factor == 1.0
            else "Reducir Margen",
        }
    except Exception as e:
        logger.error(f"Error obteniendo factor marca: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo factor: {str(e)}"
        )


# =====================================================================
# ENDPOINTS DE INFORMACIN SISTEMA
# =====================================================================


@app.get("/info-fechas-corrida", tags=["Anlisis"])
async def obtener_info_fechas_corrida(
    version_calculo: Optional[str] = None,
):
    """[OK] CORREGIDO: Obtiene informacin sobre las fechas de corrida CON VERSION_CALCULO"""
    try:
        # Normalizar version_calculo (acepta FLUIDO, FLUIDA, truncado, etc)
        version_calculo_normalizada = normalize_version_calculo(version_calculo)

        logger.info(f" Obteniendo fechas corrida para versin: {version_calculo}")

        info_fechas = {}
        tablas = ["costo_op_detalle", "resumen_wip_por_prenda", "historial_estilos"]

        for tabla in tablas:
            try:
                # Normalizar version_calculo (acepta FLUIDO, FLUIDA, truncado, etc)
                version_calculo_normalizada = normalize_version_calculo(version_calculo)

                fecha_max = await tdv_queries.obtener_fecha_maxima_corrida(
                    tabla, version_calculo
                )
                info_fechas[tabla] = {
                    "fecha_maxima_corrida": fecha_max,
                    "dias_antiguedad": (datetime.now() - fecha_max).days
                    if fecha_max
                    else None,
                    "estado": "actualizada"
                    if fecha_max and (datetime.now() - fecha_max).days <= 7
                    else "desactualizada",
                    "version_calculo": version_calculo,
                }
            except Exception as e:
                info_fechas[tabla] = {
                    "error": str(e),
                    "estado": "error",
                    "version_calculo": version_calculo,
                }

        respuesta = {
            "fechas_corrida": info_fechas,
            "timestamp_consulta": datetime.now(),
            "metodo": "fecha_corrida_maxima_por_tabla_con_version",
            "version_calculo": version_calculo,
        }

        logger.info(f"[OK] Fechas corrida obtenidas para {version_calculo}")
        return respuesta

    except Exception as e:
        logger.error(f"[ERROR] Error obteniendo info fechas corrida: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo fechas: {str(e)}"
        )


@app.get("/verificar-estilo-completo/{codigo_estilo}", tags=["Bsqueda"])
async def verificar_estilo_completo(
    codigo_estilo: str,
    familia_producto: Optional[str] = None,
    tipo_prenda: Optional[str] = None,
    version_calculo: Optional[str] = None,
):
    """
    [OK] ENDPOINT NUEVO: Verificacin completa con auto-completado y ruta
    Este endpoint era referenciado en el frontend pero no exista
    """
    try:
        # Normalizar version_calculo (acepta FLUIDO, FLUIDA, truncado, etc)
        version_calculo_normalizada = normalize_version_calculo(version_calculo)

        logger.info(
            f" Verificacin completa para estilo: {codigo_estilo} (versin: {version_calculo})"
        )

        # PASO 1: Verificacin bsica
        existe = await tdv_queries.verificar_estilo_existente(
            codigo_estilo, version_calculo
        )
        es_nuevo = not existe

        logger.info(
            f" Resultado verificacin bsica - existe: {existe}, es_nuevo: {es_nuevo}"
        )

        # PASO 2: Informacin detallada si existe
        info_detallada = await tdv_queries.obtener_info_detallada_estilo(
            codigo_estilo, version_calculo
        )

        # PASO 3: Determinar categora y auto-completado
        if info_detallada.get("encontrado", False):
            categoria = info_detallada.get("categoria", "Nuevo")
            volumen_historico = info_detallada.get("volumen_total", 0)
            familia_autocompletada = info_detallada.get("familia_producto")
            tipo_autocompletado = info_detallada.get("tipo_prenda")

            logger.info(
                f"[OK] Info detallada encontrada - categora: {categoria}, volumen: {volumen_historico}"
            )
        else:
            categoria = "Nuevo"
            volumen_historico = 0
            familia_autocompletada = None
            tipo_autocompletado = None

            logger.info(f"[WARN] Info detallada NO encontrada para {codigo_estilo}")

        # PASO 4: Respuesta estructurada
        resultado = {
            "codigo_estilo": codigo_estilo,
            "existe_en_bd": existe,
            "es_estilo_nuevo": es_nuevo,
            "categoria": categoria,
            "volumen_historico": volumen_historico,
            "version_calculo": version_calculo,
            "autocompletado": {
                "disponible": info_detallada.get("encontrado", False),
                "familia_producto": familia_autocompletada,
                "tipo_prenda": tipo_autocompletado,
            },
            "debug_info": {
                "info_detallada_encontrada": info_detallada.get("encontrado", False),
                "fuente": info_detallada.get("fuente", "no_encontrado"),
                "total_ops": info_detallada.get("total_ops", 0),
            },
        }

        # PASO 5: Ruta automtica para estilos nuevos (si se proporcionan familia/tipo)
        if es_nuevo and familia_producto and tipo_prenda:
            try:
                ruta_recomendada = await tdv_queries.obtener_ruta_textil_recomendada(
                    tipo_prenda, version_calculo
                )
                (
                    wips_textiles,
                    wips_manufactura,
                ) = await tdv_queries.obtener_wips_disponibles_estructurado(
                    tipo_prenda, version_calculo
                )

                resultado.update(
                    {
                        "ruta_automatica": {
                            "disponible": True,
                            "tipo_prenda": tipo_prenda,
                            "familia_producto": familia_producto,
                            "wips_recomendadas": ruta_recomendada.get(
                                "wips_recomendadas", []
                            )[:5],
                            "wips_textiles_disponibles": [
                                {
                                    "wip_id": w.wip_id,
                                    "nombre": w.nombre,
                                    "costo": w.costo_actual,
                                }
                                for w in wips_textiles
                                if w.disponible
                            ][:3],
                            "wips_manufactura_disponibles": [
                                {
                                    "wip_id": w.wip_id,
                                    "nombre": w.nombre,
                                    "costo": w.costo_actual,
                                }
                                for w in wips_manufactura
                                if w.disponible
                            ][:3],
                        }
                    }
                )

                logger.info(
                    f"[OK] Ruta automtica agregada para estilo nuevo: {codigo_estilo}"
                )

            except Exception as e:
                logger.warning(f"[WARN] Error obteniendo ruta automtica: {e}")
                resultado["ruta_automatica"] = {"disponible": False, "error": str(e)}

        logger.info(
            f"[OK] Verificacin completa finalizada para {codigo_estilo}: {resultado}"
        )
        return resultado

    except Exception as e:
        logger.error(f"[ERROR] Error en verificacin completa: {e}")
        raise HTTPException(status_code=500, detail=f"Error en verificacin: {str(e)}")


@app.get("/autocompletar-estilo/{codigo_estilo}", tags=["Bsqueda"])
async def autocompletar_estilo_recurrente(
    codigo_estilo: str,
    version_calculo: Optional[str] = None,
):
    """
    [OK] ENDPOINT NUEVO: Auto-completa informacin para estilos recurrentes
    """
    try:
        # Normalizar version_calculo (acepta FLUIDO, FLUIDA, truncado, etc)
        version_calculo_normalizada = normalize_version_calculo(version_calculo)

        logger.info(
            f" Auto-completado solicitado para: {codigo_estilo} (versin: {version_calculo})"
        )

        # Obtener informacin detallada
        info_detallada = await tdv_queries.obtener_info_detallada_estilo(
            codigo_estilo, version_calculo
        )

        if info_detallada.get("encontrado", False):
            logger.info(f"[OK] Auto-completado disponible para {codigo_estilo}")

            return {
                "codigo_estilo": codigo_estilo,
                "autocompletado_disponible": True,
                "info_estilo": info_detallada,
                "campos_sugeridos": {
                    "familia_producto": info_detallada.get("familia_producto"),
                    "tipo_prenda": info_detallada.get("tipo_prenda"),
                },
                "metadata": {
                    "total_ops": info_detallada.get("total_ops", 0),
                    "volumen_total": info_detallada.get("volumen_total", 0),
                    "categoria": info_detallada.get("categoria", "Nuevo"),
                    "version_calculo": version_calculo,
                    "fuente": info_detallada.get("fuente", "historial_completo"),
                },
            }
        else:
            logger.info(f"[WARN] Auto-completado NO disponible para {codigo_estilo}")

            return {
                "codigo_estilo": codigo_estilo,
                "autocompletado_disponible": False,
                "razon": "Estilo no encontrado en base de datos",
                "es_estilo_nuevo": True,
                "version_calculo": version_calculo,
                "debug_info": info_detallada,
            }

    except Exception as e:
        logger.error(f"[ERROR] Error en autocompletado: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo autocompletado: {str(e)}"
        )


@app.get("/debug-estilo/{codigo_estilo}", tags=["Debug"])
async def debug_estilo_clasificacion(
    codigo_estilo: str,
    version_calculo: Optional[str] = None,
):
    """
     ENDPOINT DE DEBUG: Para diagnosticar problemas de clasificacin
    """
    try:
        # Normalizar version_calculo (acepta FLUIDO, FLUIDA, truncado, etc)
        version_calculo_normalizada = normalize_version_calculo(version_calculo)

        debug_info = {}

        # 1. Verificacin en historial_estilos
        query_historial = f"""
        SELECT COUNT(*) as total, MAX(fecha_corrida) as ultima_corrida
        FROM {settings.db_schema}.historial_estilos
        WHERE codigo_estilo = ? AND version_calculo = ?
        """
        resultado_historial = await tdv_queries.db.query(
            query_historial, (codigo_estilo, version_calculo)
        )
        debug_info["historial_estilos"] = (
            resultado_historial[0] if resultado_historial else {}
        )

        # 2. Verificacin en costo_op_detalle
        query_ops = f"""
        SELECT
          COUNT(*) as total_ops,
          SUM(prendas_requeridas) as volumen_total,
          MAX(fecha_corrida) as ultima_corrida,
          MAX(fecha_facturacion) as ultima_facturacion
        FROM {settings.db_schema}.costo_op_detalle
        WHERE estilo_propio = ? AND version_calculo = ?
        """
        resultado_ops = await tdv_queries.db.query(
            query_ops, (codigo_estilo, version_calculo)
        )
        debug_info["costo_op_detalle"] = resultado_ops[0] if resultado_ops else {}

        # 3. Bsqueda con LIKE
        query_like = f"""
        SELECT codigo_estilo, COUNT(*) as total
        FROM {settings.db_schema}.historial_estilos
        WHERE codigo_estilo LIKE ? AND version_calculo = ?
        GROUP BY codigo_estilo
        ORDER BY codigo_estilo
        """
        resultado_like = await tdv_queries.db.query(
            query_like, (f"%{codigo_estilo}%", version_calculo)
        )
        debug_info["busqueda_similar"] = resultado_like

        # 4. Funcin actual de verificacin
        existe_actual = await tdv_queries.verificar_estilo_existente(
            codigo_estilo, version_calculo
        )
        debug_info["verificacion_actual"] = existe_actual

        # 5. Info detallada
        info_detallada = await tdv_queries.obtener_info_detallada_estilo(
            codigo_estilo, version_calculo
        )
        debug_info["info_detallada"] = info_detallada

        return {
            "codigo_estilo": codigo_estilo,
            "version_calculo": version_calculo,
            "debug_completo": debug_info,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"[ERROR] Error en debug: {e}")
        return {
            "codigo_estilo": codigo_estilo,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@app.get("/versiones-calculo", tags=["Configuracin"])
async def obtener_versiones_calculo():
    """[OK] CORREGIDO: Obtiene informacin sobre las versiones de clculo disponibles"""
    try:
        logger.info("[INFO] Obteniendo informacin de versiones de clculo")

        versiones_info = {}
        versiones = ["FLUIDO", "FLUIDA", "truncado"]  # FLUIDA included for backwards compatibility with old database data

        for version in versiones:
            try:
                # Obtener estadsticas bsicas por versin
                query = f"""
                SELECT
                  COUNT(*) as total_registros,
                  COUNT(DISTINCT cliente) as clientes_unicos,
                  COUNT(DISTINCT familia_de_productos) as familias_unicas,
                  MAX(fecha_corrida) as ultima_fecha_corrida
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = ?
                """
                resultado = await tdv_queries.db.query(query, (version,))

                if resultado and resultado[0]:
                    stats = resultado[0]
                    versiones_info[version] = {
                        "total_registros": int(stats[0] or 0),
                        "clientes_unicos": int(stats[1] or 0),
                        "familias_unicas": int(stats[2] or 0),
                        "ultima_fecha_corrida": stats[3],
                        "estado": "disponible" if (stats[0] or 0) > 0 else "sin_datos",
                    }
                else:
                    versiones_info[version] = {
                        "total_registros": 0,
                        "estado": "sin_datos",
                    }

            except Exception as e:
                versiones_info[version] = {"error": str(e), "estado": "error"}

        respuesta = {
            "versiones_disponibles": versiones_info,
            "version_por_defecto": "FLUIDO",
            "descripcion": {
                "FLUIDO": "Metodologa de clculo actual con optimizaciones",
                "FLUIDA": "Metodologa de clculo actual con optimizaciones (alias para compatibilidad BD)",
                "truncado": "Metodologa de clculo con datos truncados/limitados",
            },
            "timestamp_consulta": datetime.now(),
        }

        logger.info(f"[OK] Versiones de clculo obtenidas: {list(versiones_info.keys())}")
        return respuesta

    except Exception as e:
        logger.error(f"[ERROR] Error obteniendo versiones de clculo: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo versiones: {str(e)}"
        )


# =====================================================================
# STARTUP Y CONFIGURACIN
# =====================================================================


@app.on_event("startup")
async def startup_event():
    """Eventos de inicio de la aplicacin"""
    logger.info("[STARTUP] Iniciando Sistema Cotizador TDV CORREGIDO")
    logger.info(f"[VERSION] Versi_n: {settings.api_version}")
    logger.info(f"[DATABASE] Base de datos: {settings.db_host}")
    logger.info(f"[CORS] CORS habilitado para: {settings.cors_origins}")
    logger.info("[OK] CORRECCIONES APLICADAS:")
    logger.info(
        "   - [OK] Nuevos endpoints: /verificar-estilo-completo y /ops-utilizadas-cotizacion"
    )
    logger.info("   - [OK] Auto-completado inteligente para estilos recurrentes")
    logger.info("   - [OK] Manejo completo de version_calculo en todos los endpoints")
    logger.info("   - [OK] WIPs por estabilidad (37,45 = 6 meses | resto = ultlast)")
    logger.info("   - [OK] Gastos indirectos: (MAX + PROMEDIO)/2")
    logger.info("   - [OK] Materia prima/avios: ltimo costo")
    logger.info("   - [OK] Filtros por fecha_corrida en lugar de GETDATE()")
    logger.info("   - [OK] Rutas textiles restauradas y mejoradas")
    logger.info("   - [OK] Logging mejorado con emojis para mejor seguimiento")

    # Verificar conexin inicial
    try:
        tablas = await tdv_queries.health_check()
        logger.info(f"[INFO] Tablas verificadas: {tablas}")

        # Verificar versiones disponibles
        try:
            versiones_query = f"""
            SELECT DISTINCT version_calculo, COUNT(*) as registros
            FROM {settings.db_schema}.costo_op_detalle
            GROUP BY version_calculo
            ORDER BY registros DESC
            """
            versiones_resultado = await tdv_queries.db.query(versiones_query)

            if versiones_resultado:
                logger.info("[DATA] Versiones de clculo disponibles:")
                for version_info in versiones_resultado:
                    version, registros = version_info
                    logger.info(f"     - {version}: {registros} registros")
            else:
                logger.warning(
                    "[WARN] No se encontraron versiones de clculo en costo_op_detalle"
                )

        except Exception as e:
            logger.warning(f"[WARN] Error verificando versiones de clculo: {e}")

        # Verificar fechas de corrida por versin
        for tabla in ["costo_op_detalle", "resumen_wip_por_prenda"]:
            try:
                for version in ["FLUIDA", "truncado"]:
                    try:
                        fecha_max = await tdv_queries.obtener_fecha_maxima_corrida(
                            tabla, version
                        )
                        if fecha_max:
                            dias_antiguedad = (datetime.now() - fecha_max).days
                            logger.info(
                                f" {tabla} ({version}): ltima corrida {fecha_max} ({dias_antiguedad} das)"
                            )
                    except Exception:
                        # Si no existe la versin, no es crtico
                        pass
            except Exception as e:
                logger.warning(f"[WARN] {tabla}: error obteniendo fechas corrida - {e}")

    except Exception as e:
        logger.error(f"[ERROR] Error verificando BD en startup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Eventos de cierre de la aplicacin"""
    logger.info(" Cerrando Sistema Cotizador TDV")


# =====================================================================
# PUNTO DE ENTRADA
# =====================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info(f"[STARTUP] Iniciando servidor en {settings.api_host}:{settings.api_port}")
    uvicorn.run(
        "smp.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
