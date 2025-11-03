"""
=====================================================================
COTIZADOR TDV - LÓGICA PRINCIPAL - COMPLETAMENTE CORREGIDO
=====================================================================
 Detección mejorada de estilos con nuevas funciones de database.py
 Auto-completado automático funcionando
 Manejo completo de versiones de cálculo
 Rutas textiles automáticas para estilos nuevos
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
        logger.info(f"[INICIO] Cotizador TDV iniciado - Versión {self.version}")

    async def procesar_cotizacion(
        self, input_data: CotizacionInput
    ) -> CotizacionResponse:
        """
         FUNCIÓN PRINCIPAL COMPLETAMENTE CORREGIDA

        Flujo mejorado:
        1. Validaciones iniciales robustas
        2. Detección inteligente de categoría de estilo
        3. Auto-completado automático si es recurrente
        4. Procesamiento según tipo (nuevo vs recurrente)
        5. Ruta automática para estilos nuevos
        6. Respuesta estructurada completa
        """

        logger.info(
            f" Iniciando cotización: {input_data.codigo_estilo} | {input_data.usuario} | Versión: {input_data.version_calculo}"
        )
        inicio_tiempo = datetime.now()

        try:
            # Generar ID único para la cotización
            id_cotizacion = self._generar_id_cotizacion()

            #  VALIDACIONES INICIALES ROBUSTAS
            self._validar_input_completo(input_data)

            #  DETECCIÓN INTELIGENTE DE CATEGORÍA DE ESTILO
            (
                categoria_estilo,
                volumen_historico,
                info_autocompletado,
            ) = await self._determinar_categoria_estilo_completa(input_data)
            logger.info(
                f" Estilo {input_data.codigo_estilo}: categoría={categoria_estilo}, volumen={volumen_historico}"
            )

            #  AUTO-COMPLETADO AUTOMÁTICO
            if info_autocompletado and info_autocompletado.get("encontrado"):
                logger.info(
                    f"🎯 Aplicando auto-completado para {input_data.codigo_estilo}"
                )
                input_data.familia_producto = info_autocompletado.get(
                    "familia_producto", input_data.familia_producto
                )
                input_data.tipo_prenda = info_autocompletado.get(
                    "tipo_prenda", input_data.tipo_prenda
                )

            #  DETERMINAR SI ES NUEVO BASADO EN CATEGORÍA
            es_estilo_nuevo = categoria_estilo == "Nuevo"
            input_data.es_estilo_nuevo = es_estilo_nuevo

            # Categorizar lote
            categoria_lote, factor_lote = self._categorizar_lote(
                input_data.categoria_lote
            )

            # Obtener factor de marca
            factor_marca = factores.obtener_factor_marca(input_data.cliente_marca)

            #  PROCESAR SEGÚN TIPO DE ESTILO CON LÓGICA MEJORADA
            if es_estilo_nuevo:
                logger.info(
                    f"🆕 Procesando como ESTILO NUEVO: {input_data.codigo_estilo}"
                )
                resultado = await self._procesar_estilo_nuevo_mejorado(
                    input_data, id_cotizacion, categoria_lote, factor_lote, factor_marca
                )
            else:
                logger.info(
                    f"🔄 Procesando como ESTILO RECURRENTE: {input_data.codigo_estilo}"
                )
                resultado = await self._procesar_estilo_recurrente_mejorado(
                    input_data, id_cotizacion, categoria_lote, factor_lote, factor_marca
                )

            #  ENRIQUECER RESPUESTA CON METADATA COMPLETA
            resultado.categoria_estilo = categoria_estilo
            resultado.volumen_historico = volumen_historico
            resultado.version_calculo_usada = input_data.version_calculo

            #  AGREGAR RUTA AUTOMÁTICA PARA ESTILOS NUEVOS
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
                        f"🧵 Ruta automática agregada para estilo nuevo: {len(ruta_automatica.get('wips_recomendadas', []))} WIPs"
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
                f" Cotización completada: {id_cotizacion} | ${resultado.precio_final:.2f} | {tiempo_procesamiento:.2f}s"
            )

            return resultado

        except Exception as e:
            logger.error(f" Error procesando cotización: {e}")
            raise

    def _validar_input_completo(self, input_data: CotizacionInput):
        """ Validaciones completas y robustas del input"""

        errores = []

        # Validaciones básicas
        if not input_data.codigo_estilo or len(input_data.codigo_estilo.strip()) < 3:
            errores.append("El código de estilo debe tener al menos 3 caracteres")

        if not input_data.cliente_marca or len(input_data.cliente_marca.strip()) == 0:
            errores.append("El cliente/marca es requerido")

        if (
            not input_data.familia_producto
            or len(input_data.familia_producto.strip()) == 0
        ):
            errores.append("La familia de producto es requerida")

        if not input_data.tipo_prenda or len(input_data.tipo_prenda.strip()) == 0:
            errores.append("El tipo de prenda es requerido")

        # Validar version_calculo
        if not hasattr(input_data, "version_calculo") or not input_data.version_calculo:
            input_data.version_calculo = VersionCalculo.FLUIDO  # Default
        else:
            versiones_validas = ["FLUIDO", "truncado"]
            version_value = input_data.version_calculo.value if hasattr(input_data.version_calculo, 'value') else str(input_data.version_calculo)
            if version_value not in versiones_validas:
                errores.append(f"version_calculo debe ser una de: {versiones_validas}")

        # Validar categoría de lote
        if input_data.categoria_lote not in factores.RANGOS_LOTE:
            errores.append(f"Categoría de lote inválida: {input_data.categoria_lote}")

        # Validar temporada
        if not input_data.temporada or len(input_data.temporada.strip()) == 0:
            errores.append("La temporada es requerida")

        # Usar cantidad_prendas del categoría_lote si no viene especificada
        if (
            not hasattr(input_data, "cantidad_prendas")
            or not input_data.cantidad_prendas
        ):
            cantidad_map = {
                "Micro Lote": 25,
                "Lote Pequeño": 250,
                "Lote Mediano": 750,
                "Lote Grande": 2500,
                "Lote Masivo": 5000,
            }
            input_data.cantidad_prendas = cantidad_map.get(
                input_data.categoria_lote, 500
            )

        if errores:
            raise ValueError(f"Errores de validación: {'; '.join(errores)}")

        # Limpiar y normalizar datos
        input_data.codigo_estilo = input_data.codigo_estilo.strip().upper()
        input_data.cliente_marca = input_data.cliente_marca.strip()
        input_data.familia_producto = input_data.familia_producto.strip()
        input_data.tipo_prenda = input_data.tipo_prenda.strip()
        input_data.temporada = input_data.temporada.strip()

        logger.info(f" Validación completa exitosa para {input_data.codigo_estilo}")

    async def _determinar_categoria_estilo_completa(
        self, input_data: CotizacionInput
    ) -> Tuple[TipoEstilo, int, Optional[Dict]]:
        """
         FUNCIÓN COMPLETAMENTE CORREGIDA: Determina categoría con auto-completado

        Returns:
            Tuple[categoria, volumen_historico, info_autocompletado]
        """

        categoria_estilo = TipoEstilo.NUEVO
        volumen_historico = 0
        info_autocompletado = None

        if input_data.codigo_estilo:
            try:
                #  USAR NUEVA FUNCIÓN DE INFORMACIÓN DETALLADA
                info_detallada = await tdv_queries.obtener_info_detallada_estilo(
                    input_data.codigo_estilo, input_data.version_calculo
                )

                if info_detallada.get("encontrado", False):
                    # Es un estilo recurrente con información completa
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
                        f"🆕 Estilo {input_data.codigo_estilo} NO ENCONTRADO: categoría=Nuevo"
                    )

            except Exception as e:
                logger.error(
                    f" Error determinando categoría estilo {input_data.codigo_estilo}: {e}"
                )
                categoria_estilo = TipoEstilo.NUEVO  # Asumir nuevo en caso de error

        return categoria_estilo, volumen_historico, info_autocompletado

    async def _obtener_ruta_automatica_mejorada(
        self, input_data: CotizacionInput
    ) -> Optional[Dict[str, Any]]:
        """
         FUNCIÓN MEJORADA: Obtiene ruta automática para estilos nuevos
        """

        try:
            # Obtener ruta textil recomendada
            ruta_textil = await tdv_queries.obtener_ruta_textil_recomendada(
                input_data.tipo_prenda, input_data.version_calculo
            )

            if not ruta_textil or not ruta_textil.get("wips_recomendadas"):
                logger.warning(
                    f" No se encontró ruta textil para {input_data.tipo_prenda}"
                )
                return None

            # Obtener WIPs disponibles estructurados
            (
                wips_textiles,
                wips_manufactura,
            ) = await tdv_queries.obtener_wips_disponibles_estructurado(
                input_data.tipo_prenda, input_data.version_calculo
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
                "mensaje": f"Ruta automática generada para estilo nuevo '{input_data.codigo_estilo}' en {input_data.tipo_prenda}",
                "fecha_generacion": datetime.now().isoformat(),
            }

            logger.info(
                f"🧵 Ruta automática generada: {len(wips_textiles_disponibles)} textiles + {len(wips_manufactura_disponibles)} manufactura"
            )
            return ruta_automatica

        except Exception as e:
            logger.warning(
                f" Error generando ruta automática para {input_data.codigo_estilo}: {e}"
            )
            return None

    async def _procesar_estilo_recurrente_mejorado(
        self,
        input_data: CotizacionInput,
        id_cotizacion: str,
        categoria_lote: str,
        factor_lote: float,
        factor_marca: float,
    ) -> CotizacionResponse:
        """
         FUNCIÓN COMPLETAMENTE CORREGIDA: Procesa estilos recurrentes
        Usa MÉTODO ÚNICO COORDINADO:
        - Costos directos (4): del histórico específico del estilo
        - Gastos indirectos (3): MODA + filtrado (obtener_gastos_indirectos_formula)
        """

        logger.info(
            f"🔄 PROCESANDO estilo RECURRENTE: {input_data.codigo_estilo} ({input_data.version_calculo})"
        )

        #  ESTRATEGIA CORREGIDA: SEPARAR COSTOS DIRECTOS DE INDIRECTOS
        try:
            # Costos DIRECTOS (4): histórico del estilo específico
            costos_hist = await tdv_queries.buscar_costos_estilo_especifico(
                input_data.codigo_estilo,
                meses=24,
                version_calculo=input_data.version_calculo,
            )
            metodo_usado_directos = f"historico_especifico_{input_data.codigo_estilo}"
            logger.info(
                f" Costos directos obtenidos: {costos_hist.get('registros_encontrados', 0)} registros"
            )

            # Gastos INDIRECTOS (3): MODA + filtrado (MÉTODO ÚNICO)
            gastos_indirectos, ops_excluidas = await tdv_queries.obtener_gastos_indirectos_formula(
                version_calculo=input_data.version_calculo,
                codigo_estilo=input_data.codigo_estilo,  # Para estilo recurrente
            )
            metodo_usado_indirectos = "moda_filtrado_10x"
            logger.info(
                f" Gastos indirectos (MODA+filtrado) obtenidos: {gastos_indirectos}"
            )

        except Exception as e:
            logger.warning(
                f" No se pudo obtener costos para {input_data.codigo_estilo}: {e}"
            )
            raise ValueError(
                f"Estilo {input_data.codigo_estilo} marcado como recurrente pero sin datos históricos"
            )

        #  CONSOLIDAR COMPONENTES: Directos + Indirectos
        componentes = []
        costos_validados = {}
        alertas = []
        componentes_faltantes = []

        # Procesar COSTOS DIRECTOS (4) del histórico específico
        costos_directos = [
            "costo_textil",
            "costo_manufactura",
            "costo_avios",
            "costo_materia_prima",
        ]

        for componente in costos_directos:
            valor = costos_hist.get(componente, 0)

            # Si no está en histórico, usar fallback
            if valor is None or valor <= 0:
                componentes_faltantes.append(componente)
                logger.warning(
                    f" {componente} no disponible en histórico de {input_data.codigo_estilo}"
                )
                if componente in factores.RANGOS_SEGURIDAD:
                    valor = factores.RANGOS_SEGURIDAD[componente]["min"]
                    alertas.append(
                        f" {componente}: no en histórico, usando valor mínimo ${valor:.2f}"
                    )
                else:
                    valor = 0.5
                    alertas.append(
                        f" {componente}: no en histórico, usando fallback ${valor:.2f}"
                    )

            # Aplicar rangos de seguridad
            valor_original = valor
            valor_validado, fue_ajustado = factores.validar_rango_seguridad(
                valor, componente
            )
            costos_validados[componente] = valor_validado

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

            # Si no está disponible, usar fallback
            if valor is None or valor <= 0:
                componentes_faltantes.append(componente)
                logger.warning(
                    f" {componente} no disponible en fórmula MODA para {input_data.codigo_estilo}"
                )
                if componente in factores.RANGOS_SEGURIDAD:
                    valor = factores.RANGOS_SEGURIDAD[componente]["min"]
                    alertas.append(
                        f" {componente}: no en MODA, usando valor mínimo ${valor:.2f}"
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
                f" {len(ops_excluidas)} OPs excluidas como outliers en cálculo de MODA"
            )

        #  ADVERTENCIA SI HAY COMPONENTES FALTANTES
        if componentes_faltantes:
            alertas.append(
                f" Componentes sin datos históricos: {', '.join(componentes_faltantes)}"
            )
            logger.warning(
                f" Estilo {input_data.codigo_estilo} recurrente pero faltan: {componentes_faltantes}"
            )

        #  CALCULAR TOTALES Y FACTORES
        costo_base_total = sum(costos_validados.values())

        # Determinar esfuerzo (usar histórico si disponible)
        esfuerzo_historico = int(costos_hist.get("esfuerzo_promedio", 6))
        if esfuerzo_historico < 1 or esfuerzo_historico > 10:
            esfuerzo_historico = 6  # Fallback seguro

        _, factor_esfuerzo = factores.obtener_factor_esfuerzo(esfuerzo_historico)

        # Determinar categoría estilo para factor
        volumen = await tdv_queries.obtener_volumen_historico_estilo(
            input_data.codigo_estilo, input_data.version_calculo
        )
        categoria_estilo = "Muy Recurrente" if volumen >= 4000 else "Recurrente"
        factor_estilo = factores.obtener_factor_estilo(categoria_estilo)

        # Vector total y precio final
        vector_total = factor_lote * factor_esfuerzo * factor_estilo * factor_marca
        precio_final = costo_base_total * (1 + 0.15 * vector_total)
        margen_aplicado = 15 * vector_total

        #  OBTENER INFORMACIÓN COMERCIAL
        info_comercial = await self._obtener_info_comercial_mejorada(input_data)

        #  VALIDACIONES Y ALERTAS MEJORADAS
        total_componentes = 7
        validaciones = [
            " Estilo RECURRENTE procesado con método COORDINADO",
            f" Costos directos (4): {metodo_usado_directos}",
            f" Gastos indirectos (3): {metodo_usado_indirectos}",
            f" Registros históricos usados: {costos_hist.get('registros_encontrados', 0)}",
            f" Versión de cálculo: {input_data.version_calculo}",
            f" Componentes con datos: {total_componentes - len(componentes_faltantes)}/{total_componentes}",
            f" Precisión estimada: {costos_hist.get('precision_estimada', 0.8):.1%}",
        ]

        if costos_hist.get("total_ajustados", 0) > 0:
            alertas.append(
                f" {costos_hist.get('total_ajustados')} valores ajustados por límites de seguridad"
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
            categoria_lote=categoria_lote,
            categoria_esfuerzo=esfuerzo_historico,
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
            factor_lote=factor_lote,
            factor_esfuerzo=factor_esfuerzo,
            factor_estilo=factor_estilo,
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
            volumen_historico=volumen,
            metadatos_adicionales={
                "estrategia_costos": "coordinado_directo+moda",
                "esfuerzo_historico": esfuerzo_historico,
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
        categoria_lote: str,
        factor_lote: float,
        factor_marca: float,
    ) -> CotizacionResponse:
        """
         FUNCIÓN COMPLETAMENTE CORREGIDA: Procesa estilos nuevos con WIPs y ruta automática
        """

        logger.info(
            f"🆕 PROCESANDO estilo NUEVO: {input_data.codigo_estilo} ({input_data.version_calculo})"
        )

        #  VALIDAR QUE TENGA WIPS (REQUERIDO PARA ESTILOS NUEVOS)
        if (not input_data.wips_textiles or len(input_data.wips_textiles) == 0) and (
            not input_data.wips_manufactura or len(input_data.wips_manufactura) == 0
        ):
            raise ValueError(
                "Para estilos nuevos se requieren WIPs textiles y/o manufactura seleccionadas"
            )

        #  OBTENER COSTOS WIPS CON ANÁLISIS INTELIGENTE
        try:
            costos_wips = await tdv_queries.obtener_costos_wips_por_estabilidad(
                input_data.tipo_prenda, input_data.version_calculo
            )
            logger.info(
                f" Costos WIPs obtenidos: {len(costos_wips)} WIPs disponibles"
            )
        except Exception as e:
            logger.error(f" Error obteniendo costos WIPs: {e}")
            raise ValueError(
                f"No se pudieron obtener costos de WIPs para {input_data.tipo_prenda}"
            )

        #  PROCESAR WIPS CON VALIDACIÓN ROBUSTA
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
                f" Costo textil ajustado: ${costo_textil_total:.2f} → ${costo_textil:.2f}"
            )
        if manufactura_ajustado:
            alertas.append(
                f" Costo manufactura ajustado: ${costo_manufactura_total:.2f} → ${costo_manufactura:.2f}"
            )

        #  OBTENER COSTOS COMPLEMENTARIOS
        costos_complementarios = await self._obtener_costos_complementarios_mejorados(
            input_data, componentes, alertas, es_estilo_nuevo=True
        )

        #  CALCULAR TOTALES
        costo_base_total = (
            costo_textil + costo_manufactura + sum(costos_complementarios.values())
        )

        #  FACTORES PARA ESTILOS NUEVOS
        esfuerzo_estimado = 7  # Default conservador para nuevos
        if hasattr(input_data, "esfuerzo_total") and input_data.esfuerzo_total:
            esfuerzo_estimado = max(1, min(10, int(input_data.esfuerzo_total)))

        _, factor_esfuerzo = factores.obtener_factor_esfuerzo(esfuerzo_estimado)
        factor_estilo = factores.obtener_factor_estilo("Nuevo")

        vector_total = factor_lote * factor_esfuerzo * factor_estilo * factor_marca
        precio_final = costo_base_total * (1 + 0.15 * vector_total)
        margen_aplicado = 15 * vector_total

        #  INFORMACIÓN COMERCIAL
        info_comercial = await self._obtener_info_comercial_mejorada(input_data)

        #  VALIDACIONES Y CONFIGURACIÓN WIPS
        validaciones = [
            " Estilo NUEVO procesado correctamente",
            f" WIPs configuradas: {len(input_data.wips_textiles or [])} textiles + {len(input_data.wips_manufactura or [])} manufactura",
            f" Versión de cálculo: {input_data.version_calculo}",
            f" Costos WIP obtenidos: {len(costos_wips)} disponibles",
            " Estrategia: configuración manual de WIPs",
        ]

        # Configuración WIPs para respuesta
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
            categoria_lote=categoria_lote,
            categoria_esfuerzo=esfuerzo_estimado,
            categoria_estilo="Nuevo",
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
            factor_lote=factor_lote,
            factor_esfuerzo=factor_esfuerzo,
            factor_estilo=factor_estilo,
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
            volumen_historico=0,
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
        """ Procesa WIPs seleccionadas con validación robusta"""

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
            f" WIPs {grupo} procesadas: {len(wips_seleccionadas)} → ${costo_total:.2f}"
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

        #  OBTENER ÚLTIMO COSTO DE MATERIALES
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
                    alertas.append(f" {comp}: ajustado por límites de seguridad")

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
                f" Costos materiales obtenidos: MP=${costos_validados.get('costo_materia_prima', 0):.2f}, Avíos=${costos_validados.get('costo_avios', 0):.2f}"
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

        #  OBTENER GASTOS INDIRECTOS (usando MODA para RECURRENTES, genéricos para NUEVOS)
        try:
            if es_estilo_nuevo:
                #  ESTILOS NUEVOS: Usar función con MODA por marca + familia + tipo
                gastos, ops_excluidas = await tdv_queries.obtener_gastos_por_estilo_nuevo(
                    marca=input_data.cliente_marca,
                    familia_prenda=input_data.familia_producto,
                    tipo_prenda=input_data.tipo_prenda,
                    version_calculo=input_data.version_calculo,
                )
                metodo_gastos = "MODA (nuevo por familia/tipo)"
            else:
                #  ESTILOS RECURRENTES: Usar función con MODA por código_estilo exacto
                gastos, ops_excluidas = await tdv_queries.obtener_gastos_por_estilo_recurrente(
                    codigo_estilo=input_data.codigo_estilo,
                    version_calculo=input_data.version_calculo,
                )
                metodo_gastos = "MODA (recurrente específico)"

            for comp in [
                "costo_indirecto_fijo",
                "gasto_administracion",
                "gasto_ventas",
            ]:
                valor = gastos.get(comp, 0)
                #  NOTA: Los límites de seguridad ya NO se aplican a estos 3 costos
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
        """ Obtiene información comercial con manejo robusto de errores"""
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

    def _categorizar_lote(self, categoria_input: str) -> Tuple[str, float]:
        """Convierte categoría de lote del frontend a factor"""
        for categoria, config in factores.RANGOS_LOTE.items():
            if categoria == categoria_input:
                return categoria, config["factor"]
        return "Lote Mediano", 1.05  # Default seguro

    def _generar_id_cotizacion(self) -> str:
        """Genera ID único para cotización"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid4())[:8].upper()
        return f"COT_{timestamp}_{unique_id}"


# Instancia global del cotizador
cotizador_tdv = CotizadorTDV()

