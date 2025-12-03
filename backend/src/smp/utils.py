"""
=====================================================================
COTIZADOR TDV - LGICA PRINCIPAL - COMPLETAMENTE CORREGIDO
=====================================================================
 Deteccin mejorada de estilos con nuevas funciones de database.py
 Auto-completado automtico funcionando
 Manejo completo de versiones de clculo
 Rutas textiles automticas para estilos nuevos
 Logging mejorado con emojis
 Validaciones robustas
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4

from .models import (
    CotizacionInput,
    CotizacionResponse,
    ComponenteCosto,
    FuenteCosto,
    TipoEstilo,
    WipConfiguracion,
    InfoComercial,
    WipSeleccionada,
    VersionCalculo,
)
from .database import TDVQueries
from .config import factores

logger = logging.getLogger(__name__)

tdv_queries: TDVQueries = TDVQueries.get_instance()

class CotizadorTDV:
    """ Cotizador principal para TDV COMPLETAMENTE CORREGIDO"""

    def __init__(self):
        self.version = "2.1.0-CORREGIDO-COMPLETO"
        self.tdv_queries = tdv_queries
        logger.info(f"[INICIO] Cotizador TDV iniciado - Versin {self.version}")

    async def procesar_cotizacion(
        self, input_data: CotizacionInput
    ) -> CotizacionResponse:
        """
         FUNCIN PRINCIPAL COMPLETAMENTE CORREGIDA

        Flujo mejorado:
        1. Validaciones iniciales robustas
        2. Deteccin inteligente de categora de estilo
        3. Auto-completado automtico si es recurrente
        4. Procesamiento segn tipo (nuevo vs recurrente)
        5. Ruta automtica para estilos nuevos
        6. Respuesta estructurada completa
        """

        logger.info(
            f" Iniciando cotizacin: {input_data.codigo_estilo} | {input_data.usuario} | Versin: {input_data.version_calculo}"
        )
        inicio_tiempo = datetime.now()

        try:
            # Generar ID nico para la cotizacin
            id_cotizacion = self._generar_id_cotizacion()

            #  VALIDACIONES INICIALES ROBUSTAS
            self._validar_input_completo(input_data)

            #  DETECCIN INTELIGENTE DE CATEGORA DE ESTILO
            (
                categoria_estilo,
                volumen_historico,
                info_autocompletado,
            ) = await self._determinar_categoria_estilo_completa(input_data)
            logger.info(
                f" Estilo {input_data.codigo_estilo}: categora={categoria_estilo}, volumen={volumen_historico}"
            )

            #  AUTO-COMPLETADO AUTOMÁTICO (v2.0: tipo_prenda + cliente_marca)
            if info_autocompletado and info_autocompletado.get("encontrado"):
                logger.info(
                    f" Aplicando auto-completado para {input_data.estilo_cliente or input_data.codigo_estilo}"
                )
                # Auto-completar familia y tipo de prenda
                input_data.familia_producto = info_autocompletado.get(
                    "familia_producto", input_data.familia_producto
                )
                input_data.tipo_prenda = info_autocompletado.get(
                    "tipo_prenda", input_data.tipo_prenda
                )
                # ⭐ v2.0: Auto-completar cliente_marca
                cliente_encontrado = info_autocompletado.get("cliente_principal")
                if cliente_encontrado:
                    input_data.cliente_marca = cliente_encontrado
                    logger.info(
                        f" Auto-completado cliente: {cliente_encontrado}"
                    )

            #  DETERMINAR SI ES NUEVO BASADO EN CATEGORA
            es_estilo_nuevo = categoria_estilo == "Nuevo"
            input_data.es_estilo_nuevo = es_estilo_nuevo

            # Obtener factor de marca (ÚNICO factor de cliente)
            factor_marca = factores.obtener_factor_marca(input_data.cliente_marca)

            #  PROCESAR SEGÚN TIPO DE ESTILO CON LÓGICA MEJORADA
            if es_estilo_nuevo:
                logger.info(
                    f"NUEVO Procesando como ESTILO NUEVO: {input_data.codigo_estilo}"
                )
                resultado = await self._procesar_estilo_nuevo_mejorado(
                    input_data, id_cotizacion, factor_marca, categoria_estilo, volumen_historico
                )
            else:
                logger.info(
                    f"RECURRENTE Procesando como ESTILO RECURRENTE: {input_data.codigo_estilo}"
                )
                resultado = await self._procesar_estilo_recurrente_mejorado(
                    input_data, id_cotizacion, factor_marca, categoria_estilo, volumen_historico
                )

            #  ENRIQUECER RESPUESTA CON METADATA COMPLETA (ya configurado en funciones)
            resultado.version_calculo_usada = input_data.version_calculo

            #  AGREGAR RUTA AUTOMTICA PARA ESTILOS NUEVOS
            if (
                es_estilo_nuevo
                and input_data.familia_producto
                and input_data.tipo_prenda
            ):
                ruta_automatica = await self._obtener_ruta_automatica_mejorada(
                    input_data
                )
                if ruta_automatica:
                    resultado.metadatos_adicionales = (
                        resultado.metadatos_adicionales or {}
                    )
                    resultado.metadatos_adicionales["ruta_automatica_sugerida"] = (
                        ruta_automatica
                    )
                    resultado.metadatos_adicionales["estilo_nuevo_con_ruta"] = True
                    logger.info(
                        f" Ruta automtica agregada para estilo nuevo: {len(ruta_automatica.get('wips_recomendadas', []))} WIPs"
                    )

            #  AGREGAR INFO DE AUTO-COMPLETADO A METADATA
            if info_autocompletado and info_autocompletado.get("encontrado"):
                resultado.metadatos_adicionales = resultado.metadatos_adicionales or {}
                resultado.metadatos_adicionales["autocompletado_aplicado"] = {
                    "familia_producto": info_autocompletado.get("familia_producto"),
                    "tipo_prenda": info_autocompletado.get("tipo_prenda"),
                    "volumen_total": info_autocompletado.get("volumen_total"),
                    "fuente": info_autocompletado.get("fuente"),
                }

            tiempo_procesamiento = (datetime.now() - inicio_tiempo).total_seconds()
            logger.info(
                f" Cotizacin completada: {id_cotizacion} | ${resultado.precio_final:.2f} | {tiempo_procesamiento:.2f}s"
            )

            return resultado

        except Exception as e:
            logger.error(f" Error procesando cotizacin: {e}")
            raise

    def _validar_input_completo(self, input_data: CotizacionInput):
        """ Validaciones completas y robustas del input"""

        errores = []

        # Validaciones bsicas - v2.0: Aceptar estilo_cliente O codigo_estilo (UNO U OTRO)
        tiene_codigo_estilo = input_data.codigo_estilo and len(input_data.codigo_estilo.strip()) > 0
        tiene_estilo_cliente = hasattr(input_data, 'estilo_cliente') and input_data.estilo_cliente and len(input_data.estilo_cliente.strip()) > 0

        if not tiene_codigo_estilo and not tiene_estilo_cliente:
            errores.append("Se requiere Código de Estilo O Código de Estilo Cliente")

        if not input_data.cliente_marca or len(input_data.cliente_marca.strip()) == 0:
            errores.append("El cliente/marca es requerido")

        # NOTA: familia_producto y temporada ahora son OPCIONALES
        # Se pasarn directamente a tipo_prenda en los fallbacks

        if not input_data.tipo_prenda or len(input_data.tipo_prenda.strip()) == 0:
            errores.append("El tipo de prenda es requerido")

        # Validar version_calculo - el validador de Pydantic en models.py ya lo valida
        if not hasattr(input_data, "version_calculo") or not input_data.version_calculo:
            input_data.version_calculo = VersionCalculo.FLUIDO  # Default

        # Nota: categoria_lote ya no se valida ni usa en v2.0
        # Solo se mantiene para compatibilidad con frontend

        # Usar cantidad_prendas del categora_lote si no viene especificada
        if (
            not hasattr(input_data, "cantidad_prendas")
            or not input_data.cantidad_prendas
        ):
            cantidad_map = {
                "Micro Lote": 25,
                "Lote Pequeo": 250,
                "Lote Mediano": 750,
                "Lote Grande": 2500,
                "Lote Masivo": 5000,
            }
            input_data.cantidad_prendas = cantidad_map.get(
                input_data.categoria_lote, 500
            )

        if errores:
            raise ValueError(f"Errores de validacin: {'; '.join(errores)}")

        # Limpiar y normalizar datos
        # v2.0: codigo_estilo puede ser None si se usa estilo_cliente
        if input_data.codigo_estilo:
            input_data.codigo_estilo = input_data.codigo_estilo.strip().upper()

        # v2.0: estilo_cliente puede ser None si se usa codigo_estilo
        if hasattr(input_data, 'estilo_cliente') and input_data.estilo_cliente:
            input_data.estilo_cliente = input_data.estilo_cliente.strip().upper()

        input_data.cliente_marca = input_data.cliente_marca.strip()
        # NOTA: familia_producto y temporada ahora son opcionales
        if input_data.familia_producto:
            input_data.familia_producto = input_data.familia_producto.strip()
        if input_data.tipo_prenda:
            input_data.tipo_prenda = input_data.tipo_prenda.strip()
        if input_data.temporada:
            input_data.temporada = input_data.temporada.strip()

        logger.info(f" Validacin completa exitosa para {input_data.estilo_cliente or input_data.codigo_estilo}")

    async def _determinar_categoria_estilo_completa(
        self, input_data: CotizacionInput
    ) -> Tuple[TipoEstilo, int, Optional[Dict]]:
        """
         FUNCIÓN COMPLETAMENTE CORREGIDA v2.0: Determina categoría con auto-completado

        Flujo:
        1. Si estilo_cliente → buscar con obtener_info_detallada_estilo_cliente
        2. Si codigo_estilo → buscar con obtener_info_detallada_estilo (v1.0)
        3. Auto-completado: tipo_prenda + cliente_marca

        Returns:
            Tuple[categoria, volumen_historico, info_autocompletado]
        """

        categoria_estilo = TipoEstilo.NUEVO
        volumen_historico = 0
        info_autocompletado = None

        # Convertir enum a string y normalizar (FLUIDO → FLUIDA)
        from .database import normalize_version_calculo
        version_str = (
            input_data.version_calculo.value
            if hasattr(input_data.version_calculo, 'value')
            else str(input_data.version_calculo)
        )
        version_normalizada = normalize_version_calculo(version_str)

        logger.info(f" [UTILS] Version input: {input_data.version_calculo} → string: {version_str} → normalizada: {version_normalizada}")

        try:
            # v2.0: PRIMERO intentar buscar por estilo_cliente (nuevo flujo)
            if input_data.estilo_cliente:
                logger.info(f" Buscando por ESTILO_CLIENTE: {input_data.estilo_cliente}")

                info_detallada = await tdv_queries.obtener_info_detallada_estilo_cliente(
                    input_data.estilo_cliente, version_normalizada
                )

                if info_detallada.get("encontrado", False):
                    volumen_total = info_detallada.get("volumen_total", 0)
                    volumen_historico = volumen_total

                    # Categorizar según volumen
                    if volumen_total >= 4000:
                        categoria_estilo = TipoEstilo.MUY_RECURRENTE
                    elif volumen_total > 0:
                        categoria_estilo = TipoEstilo.RECURRENTE
                    else:
                        categoria_estilo = TipoEstilo.NUEVO

                    # Información para auto-completado v2.0: incluir cliente_principal
                    info_autocompletado = {
                        "encontrado": True,
                        "familia_producto": info_detallada.get("familia_producto"),
                        "tipo_prenda": info_detallada.get("tipo_prenda"),
                        "cliente_principal": info_detallada.get("cliente_principal"),  # ⭐ Se auto-completa
                        "volumen_total": volumen_total,
                        "categoria": categoria_estilo,
                        "fuente": info_detallada.get("fuente", "estilo_cliente"),
                        "total_ops": info_detallada.get("total_ops", 0),
                        "esfuerzo_promedio": info_detallada.get("esfuerzo_promedio", 6),
                    }

                    logger.info(
                        f" Estilo Cliente {input_data.estilo_cliente} ENCONTRADO: volumen={volumen_total}, "
                        f"categoría={categoria_estilo}, cliente={info_detallada.get('cliente_principal')}"
                    )
                else:
                    # No encontrado por estilo_cliente, es nuevo
                    categoria_estilo = TipoEstilo.NUEVO
                    logger.info(
                        f" Estilo Cliente {input_data.estilo_cliente} NO ENCONTRADO: categoría=Nuevo"
                    )

            # v1.0: FALLBACK - Si no hay estilo_cliente, usar codigo_estilo (compatibilidad hacia atrás)
            elif input_data.codigo_estilo:
                logger.info(f" Buscando por CODIGO_ESTILO (v1.0): {input_data.codigo_estilo}")

                info_detallada = await tdv_queries.obtener_info_detallada_estilo(
                    input_data.codigo_estilo, version_normalizada
                )

                if info_detallada.get("encontrado", False):
                    volumen_total = info_detallada.get("volumen_total", 0)
                    volumen_historico = volumen_total

                    # Categorizar según volumen
                    if volumen_total >= 4000:
                        categoria_estilo = TipoEstilo.MUY_RECURRENTE
                    elif volumen_total > 0:
                        categoria_estilo = TipoEstilo.RECURRENTE
                    else:
                        categoria_estilo = TipoEstilo.NUEVO

                    # Información para auto-completado
                    info_autocompletado = {
                        "encontrado": True,
                        "familia_producto": info_detallada.get("familia_producto"),
                        "tipo_prenda": info_detallada.get("tipo_prenda"),
                        "cliente_principal": info_detallada.get("cliente_principal"),
                        "volumen_total": volumen_total,
                        "categoria": categoria_estilo,
                        "fuente": info_detallada.get("fuente", "detallado"),
                        "total_ops": info_detallada.get("total_ops", 0),
                        "esfuerzo_promedio": info_detallada.get("esfuerzo_promedio", 6),
                    }

                    logger.info(
                        f" Estilo {input_data.codigo_estilo} ENCONTRADO: volumen={volumen_total}, "
                        f"categoría={categoria_estilo}, fuente={info_detallada.get('fuente')}"
                    )
                else:
                    # No encontrado, es nuevo
                    categoria_estilo = TipoEstilo.NUEVO
                    logger.info(
                        f" Estilo {input_data.codigo_estilo} NO ENCONTRADO: categoría=Nuevo"
                    )

        except Exception as e:
            logger.error(
                f" Error determinando categoría estilo: {e}"
            )
            categoria_estilo = TipoEstilo.NUEVO  # Asumir nuevo en caso de error

        return categoria_estilo, volumen_historico, info_autocompletado

    async def _obtener_ruta_automatica_mejorada(
        self, input_data: CotizacionInput
    ) -> Optional[Dict[str, Any]]:
        """
         FUNCIN MEJORADA: Obtiene ruta automtica para estilos nuevos
        """

        try:
            # Obtener ruta textil recomendada (CON filtro de marca + prendas >= 200)
            ruta_textil = await tdv_queries.obtener_ruta_textil_recomendada(
                input_data.tipo_prenda, input_data.version_calculo, input_data.cliente_marca
            )

            if not ruta_textil or not ruta_textil.get("wips_recomendadas"):
                logger.warning(
                    f" No se encontr ruta textil para {input_data.tipo_prenda}"
                )
                return None

            # Obtener WIPs disponibles estructurados (CON filtro de marca + prendas >= 200)
            (
                wips_textiles,
                wips_manufactura,
            ) = await tdv_queries.obtener_wips_disponibles_estructurado(
                input_data.tipo_prenda, input_data.version_calculo, input_data.cliente_marca
            )

            # Filtrar solo WIPs disponibles
            wips_textiles_disponibles = [
                {
                    "wip_id": w.wip_id,
                    "nombre": w.nombre,
                    "costo_actual": w.costo_actual,
                    "disponible": w.disponible,
                    "grupo": "Textil",
                    "recomendado": True,
                }
                for w in wips_textiles
                if w.disponible
            ][:5]  # Top 5

            wips_manufactura_disponibles = [
                {
                    "wip_id": w.wip_id,
                    "nombre": w.nombre,
                    "costo_actual": w.costo_actual,
                    "disponible": w.disponible,
                    "grupo": "Manufactura",
                    "recomendado": True,
                }
                for w in wips_manufactura
                if w.disponible
            ][:5]  # Top 5

            ruta_automatica = {
                "metodo": "automatico_por_frecuencia_uso",
                "tipo_prenda": input_data.tipo_prenda,
                "familia_producto": input_data.familia_producto,
                "version_calculo": input_data.version_calculo,
                "wips_recomendadas": ruta_textil.get("wips_recomendadas", [])[:10],
                "wips_textiles_disponibles": wips_textiles_disponibles,
                "wips_manufactura_disponibles": wips_manufactura_disponibles,
                "total_recomendadas": len(ruta_textil.get("wips_recomendadas", [])),
                "total_disponibles": len(wips_textiles_disponibles)
                + len(wips_manufactura_disponibles),
                "mensaje": f"Ruta automtica generada para estilo nuevo '{input_data.codigo_estilo}' en {input_data.tipo_prenda}",
                "fecha_generacion": datetime.now().isoformat(),
            }

            logger.info(
                f" Ruta automtica generada: {len(wips_textiles_disponibles)} textiles + {len(wips_manufactura_disponibles)} manufactura"
            )
            return ruta_automatica

        except Exception as e:
            logger.warning(
                f" Error generando ruta automtica para {input_data.codigo_estilo}: {e}"
            )
            return None

    async def _procesar_estilo_recurrente_mejorado(
        self,
        input_data: CotizacionInput,
        id_cotizacion: str,
        factor_marca: float,
        categoria_estilo: TipoEstilo,
        volumen_historico: int,
    ) -> CotizacionResponse:
        """
         FUNCIÓN COMPLETAMENTE CORREGIDA: Procesa estilos recurrentes
        Usa MÉTODO ÚNICO COORDINADO:
        - Costos directos (4): del histórico específico del estilo
        - Gastos indirectos (3): MODA + filtrado (obtener_gastos_indirectos_formula)

        Vector Total (v2.0): factor_esfuerzo × factor_marca
        (Sin factor_lote ni factor_estilo - simplificado a 2 factores)
        """

        logger.info(
            f" PROCESANDO estilo RECURRENTE: {input_data.codigo_estilo} ({input_data.version_calculo})"
        )

        #  ESTRATEGIA CORREGIDA: SEPARAR COSTOS DIRECTOS DE INDIRECTOS (v2.0)
        try:
            # Costos DIRECTOS (4): v2.0 - primero intentar por estilo_cliente, si no usar codigo_estilo
            if input_data.estilo_cliente:
                logger.info(f" Buscando costos por ESTILO_CLIENTE: {input_data.estilo_cliente}")
                costos_hist = await tdv_queries.buscar_costos_estilo_cliente(
                    input_data.estilo_cliente,
                    meses=24,
                    version_calculo=input_data.version_calculo,
                )
                metodo_usado_directos = f"historico_estilo_cliente_{input_data.estilo_cliente}"
            else:
                logger.info(f" Buscando costos por CODIGO_ESTILO: {input_data.codigo_estilo}")
                costos_hist = await tdv_queries.buscar_costos_estilo_especifico(
                    input_data.codigo_estilo,
                    meses=24,
                    version_calculo=input_data.version_calculo,
                )
                metodo_usado_directos = f"historico_especifico_{input_data.codigo_estilo}"

            logger.info(
                f" Costos directos obtenidos: {costos_hist.get('registros_encontrados', 0)} registros"
            )

            # SOBREESCRIBIR CON PROMEDIO PONDERADO SI HAY OPs SELECCIONADAS
            logger.debug(f"VALIDANDO OPs SELECCIONADAS")
            logger.debug(f"input_data.cod_ordpros = {input_data.cod_ordpros}")
            logger.debug(f"   tipo: {type(input_data.cod_ordpros)}")
            logger.debug(f"   es truthy: {bool(input_data.cod_ordpros)}")
            if input_data.cod_ordpros:
                logger.debug(f"   length: {len(input_data.cod_ordpros)}")
            if input_data.cod_ordpros and len(input_data.cod_ordpros) > 0:
                logger.info(
                    f" Usando OPs seleccionadas para calcular costos ponderados: {input_data.cod_ordpros}"
                )
                costos_ponderados = await tdv_queries.calcular_costos_ponderados_por_ops(
                    input_data.cod_ordpros,
                    input_data.version_calculo
                )
                if costos_ponderados and costos_ponderados.get("textil") is not None:
                    textil_ponderado = costos_ponderados.get("textil")
                    manufactura_ponderada = costos_ponderados.get("manufactura")
                    logger.info(
                        f" Costos ponderados calculados: textil=${textil_ponderado:.4f}, manufactura=${manufactura_ponderada:.4f}"
                    )
                    costos_hist["costo_textil"] = textil_ponderado
                    costos_hist["costo_manufactura"] = manufactura_ponderada
                    metodo_usado_directos = f"ponderado_ops_seleccionadas_{len(input_data.cod_ordpros)}"
                else:
                    logger.warning(
                        f" No se pudieron calcular costos ponderados, usando histrico"
                    )

            # Gastos INDIRECTOS (3): MODA + filtrado (MTODO NICO)
            logger.info(
                f" INICIANDO obtener_gastos_por_estilo_recurrente para estilo recurrente: {input_data.codigo_estilo}"
            )

            # Convertir enum version_calculo a string normalizado
            from .database import normalize_version_calculo
            version_str_para_gastos = (
                input_data.version_calculo.value
                if hasattr(input_data.version_calculo, 'value')
                else str(input_data.version_calculo)
            )
            version_normalizada_para_gastos = normalize_version_calculo(version_str_para_gastos)
            logger.info(f" [DEBUG-GASTOS] Antes de llamar obtener_gastos: version_str={version_str_para_gastos}, normalizada={version_normalizada_para_gastos}")

            gastos_indirectos, ops_excluidas = await tdv_queries.obtener_gastos_por_estilo_recurrente(
                codigo_estilo=input_data.codigo_estilo,
                version_calculo=version_normalizada_para_gastos,
            )
            logger.info(f" [DEBUG-GASTOS] Después de llamar obtener_gastos: resultado={gastos_indirectos}")
            metodo_usado_indirectos = "promedio_recurrente"
            logger.info(
                f" RESULTADO Gastos indirectos obtenidos: {gastos_indirectos}"
            )
            logger.info(
                f" OPs excluidas: {len(ops_excluidas)}  {ops_excluidas}"
            )

        except Exception as e:
            logger.error(
                f"[ERROR DETALLADO] Fallo al obtener costos para {input_data.codigo_estilo}"
            )
            logger.error(f"  Tipo de error: {type(e).__name__}")
            logger.error(f"  Mensaje: {str(e)}")
            logger.error(f"  Detalles completos: {repr(e)}")
            import traceback
            logger.error(f"  Stack trace:\n{traceback.format_exc()}")

            raise ValueError(
                f"Estilo {input_data.codigo_estilo} - Error: {type(e).__name__}: {str(e)}"
            )

        #  CONSOLIDAR COMPONENTES: Directos + Indirectos
        componentes = []
        costos_validados = {}
        alertas = []
        componentes_faltantes = []

        # Procesar COSTOS DIRECTOS (4) del histrico especfico
        costos_directos = [
            "costo_textil",
            "costo_manufactura",
            "costo_avios",
            "costo_materia_prima",
        ]

        for componente in costos_directos:
            valor = costos_hist.get(componente, 0)

            # Si no est en histrico, usar fallback
            if valor is None or valor <= 0:
                componentes_faltantes.append(componente)
                logger.warning(
                    f" {componente} no disponible en histrico de {input_data.codigo_estilo}"
                )
                if componente in factores.RANGOS_SEGURIDAD:
                    valor = factores.RANGOS_SEGURIDAD[componente]["min"]
                    alertas.append(
                        f" {componente}: no en histrico, usando valor mnimo ${valor:.2f}"
                    )
                else:
                    valor = 0.5
                    alertas.append(
                        f" {componente}: no en histrico, usando fallback ${valor:.2f}"
                    )

            # Aplicar rangos de seguridad
            valor_original = valor
            valor_validado, fue_ajustado = factores.validar_rango_seguridad(
                valor, componente
            )
            costos_validados[componente] = valor_validado

            # DEBUGGING: Log ajustes de seguridad
            if fue_ajustado:
                alertas.append(
                    f" {componente}: ajustado de ${valor_original:.2f} a ${valor_validado:.2f}"
                )

            fuente_real = "historico" if valor_original > 0 else "fallback_minimo"

            componentes.append(
                ComponenteCosto(
                    nombre=componente.replace("_", " ").title(),
                    costo_unitario=valor_validado,
                    fuente=fuente_real,
                    detalles={
                        "metodo": metodo_usado_directos,
                        "valor_original": valor_original,
                        "fue_ajustado": fue_ajustado,
                        "registros_usados": costos_hist.get("registros_encontrados", 0),
                        "disponible_en_historico": valor_original > 0,
                        "estilo": input_data.codigo_estilo,
                    },
                    validado=True,
                    ajustado_por_rango=fue_ajustado,
                )
            )

        # Procesar GASTOS INDIRECTOS (3) usando MODA + filtrado
        gastos_indirectos_keys = [
            "costo_indirecto_fijo",
            "gasto_administracion",
            "gasto_ventas",
        ]

        for componente in gastos_indirectos_keys:
            valor = gastos_indirectos.get(componente, 0)

            print(f"Valor bruto de BD: {valor} (tipo: {type(valor).__name__})", flush=True)
            print(f"Es <= 0: {valor <= 0 if isinstance(valor, (int, float)) else 'N/A'}", flush=True)

            # Si no est disponible, usar fallback
            if valor is None or valor <= 0:
                componentes_faltantes.append(componente)
                logger.warning(
                    f" {componente} no disponible en frmula MODA para {input_data.codigo_estilo}"
                )
                if componente in factores.RANGOS_SEGURIDAD:
                    valor = factores.RANGOS_SEGURIDAD[componente]["min"]
                    alertas.append(
                        f" {componente}: no en MODA, usando valor mnimo ${valor:.2f}"
                    )
                else:
                    valor = 0.5
                    alertas.append(
                        f" {componente}: no en MODA, usando fallback ${valor:.2f}"
                    )

            # Aplicar rangos de seguridad
            valor_original = valor
            valor_validado, fue_ajustado = factores.validar_rango_seguridad(
                valor, componente
            )
            costos_validados[componente] = valor_validado

            # Reload trigger 2025-11-10 08:45:00

            if fue_ajustado:
                alertas.append(
                    f" {componente}: ajustado de ${valor_original:.2f} a ${valor_validado:.2f}"
                )

            fuente_real = "moda_filtrado" if valor_original > 0 else "fallback_minimo"

            componentes.append(
                ComponenteCosto(
                    nombre=componente.replace("_", " ").title(),
                    costo_unitario=valor_validado,
                    fuente=fuente_real,
                    detalles={
                        "metodo": metodo_usado_indirectos,
                        "valor_original": valor_original,
                        "fue_ajustado": fue_ajustado,
                        "ops_excluidas": len(ops_excluidas),
                        "estilo": input_data.codigo_estilo,
                    },
                    validado=True,
                    ajustado_por_rango=fue_ajustado,
                )
            )

        if ops_excluidas:
            alertas.append(
                f" {len(ops_excluidas)} OPs excluidas como outliers en clculo de MODA"
            )

        #  ADVERTENCIA SI HAY COMPONENTES FALTANTES
        if componentes_faltantes:
            alertas.append(
                f" Componentes sin datos histricos: {', '.join(componentes_faltantes)}"
            )
            logger.warning(
                f" Estilo {input_data.codigo_estilo} recurrente pero faltan: {componentes_faltantes}"
            )

        #  CALCULAR TOTALES Y FACTORES (v2.0 - 2 FACTORES SOLAMENTE)
        costo_base_total = sum(costos_validados.values())

        # Determinar esfuerzo - v2.0: Prioritize OPs seleccionadas sobre historial
        # Si el usuario envió esfuerzo_total (promedio de OPs seleccionadas), usarlo
        logger.info(f" [ESFUERZO v2.0] input_data.esfuerzo_total: {input_data.esfuerzo_total}")
        logger.info(f" [ESFUERZO v2.0] costos_hist.esfuerzo_promedio: {costos_hist.get('esfuerzo_promedio', 'N/A')}")

        if input_data.esfuerzo_total:
            esfuerzo_utilizado = int(input_data.esfuerzo_total)
            logger.info(f" [ESFUERZO v2.0] ✅ Usando esfuerzo de OPs seleccionadas: {esfuerzo_utilizado}")
        else:
            # Fallback: usar promedio histórico
            esfuerzo_utilizado = int(costos_hist.get("esfuerzo_promedio", 6))
            logger.info(f" [ESFUERZO v2.0] ⚠️ Usando esfuerzo histórico (default): {esfuerzo_utilizado}")

        # Validar rango
        if esfuerzo_utilizado < 1 or esfuerzo_utilizado > 10:
            esfuerzo_utilizado = 6  # Fallback seguro

        _, factor_esfuerzo = factores.obtener_factor_esfuerzo(esfuerzo_utilizado)

        # Vector total (v2.0): factor_esfuerzo × factor_marca (con pesos configurables)
        # Nota: factor_lote y factor_estilo fueron eliminados
        # Los pesos permiten ajustar la influencia relativa de cada factor
        vector_total = (factor_esfuerzo * factores.PESO_FACTOR_ESFUERZO) * (factor_marca * factores.PESO_FACTOR_MARCA)

        # Aplicar margen configurable (MARGEN_BASE_PORCENTAJE = 0.15 = 15% por defecto)
        precio_final = costo_base_total * (1 + factores.MARGEN_BASE_PORCENTAJE * vector_total)
        margen_aplicado = (factores.MARGEN_BASE_PORCENTAJE * 100) * vector_total

        #  OBTENER INFORMACIN COMERCIAL
        info_comercial = await self._obtener_info_comercial_mejorada(input_data)

        #  VALIDACIONES Y ALERTAS MEJORADAS
        total_componentes = 7
        validaciones = [
            " Estilo RECURRENTE procesado con mtodo COORDINADO",
            f" Costos directos (4): {metodo_usado_directos}",
            f" Gastos indirectos (3): {metodo_usado_indirectos}",
            f" Registros histricos usados: {costos_hist.get('registros_encontrados', 0)}",
            f" Versin de clculo: {input_data.version_calculo}",
            f" Componentes con datos: {total_componentes - len(componentes_faltantes)}/{total_componentes}",
            f" Precisin estimada: {costos_hist.get('precision_estimada', 0.8):.1%}",
        ]

        if costos_hist.get("total_ajustados", 0) > 0:
            alertas.append(
                f" {costos_hist.get('total_ajustados')} valores ajustados por lmites de seguridad"
            )

        if len(componentes_faltantes) > 0:
            alertas.append(
                f" Estilo recurrente incompleto: {len(componentes_faltantes)} componentes con fallback"
            )

        #  RESPUESTA ESTRUCTURADA COMPLETA

        return CotizacionResponse(
            id_cotizacion=id_cotizacion,
            fecha_cotizacion=datetime.now(),
            inputs=input_data,
            categoria_esfuerzo=esfuerzo_utilizado,  # v2.0: Usar esfuerzo de OPs seleccionadas o histórico
            categoria_estilo=categoria_estilo,
            factor_marca=factor_marca,
            componentes=componentes,
            costo_textil=costos_validados["costo_textil"],
            costo_manufactura=costos_validados["costo_manufactura"],
            costo_avios=costos_validados["costo_avios"],
            costo_materia_prima=costos_validados["costo_materia_prima"],
            costo_indirecto_fijo=costos_validados["costo_indirecto_fijo"],
            gasto_administracion=costos_validados["gasto_administracion"],
            gasto_ventas=costos_validados["gasto_ventas"],
            costo_base_total=costo_base_total,
            factor_esfuerzo=factor_esfuerzo,
            vector_total=vector_total,
            precio_final=precio_final,
            margen_aplicado=margen_aplicado,
            validaciones=validaciones,
            alertas=alertas,
            info_comercial=info_comercial,
            metodos_usados=[metodo_usado_directos, metodo_usado_indirectos],
            registros_encontrados=costos_hist.get("registros_encontrados", 0),
            precision_estimada=costos_hist.get(
                "precision_estimada", 0.95
            ),
            version_calculo_usada=input_data.version_calculo,
            volumen_historico=volumen_historico,
            metadatos_adicionales={
                "estrategia_costos": "coordinado_directo+moda",
                "esfuerzo_utilizado": esfuerzo_utilizado,  # v2.0: Puede venir de OPs o historial
                "ajustes_aplicados": costos_hist.get("total_ajustados", 0),
                "fecha_mas_reciente": costos_hist.get("fecha_mas_reciente"),
                "fuente_datos_directos": "historico_especifico",
                "fuente_datos_indirectos": "moda_filtrado",
                "componentes_con_datos": total_componentes - len(componentes_faltantes),
                "componentes_fallback": len(componentes_faltantes),
                "completitud": f"{((total_componentes - len(componentes_faltantes)) / total_componentes * 100):.1f}%",
            },
        )

    async def _procesar_estilo_nuevo_mejorado(
        self,
        input_data: CotizacionInput,
        id_cotizacion: str,
        factor_marca: float,
        categoria_estilo: TipoEstilo,
        volumen_historico: int,
    ) -> CotizacionResponse:
        """
         FUNCIÓN COMPLETAMENTE CORREGIDA: Procesa estilos nuevos con WIPs y ruta automática

        Vector Total (v2.0): factor_esfuerzo × factor_marca
        (Sin factor_lote ni factor_estilo - simplificado a 2 factores)
        """

        logger.info(
            f" PROCESANDO estilo NUEVO: {input_data.codigo_estilo} ({input_data.version_calculo})"
        )

        # NOTA: Validación de WIPs removida - ahora es completamente opcional
        # Los estilos nuevos pueden procesarse con WIPs seleccionados O sin ellos
        # Si no hay WIPs, se usarán costos históricos o valores por defecto

        #  OBTENER COSTOS WIPS CON ANLISIS INTELIGENTE (CON filtro de marca + prendas >= 200)
        # Esto se obtiene aunque no haya WIPs seleccionados, para tener referencia
        costos_wips = []
        try:
            costos_wips = await tdv_queries.obtener_costos_wips_por_estabilidad(
                input_data.tipo_prenda, input_data.version_calculo, input_data.cliente_marca
            )
            logger.info(
                f" Costos WIPs obtenidos: {len(costos_wips)} WIPs disponibles"
            )
        except Exception as e:
            logger.warning(f" Advertencia al obtener costos WIPs: {e}")
            # No es error fatal - continuamos con datos históricos

        #  PROCESAR WIPS CON VALIDACIN ROBUSTA
        componentes: List[ComponenteCosto] = []
        alertas: List[str] = []

        # Procesar WIPs textiles
        costo_textil_total = self._procesar_wips_mejorado(
            input_data.wips_textiles or [], costos_wips, "Textil", componentes, alertas
        )

        # Procesar WIPs manufactura
        costo_manufactura_total = self._procesar_wips_mejorado(
            input_data.wips_manufactura or [],
            costos_wips,
            "Manufactura",
            componentes,
            alertas,
        )

        #  APLICAR RANGOS DE SEGURIDAD
        costo_textil, textil_ajustado = factores.validar_rango_seguridad(
            costo_textil_total, "costo_textil"
        )
        costo_manufactura, manufactura_ajustado = factores.validar_rango_seguridad(
            costo_manufactura_total, "costo_manufactura"
        )

        if textil_ajustado:
            alertas.append(
                f" Costo textil ajustado: ${costo_textil_total:.2f}  ${costo_textil:.2f}"
            )
        if manufactura_ajustado:
            alertas.append(
                f" Costo manufactura ajustado: ${costo_manufactura_total:.2f}  ${costo_manufactura:.2f}"
            )

        #  OBTENER COSTOS COMPLEMENTARIOS
        costos_complementarios = await self._obtener_costos_complementarios_mejorados(
            input_data, componentes, alertas, es_estilo_nuevo=True
        )

        #  CALCULAR TOTALES
        costo_base_total = (
            costo_textil + costo_manufactura + sum(costos_complementarios.values())
        )

        #  FACTORES PARA ESTILOS NUEVOS (v2.0 - 2 FACTORES SOLAMENTE)
        # v2.0: Usar esfuerzo de OPs seleccionadas si está disponible
        logger.info(f" [ESFUERZO v2.0] Estilo NUEVO - input_data.esfuerzo_total: {getattr(input_data, 'esfuerzo_total', 'N/A')}")

        if hasattr(input_data, "esfuerzo_total") and input_data.esfuerzo_total:
            esfuerzo_estimado = max(1, min(10, int(input_data.esfuerzo_total)))
            logger.info(f" [ESFUERZO v2.0] Estilo NUEVO - ✅ Usando esfuerzo de OPs seleccionadas: {esfuerzo_estimado}")
        else:
            esfuerzo_estimado = 7  # Default conservador para nuevos sin OPs seleccionadas
            logger.info(f" [ESFUERZO v2.0] Estilo NUEVO - ⚠️ Usando esfuerzo default: {esfuerzo_estimado}")

        _, factor_esfuerzo = factores.obtener_factor_esfuerzo(esfuerzo_estimado)

        # Vector total (v2.0): factor_esfuerzo × factor_marca (con pesos configurables)
        # Nota: factor_lote y factor_estilo fueron eliminados
        # Los pesos permiten ajustar la influencia relativa de cada factor
        vector_total = (factor_esfuerzo * factores.PESO_FACTOR_ESFUERZO) * (factor_marca * factores.PESO_FACTOR_MARCA)

        # Aplicar margen configurable (MARGEN_BASE_PORCENTAJE = 0.15 = 15% por defecto)
        precio_final = costo_base_total * (1 + factores.MARGEN_BASE_PORCENTAJE * vector_total)
        margen_aplicado = (factores.MARGEN_BASE_PORCENTAJE * 100) * vector_total

        #  INFORMACIN COMERCIAL
        info_comercial = await self._obtener_info_comercial_mejorada(input_data)

        #  VALIDACIONES Y CONFIGURACIN WIPS
        validaciones = [
            " Estilo NUEVO procesado correctamente",
            f" WIPs configuradas: {len(input_data.wips_textiles or [])} textiles + {len(input_data.wips_manufactura or [])} manufactura",
            f" Versin de clculo: {input_data.version_calculo}",
            f" Costos WIP obtenidos: {len(costos_wips)} disponibles",
            " Estrategia: configuracin manual de WIPs",
        ]

        # Configuracin WIPs para respuesta
        configuracion_wips = []
        for wip in (input_data.wips_textiles or []) + (
            input_data.wips_manufactura or []
        ):
            costo_base = costos_wips.get(wip.wip_id, 0)
            configuracion_wips.append(
                WipConfiguracion(
                    wip_id=wip.wip_id,
                    nombre=factores.NOMBRES_WIPS.get(wip.wip_id, f"WIP {wip.wip_id}"),
                    costo=costo_base * wip.factor_ajuste,
                    grupo="Textil"
                    if wip.wip_id in factores.WIPS_TEXTILES
                    else "Manufactura",
                )
            )

        #  RESPUESTA ESTRUCTURADA COMPLETA
        return CotizacionResponse(
            id_cotizacion=id_cotizacion,
            fecha_cotizacion=datetime.now(),
            inputs=input_data,
            categoria_esfuerzo=esfuerzo_estimado,
            categoria_estilo=categoria_estilo,
            factor_marca=factor_marca,
            componentes=componentes,
            costo_textil=costo_textil,
            costo_manufactura=costo_manufactura,
            costo_avios=costos_complementarios.get("costo_avios", 0),
            costo_materia_prima=costos_complementarios.get("costo_materia_prima", 0),
            costo_indirecto_fijo=costos_complementarios.get("costo_indirecto_fijo", 0),
            gasto_administracion=costos_complementarios.get("gasto_administracion", 0),
            gasto_ventas=costos_complementarios.get("gasto_ventas", 0),
            costo_base_total=costo_base_total,
            factor_esfuerzo=factor_esfuerzo,
            vector_total=vector_total,
            precio_final=precio_final,
            margen_aplicado=margen_aplicado,
            validaciones=validaciones,
            alertas=alertas,
            info_comercial=info_comercial,
            metodos_usados=["wips_configurados_manualmente"],
            registros_encontrados=len(costos_wips),
            precision_estimada=0.90,
            version_calculo_usada=input_data.version_calculo,
            volumen_historico=volumen_historico,
            configuracion_wips=configuracion_wips,
            metadatos_adicionales={
                "estrategia_costos": "wips_configurados",
                "esfuerzo_estimado": esfuerzo_estimado,
                "total_wips_configuradas": len(configuracion_wips),
                "ajustes_seguridad": textil_ajustado or manufactura_ajustado,
                "fuente_datos": "wips_actuales",
            },
        )

    # ========================================
    #  FUNCIONES AUXILIARES MEJORADAS
    # ========================================

    def _procesar_wips_mejorado(
        self,
        wips_seleccionadas: List[WipSeleccionada],
        costos_wips: Dict[str, float],
        grupo: str,
        componentes: List[ComponenteCosto],
        alertas: List[str],
    ) -> float:
        """ Procesa WIPs seleccionadas con validacin robusta"""

        costo_total = 0.0

        for wip in wips_seleccionadas:
            if wip.wip_id not in costos_wips:
                alertas.append(f" WIP {wip.wip_id} sin costo disponible")
                costo_base = 0.0
            else:
                costo_base = float(costos_wips[wip.wip_id])

            # Validar factor de ajuste
            factor_ajuste = float(wip.factor_ajuste)
            if factor_ajuste < 0.1 or factor_ajuste > 2.0:
                factor_ajuste = max(0.1, min(2.0, factor_ajuste))
                alertas.append(
                    f" Factor ajuste WIP {wip.wip_id} limitado a {factor_ajuste}"
                )

            costo_ajustado = costo_base * factor_ajuste
            costo_total += costo_ajustado

            # Nombre descriptivo
            nombre_wip = factores.NOMBRES_WIPS.get(wip.wip_id, f"WIP {wip.wip_id}")

            componentes.append(
                ComponenteCosto(
                    nombre=f"{nombre_wip} ({grupo})",
                    costo_unitario=costo_ajustado,
                    fuente="wip",
                    detalles={
                        "wip_id": wip.wip_id,
                        "costo_base": costo_base,
                        "factor_ajuste": factor_ajuste,
                        "grupo": grupo,
                        "disponible": costo_base > 0,
                    },
                    validado=True,
                )
            )

        logger.info(
            f" WIPs {grupo} procesadas: {len(wips_seleccionadas)}  ${costo_total:.2f}"
        )
        return costo_total

    async def _obtener_costos_complementarios_mejorados(
        self,
        input_data: CotizacionInput,
        componentes: List[ComponenteCosto],
        alertas: List[str],
        es_estilo_nuevo: bool = False,
    ) -> Dict[str, float]:
        """ Obtiene costos complementarios con fallbacks robustos"""

        costos_validados = {}

        #  OBTENER LTIMO COSTO DE MATERIALES
        try:
            costos_materiales = await tdv_queries.obtener_ultimo_costo_materiales(
                input_data.version_calculo
            )
            for comp in ["costo_materia_prima", "costo_avios"]:
                valor = costos_materiales.get(comp, 0)
                valor_validado, fue_ajustado = factores.validar_rango_seguridad(
                    valor, comp
                )
                costos_validados[comp] = valor_validado

                if fue_ajustado:
                    alertas.append(f" {comp}: ajustado por lmites de seguridad")

                componentes.append(
                    ComponenteCosto(
                        nombre=comp.replace("_", " ").title(),
                        costo_unitario=valor_validado,
                        fuente="ultimo_costo",
                        detalles={
                            "version_calculo": input_data.version_calculo,
                            "fue_ajustado": fue_ajustado,
                        },
                        validado=True,
                        ajustado_por_rango=fue_ajustado,
                    )
                )

            logger.info(
                f" Costos materiales obtenidos: MP=${costos_validados.get('costo_materia_prima', 0):.2f}, Avos=${costos_validados.get('costo_avios', 0):.2f}"
            )

        except Exception as e:
            logger.warning(
                f" Error obteniendo costos materiales, usando defaults: {e}"
            )
            for comp in ["costo_materia_prima", "costo_avios"]:
                if comp in factores.RANGOS_SEGURIDAD:
                    rango = factores.RANGOS_SEGURIDAD[comp]
                    valor_default = (rango["min"] + rango["max"]) / 2
                    costos_validados[comp] = valor_default
                    alertas.append(f" {comp}: usando valor promedio por error en BD")

        #  OBTENER GASTOS INDIRECTOS (usando MODA para RECURRENTES, genricos para NUEVOS)
        try:
            if es_estilo_nuevo:
                #  ESTILOS NUEVOS: Usar funcin con MODA por marca + tipo (familia ahora es OPCIONAL)
                gastos, ops_excluidas = await tdv_queries.obtener_gastos_por_estilo_nuevo(
                    marca=input_data.cliente_marca,
                    familia_prenda=getattr(input_data, 'familia_producto', None),
                    tipo_prenda=input_data.tipo_prenda,
                    version_calculo=input_data.version_calculo,
                )
                metodo_gastos = "MODA (nuevo por tipo)"
            else:
                #  ESTILOS RECURRENTES: Usar funcin con MODA por cdigo_estilo exacto
                gastos, ops_excluidas = await tdv_queries.obtener_gastos_por_estilo_recurrente(
                    codigo_estilo=input_data.codigo_estilo,
                    version_calculo=input_data.version_calculo,
                )
                metodo_gastos = "MODA (recurrente especfico)"

            for comp in [
                "costo_indirecto_fijo",
                "gasto_administracion",
                "gasto_ventas",
            ]:
                valor = gastos.get(comp, 0)
                #  NOTA: Los lmites de seguridad ya NO se aplican a estos 3 costos
                # porque usamos MODA con filtrado de outliers (10x)
                costos_validados[comp] = valor
                logger.info(f" {comp}: ${valor:.4f} (por {metodo_gastos}, sin rango_seguridad)")

                componentes.append(
                    ComponenteCosto(
                        nombre=comp.replace("_", " ").title(),
                        costo_unitario=valor,
                        fuente="moda_filtrada",
                        detalles={
                            "metodo": metodo_gastos,
                            "version_calculo": input_data.version_calculo,
                            "ops_excluidas_por_outlier": len(ops_excluidas),
                        },
                        validado=True,
                        ajustado_por_rango=False,
                    )
                )

            logger.info(
                f" Gastos indirectos obtenidos: {sum([gastos.get(c, 0) for c in ['costo_indirecto_fijo', 'gasto_administracion', 'gasto_ventas']]):.2f}"
            )

        except Exception as e:
            logger.warning(
                f" Error obteniendo gastos indirectos, usando defaults: {e}"
            )
            for comp in [
                "costo_indirecto_fijo",
                "gasto_administracion",
                "gasto_ventas",
            ]:
                if comp in factores.RANGOS_SEGURIDAD:
                    rango = factores.RANGOS_SEGURIDAD[comp]
                    valor_default = (rango["min"] + rango["max"]) / 2
                    costos_validados[comp] = valor_default
                    alertas.append(f" {comp}: usando valor promedio por error en BD")

        return costos_validados

    async def _obtener_info_comercial_mejorada(
        self, input_data: CotizacionInput
    ) -> InfoComercial:
        """ Obtiene informacin comercial con manejo robusto de errores"""
        try:
            info_raw = await tdv_queries.obtener_info_comercial(
                input_data.familia_producto,
                input_data.tipo_prenda,
                input_data.version_calculo,
            )

            return InfoComercial(
                ops_utilizadas=info_raw.get("historico_volumen", {}).get(
                    "ops_producidas", 0
                ),
                historico_volumen=info_raw.get(
                    "historico_volumen",
                    {"volumen_total_6m": 0, "volumen_promedio": 0, "ops_producidas": 0},
                ),
                tendencias_costos=info_raw.get("tendencias_costos", []),
                analisis_competitividad=info_raw.get("analisis_competitividad", []),
            )
        except Exception as e:
            logger.warning(f" Error obteniendo info comercial: {e}")
            return InfoComercial(
                ops_utilizadas=0,
                historico_volumen={
                    "volumen_total_6m": 0,
                    "volumen_promedio": 0,
                    "ops_producidas": 0,
                },
                tendencias_costos=[],
                analisis_competitividad=[],
            )

    def _generar_id_cotizacion(self) -> str:
        """Genera ID nico para cotizacin"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid4())[:8].upper()
        return f"COT_{timestamp}_{unique_id}"

    async def procesar_cotizacion_rapida_por_ops(
        self, input_data: CotizacionInput
    ) -> CotizacionResponse:
        """
        NUEVA FUNCION OPTIMIZADA: Calcula cotización DIRECTA basada en OPs seleccionadas.

        En lugar de buscar en 196M registros, busca SOLO las OPs que el usuario seleccionó.
        Tiempo esperado: < 1 segundo

        Flujo:
        1. Obtener datos de las OPs específicas (1 query)
        2. Calcular promedios en memoria (Python)
        3. Retornar respuesta
        """
        logger.info(f"[COTIZACION RAPIDA] Iniciando para estilo {input_data.codigo_estilo} con OPs: {input_data.cod_ordpros}")

        if not input_data.cod_ordpros or len(input_data.cod_ordpros) == 0:
            logger.warning(f"[COTIZACION RAPIDA] Sin OPs seleccionadas, usando método estándar")
            return await self.procesar_cotizacion(input_data)

        try:
            id_cotizacion = self._generar_id_cotizacion()
            inicio_tiempo = datetime.now()

            # QUERY ÚNICA Y EFICIENTE: Obtener datos de las OPs específicas
            costos_ops = await tdv_queries.obtener_costos_por_ops_especificas(
                input_data.cod_ordpros,
                input_data.version_calculo
            )

            if not costos_ops:
                # ⚠️ FALLBACK: Si no se encuentran OPs específicas, usar cotización estándar
                logger.warning(
                    f"[COTIZACION RAPIDA] No se encontraron datos para OPs: {input_data.cod_ordpros}. "
                    f"Usando método de cotización estándar como fallback."
                )
                return await self.procesar_cotizacion(input_data)

            logger.info(f"[COTIZACION RAPIDA] Obtenidas {len(costos_ops)} OPs en < 1s")

            # ✨ NUEVO CÁLCULO: SUMA TOTAL / TOTAL PRENDAS
            # Sumar TODOS los costos totales (no unitarios)
            total_prendas = sum(float(op.get('prendas_requeridas', 1)) for op in costos_ops)

            costo_textil_total = sum(float(op.get('costo_textil_total', 0)) for op in costos_ops)
            costo_manufactura_total = sum(float(op.get('costo_manufactura_total', 0)) for op in costos_ops)
            costo_avios_total = sum(float(op.get('costo_avios_total', 0)) for op in costos_ops)
            costo_materia_prima_total = sum(float(op.get('costo_materia_prima_total', 0)) for op in costos_ops)

            # ✨ Dividir TOTAL por TOTAL PRENDAS (no por cantidad de OPs)
            costo_textil_promedio = costo_textil_total / total_prendas if total_prendas > 0 else 0
            costo_manufactura_promedio = costo_manufactura_total / total_prendas if total_prendas > 0 else 0
            costo_avios_promedio = costo_avios_total / total_prendas if total_prendas > 0 else 0
            costo_materia_prima_promedio = costo_materia_prima_total / total_prendas if total_prendas > 0 else 0

            # ✨ Indirectos y gastos YA SON UNITARIOS - promedio normal
            costos_indirectos_fijo = [float(op.get('costo_indirecto_fijo', 0)) for op in costos_ops]
            gastos_admin = [float(op.get('gasto_administracion', 0)) for op in costos_ops]
            gastos_ventas = [float(op.get('gasto_ventas', 0)) for op in costos_ops]

            costo_indirecto_promedio = sum(costos_indirectos_fijo) / len(costos_indirectos_fijo) if costos_indirectos_fijo else 0
            gasto_admin_promedio = sum(gastos_admin) / len(gastos_admin) if gastos_admin else 0
            gasto_ventas_promedio = sum(gastos_ventas) / len(gastos_ventas) if gastos_ventas else 0

            logger.info(
                f"[COTIZACION RAPIDA] Promedios 7 componentes - Textil: ${costo_textil_promedio:.4f}, Manufactura: ${costo_manufactura_promedio:.4f}, Avíos: ${costo_avios_promedio:.4f}, Materia Prima: ${costo_materia_prima_promedio:.4f}"
            )

            # ✨ FACTORES (v2.0 - Solo 2 factores)
            # Esfuerzo: desde input_data si existe, sino usar default 6
            esfuerzo_total = input_data.esfuerzo_total if input_data.esfuerzo_total else 6
            # Desempaqueta correctamente la tupla en dos variables distintas
            categoria_esfuerzo_str, factor_esfuerzo = factores.obtener_factor_esfuerzo(esfuerzo_total)

            # Opcional: convertir la categoría de string a un valor numérico si lo necesitas para la respuesta
            # (Basado en el código que parece intentar hacer esto)
            mapa_esfuerzo = {"Bajo": 5, "Medio": 6, "Alto": 7}
            categoria_esfuerzo = mapa_esfuerzo.get(categoria_esfuerzo_str, 6)

            factor_marca = factores.obtener_factor_marca(input_data.cliente_marca)

            # Categoría de estilo: basada en la presencia de OPs (si hay OPs = recurrente)
            categoria_estilo = TipoEstilo.RECURRENTE

            # DEBUG: Log detallado de cada factor ANTES de multiplicar (v2.0)
            logger.info(f"[FACTORES v2.0] esfuerzo: {factor_esfuerzo} ({type(factor_esfuerzo).__name__}) | marca: {factor_marca} ({type(factor_marca).__name__})")

            # Validar tipos antes de operación matemática
            if not isinstance(factor_esfuerzo, (int, float)):
                logger.error(f"[ERROR TIPO] factor_esfuerzo NO es número: {factor_esfuerzo} (type: {type(factor_esfuerzo)})")
                raise TypeError(f"factor_esfuerzo debe ser float, obtuvo {type(factor_esfuerzo)}: {factor_esfuerzo}")
            if not isinstance(factor_marca, (int, float)):
                logger.error(f"[ERROR TIPO] factor_marca NO es número: {factor_marca} (type: {type(factor_marca)})")
                raise TypeError(f"factor_marca debe ser float, obtuvo {type(factor_marca)}: {factor_marca}")

            # ✨ FÓRMULA CORRECTA: Base Cost (7 componentes) × (1 + 0.15 × vector_total)
            costo_base = (costo_textil_promedio + costo_manufactura_promedio + costo_avios_promedio +
                         costo_materia_prima_promedio + costo_indirecto_promedio +
                         gasto_admin_promedio + gasto_ventas_promedio)

            # Vector total de factores (v2.0): Solo factor_esfuerzo × factor_marca
            logger.info(f"[MULTIPLICACION v2.0] Iniciando: {factor_esfuerzo} * {factor_marca}")
            vector_total = factor_esfuerzo * factor_marca
            logger.info(f"[MULTIPLICACION v2.0] Resultado: {vector_total}")

            # Precio final con margen del 15%
            precio_final = costo_base * (1 + 0.15 * vector_total)
            margen_aplicado = 0.15 * vector_total

            # Desglose por WIP (si existe)
            desglose_wips = self._generar_desglose_wips_desde_ops(costos_ops)

            # ✨ Construir respuesta con TODOS LOS 7 COMPONENTES
            componentes = [
                ComponenteCosto(
                    nombre="Costo Textil",
                    costo_unitario=costo_textil_promedio,
                    fuente=FuenteCosto.PROMEDIO_RANGO,
                    detalles={"porcentaje": (costo_textil_promedio / costo_base * 100) if costo_base > 0 else 0}
                ),
                ComponenteCosto(
                    nombre="Costo Manufactura",
                    costo_unitario=costo_manufactura_promedio,
                    fuente=FuenteCosto.PROMEDIO_RANGO,
                    detalles={"porcentaje": (costo_manufactura_promedio / costo_base * 100) if costo_base > 0 else 0}
                ),
                ComponenteCosto(
                    nombre="Costo Avíos",
                    costo_unitario=costo_avios_promedio,
                    fuente=FuenteCosto.PROMEDIO_RANGO,
                    detalles={"porcentaje": (costo_avios_promedio / costo_base * 100) if costo_base > 0 else 0}
                ),
                ComponenteCosto(
                    nombre="Costo Materia Prima",
                    costo_unitario=costo_materia_prima_promedio,
                    fuente=FuenteCosto.PROMEDIO_RANGO,
                    detalles={"porcentaje": (costo_materia_prima_promedio / costo_base * 100) if costo_base > 0 else 0}
                ),
                ComponenteCosto(
                    nombre="Costo Indirecto Fijo",
                    costo_unitario=costo_indirecto_promedio,
                    fuente=FuenteCosto.PROMEDIO_RANGO,
                    detalles={"porcentaje": (costo_indirecto_promedio / costo_base * 100) if costo_base > 0 else 0}
                ),
                ComponenteCosto(
                    nombre="Gasto Administración",
                    costo_unitario=gasto_admin_promedio,
                    fuente=FuenteCosto.PROMEDIO_RANGO,
                    detalles={"porcentaje": (gasto_admin_promedio / costo_base * 100) if costo_base > 0 else 0}
                ),
                ComponenteCosto(
                    nombre="Gasto Ventas",
                    costo_unitario=gasto_ventas_promedio,
                    fuente=FuenteCosto.PROMEDIO_RANGO,
                    detalles={"porcentaje": (gasto_ventas_promedio / costo_base * 100) if costo_base > 0 else 0}
                ),
            ]

            tiempo_total = (datetime.now() - inicio_tiempo).total_seconds()

            # ✨ Retornar CotizacionResponse COMPLETO con TODOS los campos
            return CotizacionResponse(
                id_cotizacion=id_cotizacion,
                fecha_cotizacion=datetime.now(),
                inputs=input_data,
                categoria_esfuerzo=categoria_esfuerzo,
                categoria_estilo=categoria_estilo,
                factor_marca=factor_marca,
                componentes=componentes,
                costo_textil=costo_textil_promedio,
                costo_manufactura=costo_manufactura_promedio,
                costo_avios=costo_avios_promedio,
                costo_materia_prima=costo_materia_prima_promedio,
                costo_indirecto_fijo=costo_indirecto_promedio,
                gasto_administracion=gasto_admin_promedio,
                gasto_ventas=gasto_ventas_promedio,
                costo_base_total=costo_base,
                factor_esfuerzo=factor_esfuerzo,
                vector_total=vector_total,
                precio_final=precio_final,
                margen_aplicado=margen_aplicado,
                validaciones=[
                    f"✓ {len(input_data.cod_ordpros)} OPs seleccionadas procesadas",
                    f"✓ 7 componentes de costo calculados correctamente",
                    f"✓ Promedios ponderados aplicados",
                    f"✓ Factores de ajuste aplicados (v2.0): Esfuerzo({factor_esfuerzo:.2f}) × Marca({factor_marca:.2f})",
                    f"✓ Margen del 15% aplicado con vector total: {vector_total:.4f}",
                ],
                alertas=[
                    f"Cotización rápida basada en {len(input_data.cod_ordpros)} OPs seleccionadas",
                    f"Método: Promedio ponderado de OPs",
                    f"Tiempo de procesamiento: {tiempo_total:.2f}s",
                ],
                info_comercial=InfoComercial(
                    ops_utilizadas=len(costos_ops),
                    historico_volumen={
                        "cantidad_ops": len(costos_ops),
                        "prendas_totales": sum(float(op.get('prendas_requeridas', 0)) for op in costos_ops) if costos_ops else 0,
                        "fecha_ultima_op": datetime.now().isoformat(),
                    },
                    tendencias_costos=[
                        {
                            "componente": "Textil",
                            "valor_promedio": costo_textil_promedio,
                            "variacion_porcentaje": 0,
                        },
                        {
                            "componente": "Manufactura",
                            "valor_promedio": costo_manufactura_promedio,
                            "variacion_porcentaje": 0,
                        },
                    ],
                    margen_adicional_usuario=input_data.margen_adicional or 0,
                    precio_referencia=precio_final,
                    descuento_cliente=0,
                ),
                metodos_usados=[
                    "obtener_costos_por_ops_especificas",
                    "promedio_ponderado_7_componentes",
                    "aplicacion_factores_ajuste",
                    "formula_precio_base_15porciento",
                ],
                registros_encontrados=len(costos_ops),
                precision_estimada=95.0 if len(costos_ops) >= 2 else 90.0,  # Mayor precisión con más OPs
                version_calculo_usada=input_data.version_calculo or VersionCalculo.FLUIDO,
                codigo_estilo=input_data.codigo_estilo,
                estrategia_costos="promedio_ops_seleccionadas",
                metadatos_adicionales={
                    "metodo_calculo": "promedio_ops_directas_7_componentes",
                    "num_ops": len(input_data.cod_ordpros),
                    "tiempo_segundos": tiempo_total,
                    "base_cost": float(costo_base),
                    "margen_porcentaje": float(margen_aplicado * 100),
                    "cod_ordpros_utilizadas": input_data.cod_ordpros,
                },
                timestamp=datetime.now(),
                usuario=input_data.usuario,
            )

        except Exception as e:
            logger.error(f"[COTIZACION RAPIDA] Error: {type(e).__name__}: {str(e)}")
            raise

    def _generar_desglose_wips_desde_ops(self, costos_ops: List[Dict]) -> List[Dict]:
        """Extrae y agrupa WIPs desde los datos de OPs"""
        wips_dict = {}
        for op in costos_ops:
            wip_id = op.get('wip_id')
            if wip_id:
                if wip_id not in wips_dict:
                    wips_dict[wip_id] = {
                        "wip_id": wip_id,
                        "nombre": factores.NOMBRES_WIPS.get(wip_id, f"WIP {wip_id}"),
                        "cantidad": 0,
                        "costo_total": 0,
                    }
                wips_dict[wip_id]["cantidad"] += op.get('cantidad_wip', 0)
                wips_dict[wip_id]["costo_total"] += op.get('costo_manufactura', 0) * op.get('cantidad_wip', 1)

        return list(wips_dict.values())

# Instancia global del cotizador
cotizador_tdv = CotizadorTDV()

