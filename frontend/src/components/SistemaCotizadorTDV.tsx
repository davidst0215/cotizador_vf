"use client"

import React, { useState, useEffect, useCallback, useRef, useMemo } from "react"
import {
  Settings,
  DollarSign,
  Package,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Calendar,
  FileText,
  Download,
  Printer,
  RefreshCw,
  Database,
} from "lucide-react"

// Constantes del sistema
const CATEGORIAS_LOTE = {
  "Micro Lote": { rango: "1-50" },
  "Lote Pequeño": { rango: "51-500" },
  "Lote Mediano": { rango: "501-1000" },
  "Lote Grande": { rango: "1001-4000" },
  "Lote Masivo": { rango: "4001+" },
}

const API_BASE_URL = "http://localhost:8000"

// Interfaces TypeScript
interface WipDisponible {
  wip_id: string
  nombre: string
  costo_actual: number
  disponible: boolean
  grupo: string
}

interface WipSeleccionada {
  wip_id: string
  factor_ajuste: number
  costo_base: number
}

interface EstiloSimilar {
  codigo: string
  familia_producto: string
  tipo_prenda: string
  temporada: string
  ops_encontradas: number
  costo_promedio: number
}

interface FormData {
  cliente_marca: string
  temporada: string
  categoria_lote: string
  familia_producto: string
  tipo_prenda: string
  codigo_estilo: string
  usuario: string
  version_calculo: string
}

interface ComponenteCosto {
  nombre: string
  costo_unitario: number
  fuente: string
  ajustado_por_rango?: boolean
}

interface InfoComercial {
  ops_utilizadas: number
  historico_volumen: {
    volumen_total_6m: number
    volumen_promedio: number
    ops_producidas: number
  }
  tendencias_costos: Array<{
    año: number
    mes: number
    costo_textil_promedio: number
    costo_manufactura_promedio: number
    ops_mes: number
  }>
}

interface ResultadoCotizacion {
  id_cotizacion: string
  fecha_cotizacion: string
  inputs: FormData
  componentes: ComponenteCosto[]
  costo_textil: number
  costo_manufactura: number
  costo_avios: number
  costo_materia_prima: number
  costo_indirecto_fijo: number
  gasto_administracion: number
  gasto_ventas: number
  costo_base_total: number
  factor_lote: number
  factor_esfuerzo: number
  factor_estilo: number
  factor_marca: number
  vector_total: number
  precio_final: number
  margen_aplicado: number
  validaciones: string[]
  alertas: string[]
  info_comercial: InfoComercial
  categoria_esfuerzo: number
  categoria_estilo: string
  version_calculo_usada?: string
  volumen_historico?: number
}

interface OpReal {
    cod_ordpro: string
  estilo_propio: string
  cliente: string
  fecha_facturacion: string | null
  prendas_requeridas: number
  monto_factura: number
  precio_unitario: number
  costos_componentes: {
    textil: number
    manufactura: number
    avios: number
    materia_prima: number
    indirecto_fijo: number
    gasto_admin: number
    gasto_ventas: number
  }
  costo_total_unitario: number
  costo_total_original?: number    // ✅ NUEVO
  fue_ajustado?: boolean          // ✅ NUEVO
  esfuerzo_total: number
}

interface OpsResponse {
  ops_data: {
    ops_utilizadas: OpReal[]
    metodo_utilizado: string
    estadisticas: {
      total_ops: number
      costo_promedio: number
      costo_min: number
      costo_max: number
      esfuerzo_promedio: number
      rango_fechas?: {
        desde: string
        hasta: string
      }
    }
    parametros_busqueda: {
      codigo_estilo: string | null
      familia_producto: string | null
      tipo_prenda: string | null
      cliente: string | null
      version_calculo: string
    }
    rangos_aplicados?: boolean
  }
  timestamp: string
  total_ops_encontradas: number
}

// ✅ NUEVA: Interface para auto-completado
interface AutoCompletadoInfo {
  autocompletado_disponible: boolean
  info_estilo?: {
    familia_producto: string
    tipo_prenda: string
    categoria: string
    volumen_total: number
  }
  campos_sugeridos?: {
    familia_producto: string
    tipo_prenda: string
  }
}

const SistemaCotizadorTDV = () => {
  // Estados principales
  const [pestanaActiva, setPestanaActiva] = useState<"formulario" | "resultados">("formulario")
  const [wipsDisponibles, setWipsDisponibles] = useState<{
    wips_textiles: WipDisponible[]
    wips_manufactura: WipDisponible[]
  }>({ wips_textiles: [], wips_manufactura: [] })
  const [cotizacionActual, setCotizacionActual] = useState<ResultadoCotizacion | null>(null)
  const [cargando, setCargando] = useState(false)
  
  // Estados de datos maestros dinámicos
  const [clientesDisponibles, setClientesDisponibles] = useState<string[]>([])
  const [familiasDisponibles, setFamiliasDisponibles] = useState<string[]>([])
  const [tiposDisponibles, setTiposDisponibles] = useState<string[]>([])
  const [cargandoFamilias, setCargandoFamilias] = useState(false)
  const [cargandoTipos, setCargandoTipos] = useState(false)

  // Estados para OPs reales
  const [opsReales, setOpsReales] = useState<OpsResponse | null>(null)
  const [cargandoOps, setCargandoOps] = useState(false)
  const [errorOps, setErrorOps] = useState<string | null>(null)

  // ✅ CORREGIDO: Estados del formulario con mejor estructura
  const [formData, setFormData] = useState<FormData>({
    cliente_marca: "LACOSTE",
    temporada: "",
    categoria_lote: "Lote Mediano",
    familia_producto: "",
    tipo_prenda: "",
    codigo_estilo: "",
    usuario: "Usuario Demo",
    version_calculo: "FLUIDA",
  })

  // Estados para búsqueda de estilos
  const [estilosEncontrados, setEstilosEncontrados] = useState<EstiloSimilar[]>([])
  const [buscandoEstilo, setBuscandoEstilo] = useState(false)
  const [esEstiloNuevo, setEsEstiloNuevo] = useState(false)

  // ✅ NUEVO: Estado para auto-completado
  const [infoAutoCompletado, setInfoAutoCompletado] = useState<AutoCompletadoInfo | null>(null)

  // Estados para WIPs seleccionadas
  const [wipsTextiles, setWipsTextiles] = useState<WipSeleccionada[]>([])
  const [wipsManufactura, setWipsManufactura] = useState<WipSeleccionada[]>([])

  // Referencias para evitar re-renders
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  // ✅ CORRECCIÓN CRÍTICA: Callback estable sin dependencias complejas
  const manejarCambioFormulario = useCallback((campo: keyof FormData, valor: string) => {
    console.log(`📝 Cambiando ${campo}: ${valor}`)
    
    setFormData(prev => ({
      ...prev,
      [campo]: valor,
      // Limpiar tipo si cambia familia
      ...(campo === "familia_producto" ? { tipo_prenda: "" } : {})
    }))
  }, [])

  // ✅ CORRECCIÓN: Side-effects separados por responsabilidad
  
  // Efecto 1: Recargar cuando cambia version_calculo
  useEffect(() => {
    const recargarDatosVersion = async () => {
      console.log(`🔄 Recargando datos para versión: ${formData.version_calculo}`)
      
      try {
        // Cargar datos principales
        await Promise.all([
          cargarWipsDisponibles(formData.version_calculo),
          cargarClientesDisponibles(formData.version_calculo),
          cargarFamiliasProductos(formData.version_calculo)
        ])
        
        // Recargar tipos si hay familia
        if (formData.familia_producto) {
          await cargarTiposPrenda(formData.familia_producto, formData.version_calculo)
        }
        
        // Recargar WIPs si hay tipo y es nuevo
        if (formData.tipo_prenda && esEstiloNuevo) {
          await cargarWipsPorTipoPrenda(formData.tipo_prenda, formData.version_calculo)
        }
        
        // Re-verificar estilo si existe
        if (formData.codigo_estilo && formData.codigo_estilo.length >= 3) {
          await verificarYBuscarEstilo(formData.codigo_estilo, formData.cliente_marca, formData.version_calculo)
        }
        
        console.log(`✅ Datos recargados para versión: ${formData.version_calculo}`)
      } catch (error) {
        console.error(`❌ Error recargando datos:`, error)
      }
    }
    
    recargarDatosVersion()
  }, [formData.version_calculo]) // Solo depende de version_calculo

  // Efecto 2: Cargar tipos cuando cambia familia
  useEffect(() => {
    if (formData.familia_producto) {
      cargarTiposPrenda(formData.familia_producto, formData.version_calculo)
    } else {
      setTiposDisponibles([])
    }
  }, [formData.familia_producto, formData.version_calculo])

  // Efecto 3: Cargar WIPs cuando cambia tipo (solo para estilos nuevos)
  useEffect(() => {
    if (formData.tipo_prenda && esEstiloNuevo) {
      cargarWipsPorTipoPrenda(formData.tipo_prenda, formData.version_calculo)
    }
  }, [formData.tipo_prenda, formData.version_calculo, esEstiloNuevo])

  // Efecto 4: Búsqueda debounced de estilos
  useEffect(() => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current)
    }
    
    if (formData.codigo_estilo && formData.codigo_estilo.length >= 3) {
      debounceTimeoutRef.current = setTimeout(() => {
        verificarYBuscarEstilo(formData.codigo_estilo, formData.cliente_marca, formData.version_calculo)
      }, 300)
    } else {
      setEstilosEncontrados([])
      setEsEstiloNuevo(true)
      setInfoAutoCompletado(null)
    }
    
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
    }
  }, [formData.codigo_estilo, formData.cliente_marca, formData.version_calculo])

  // Cargar datos iniciales
  useEffect(() => {
    const cargarDatosIniciales = async () => {
      await Promise.all([
        cargarWipsDisponibles(formData.version_calculo),
        cargarClientesDisponibles(formData.version_calculo),
        cargarFamiliasProductos(formData.version_calculo)
      ])
    }
    cargarDatosIniciales()
  }, []) // Solo una vez al montar

  // Limpiar al desmontar
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  // ========================================
  // 🔧 FUNCIONES DE CARGA CORREGIDAS
  // ========================================

  const cargarWipsDisponibles = useCallback(async (versionCalculo: string = 'FLUIDA') => {
    try {
      const response = await fetch(`${API_BASE_URL}/wips-disponibles?version_calculo=${versionCalculo}`)
      if (response.ok) {
        const data = await response.json()
        setWipsDisponibles(data)
        console.log(`✅ WIPs cargadas para ${versionCalculo}: ${data.wips_textiles.length + data.wips_manufactura.length}`)
      } else {
        console.error('Error cargando WIPs:', response.statusText)
        setWipsDisponibles({ wips_textiles: [], wips_manufactura: [] })
      }
    } catch (error) {
      console.error('Error conectando con backend:', error)
      setWipsDisponibles({ wips_textiles: [], wips_manufactura: [] })
    }
  }, [])

  const cargarWipsPorTipoPrenda = useCallback(async (tipoPrenda: string, versionCalculo: string) => {
    if (!tipoPrenda) {
      setWipsDisponibles({ wips_textiles: [], wips_manufactura: [] })
      return
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/wips-disponibles?tipo_prenda=${encodeURIComponent(tipoPrenda)}&version_calculo=${versionCalculo}`
      )
      if (response.ok) {
        const data = await response.json()
        setWipsDisponibles(data)
        setWipsTextiles([])
        setWipsManufactura([])
        console.log(`✅ WIPs específicas cargadas para ${tipoPrenda} (${versionCalculo})`)
      }
    } catch (error) {
      console.error('Error cargando WIPs específicas:', error)
    }
  }, [])

  const cargarClientesDisponibles = useCallback(async (versionCalculo: string = 'FLUIDA') => {
    try {
      const response = await fetch(`${API_BASE_URL}/clientes?version_calculo=${versionCalculo}`)
      if (response.ok) {
        const data = await response.json()
        setClientesDisponibles(data.clientes)
        console.log(`✅ Clientes cargados para ${versionCalculo}: ${data.clientes.length}`)
      }
    } catch (error) {
      console.error('Error cargando clientes:', error)
      setClientesDisponibles([])
    }
  }, [])

  const cargarFamiliasProductos = useCallback(async (versionCalculo: string = 'FLUIDA') => {
    setCargandoFamilias(true)
    try {
      const response = await fetch(`${API_BASE_URL}/familias-productos?version_calculo=${versionCalculo}`)
      if (response.ok) {
        const data = await response.json()
        setFamiliasDisponibles(data.familias)
        console.log(`✅ Familias cargadas para ${versionCalculo}: ${data.familias.length}`)
      }
    } catch (error) {
      console.error('Error cargando familias:', error)
      setFamiliasDisponibles([])
    } finally {
      setCargandoFamilias(false)
    }
  }, [])

  const cargarTiposPrenda = useCallback(async (familia: string, versionCalculo: string = 'FLUIDA') => {
    if (!familia) {
      setTiposDisponibles([])
      return
    }

    setCargandoTipos(true)
    try {
      const response = await fetch(
        `${API_BASE_URL}/tipos-prenda/${encodeURIComponent(familia)}?version_calculo=${versionCalculo}`
      )
      if (response.ok) {
        const data = await response.json()
        setTiposDisponibles(data.tipos)
        console.log(`✅ Tipos cargados para ${familia} (${versionCalculo}): ${data.tipos.length}`)
      }
    } catch (error) {
      console.error('Error cargando tipos:', error)
      setTiposDisponibles([])
    } finally {
      setCargandoTipos(false)
    }
  }, [])

  // ✅ NUEVA: Función completa de verificación y búsqueda
  const verificarYBuscarEstilo = useCallback(async (codigoEstilo: string, cliente: string, versionCalculo: string) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    if (!codigoEstilo || codigoEstilo.length < 3) {
      setEstilosEncontrados([])
      setEsEstiloNuevo(true)
      setInfoAutoCompletado(null)
      return
    }

    setBuscandoEstilo(true)
    
    const abortController = new AbortController()
    abortControllerRef.current = abortController

    try {
      // ✅ PASO 1: Verificación completa con auto-completado
      const responseVerificar = await fetch(
        `${API_BASE_URL}/verificar-estilo-completo/${codigoEstilo}?version_calculo=${versionCalculo}`,
        { signal: abortController.signal }
      )
      
      if (responseVerificar.ok && !abortController.signal.aborted) {
        const verificacion = await responseVerificar.json()
        console.log(`🔍 Verificación completa ${codigoEstilo}:`, verificacion)
        
        const esNuevo = verificacion.es_estilo_nuevo
        setEsEstiloNuevo(esNuevo)
        
        // ✅ AUTO-COMPLETADO AUTOMÁTICO
        if (!esNuevo && verificacion.autocompletado?.disponible) {
          const { familia_producto, tipo_prenda } = verificacion.autocompletado
          
          if (familia_producto && tipo_prenda) {
            console.log(`🎯 Auto-completando: ${familia_producto} → ${tipo_prenda}`)
            
            setFormData(prev => ({
              ...prev,
              familia_producto,
              tipo_prenda
            }))
            
            // Cargar tipos para la familia auto-completada
            await cargarTiposPrenda(familia_producto, versionCalculo)
            
            setInfoAutoCompletado({
              autocompletado_disponible: true,
              info_estilo: {
                familia_producto,
                tipo_prenda,
                categoria: verificacion.categoria,
                volumen_total: verificacion.volumen_historico
              },
              campos_sugeridos: { familia_producto, tipo_prenda }
            })
          }
        } else {
          setInfoAutoCompletado(null)
        }
      }
      
      // ✅ PASO 2: Buscar estilos similares
      const responseSimilares = await fetch(
        `${API_BASE_URL}/buscar-estilos/${codigoEstilo}?cliente=${encodeURIComponent(cliente)}&limite=10&version_calculo=${versionCalculo}`,
        { signal: abortController.signal }
      )
      
      if (responseSimilares.ok && !abortController.signal.aborted) {
        const estilos = await responseSimilares.json()
        setEstilosEncontrados(estilos)
        console.log(`🔍 Estilos similares encontrados: ${estilos.length}`)
      }
      
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        console.error('Error en verificación:', error)
        setEstilosEncontrados([])
        setEsEstiloNuevo(true)
        setInfoAutoCompletado(null)
      }
    } finally {
      if (!abortController.signal.aborted) {
        setBuscandoEstilo(false)
      }
    }
  }, [])

  const cargarOpsReales = useCallback(async (cotizacion: ResultadoCotizacion) => {
    setCargandoOps(true)
    setErrorOps(null)
    
    try {
      const payload = {
        cliente_marca: cotizacion.inputs.cliente_marca,
        temporada: cotizacion.inputs.temporada,
        categoria_lote: cotizacion.inputs.categoria_lote,
        familia_producto: cotizacion.inputs.familia_producto,
        tipo_prenda: cotizacion.inputs.tipo_prenda,
        codigo_estilo: cotizacion.inputs.codigo_estilo,
        usuario: cotizacion.inputs.usuario,
        version_calculo: cotizacion.inputs.version_calculo,
        wips_textiles: null,
        wips_manufactura: null
      }

      const response = await fetch(`${API_BASE_URL}/ops-utilizadas-cotizacion`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (response.ok) {
        const resultado = await response.json()
        setOpsReales(resultado)
        console.log(`✅ OPs reales cargadas: ${resultado.total_ops_encontradas}`)
      } else {
        const errorData = await response.json()
        setErrorOps(errorData.mensaje || 'Error cargando OPs')
      }
    } catch (error) {
      console.error("Error cargando OPs reales:", error)
      setErrorOps('Error de conexión al cargar OPs de referencia')
    } finally {
      setCargandoOps(false)
    }
  }, [])

  // ========================================
  // 🔧 FUNCIONES DE INTERACCIÓN MEJORADAS
  // ========================================

  const seleccionarEstiloSimilar = useCallback((estilo: EstiloSimilar) => {
    console.log(`🎯 Seleccionando estilo similar:`, estilo)
    
    setFormData(prev => ({
      ...prev,
      familia_producto: estilo.familia_producto,
      tipo_prenda: estilo.tipo_prenda,
    }))
    setEstilosEncontrados([])
    cargarTiposPrenda(estilo.familia_producto, formData.version_calculo)
  }, [formData.version_calculo, cargarTiposPrenda])

  const toggleWipTextil = useCallback((wip: WipDisponible) => {
    setWipsTextiles(prev => {
      const existe = prev.find(w => w.wip_id === wip.wip_id)
      if (existe) {
        return prev.filter(w => w.wip_id !== wip.wip_id)
      } else {
        return [...prev, { wip_id: wip.wip_id, factor_ajuste: 1.0, costo_base: wip.costo_actual }]
      }
    })
  }, [])

  const toggleWipManufactura = useCallback((wip: WipDisponible) => {
    setWipsManufactura(prev => {
      const existe = prev.find(w => w.wip_id === wip.wip_id)
      if (existe) {
        return prev.filter(w => w.wip_id !== wip.wip_id)
      } else {
        return [...prev, { wip_id: wip.wip_id, factor_ajuste: 1.0, costo_base: wip.costo_actual }]
      }
    })
  }, [])

  const actualizarFactorWip = useCallback((
    setWips: React.Dispatch<React.SetStateAction<WipSeleccionada[]>>,
    wipId: string,
    nuevoFactor: string
  ) => {
    const factor = parseFloat(nuevoFactor) || 1.0
    setWips(prev =>
      prev.map(w => (w.wip_id === wipId ? 
        { ...w, factor_ajuste: factor } : w))
    )
  }, [])

  const validarFormulario = useCallback(() => {
    const errores = []
    
    if (!formData.cliente_marca) errores.push("Cliente/Marca es requerido")
    if (!formData.temporada) errores.push("Temporada es requerida")
    if (!formData.familia_producto) errores.push("Familia de Producto es requerida")
    if (!formData.tipo_prenda) errores.push("Tipo de Prenda es requerido")
    if (!formData.codigo_estilo) errores.push("Código de Estilo es requerido")
    
    if (esEstiloNuevo && formData.codigo_estilo) {
      if (wipsTextiles.length === 0 && wipsManufactura.length === 0) {
        errores.push("Estilo nuevo requiere al menos una WIP")
      }
    }
    
    return errores
  }, [formData, esEstiloNuevo, wipsTextiles.length, wipsManufactura.length])

  const procesarCotizacion = useCallback(async () => {
    setCargando(true)
    try {
      const payload = {
        cliente_marca: formData.cliente_marca,
        temporada: formData.temporada,
        categoria_lote: formData.categoria_lote,
        familia_producto: formData.familia_producto,
        tipo_prenda: formData.tipo_prenda,
        codigo_estilo: formData.codigo_estilo,
        usuario: formData.usuario,
        version_calculo: formData.version_calculo,
        wips_textiles: esEstiloNuevo ? wipsTextiles : null,
        wips_manufactura: esEstiloNuevo ? wipsManufactura : null,
      }

      console.log(`🚀 Procesando cotización:`, payload)

      const response = await fetch(`${API_BASE_URL}/cotizar`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (response.ok) {
        const resultado = await response.json()
        setCotizacionActual(resultado)
        
        await cargarOpsReales(resultado)
        
        setPestanaActiva("resultados")
        console.log(`✅ Cotización exitosa: ${resultado.id_cotizacion}`)
      } else {
        const errorData = await response.json()
        console.error('Error en cotización:', errorData)
        alert(`Error: ${errorData.mensaje || 'Error procesando cotización'}`)
      }
    } catch (error) {
      console.error("Error procesando cotización:", error)
      alert('Error de conexión con el servidor. Verifique que el backend esté ejecutándose.')
    } finally {
      setCargando(false)
    }
  }, [formData, esEstiloNuevo, wipsTextiles, wipsManufactura, cargarOpsReales])

  // ========================================
  // 🎨 COMPONENTES MEMOIZADOS CORREGIDOS
  // ========================================

  // ✅ COMPONENTE: Switch de versión
  const SwitchVersionCalculo = useMemo(() => (
    <div className="bg-white rounded-xl shadow-md border border-gray-100 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Database className="h-5 w-5" style={{ color: "#821417" }} />
          <div>
            <h3 className="font-semibold" style={{ color: "#821417" }}>
              Versión de Datos
            </h3>
            <p className="text-sm text-gray-600">
              Selecciona el tipo de cálculo para la cotización
            </p>
            <div className="text-xs text-gray-500 mt-1">
              {(cargandoFamilias || cargandoTipos) ? '🔄 Recargando datos...' : '✅ Datos actualizados'}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4 bg-gray-50 px-4 py-2 rounded-lg">
          <span 
            className={`font-medium transition-colors ${
              formData.version_calculo === 'FLUIDA' ? 'text-gray-900' : 'text-gray-400'
            }`}
            style={{ 
              fontWeight: formData.version_calculo === 'FLUIDA' ? '600' : '400',
              textTransform: 'uppercase'
            }}
          >
            FLUIDA
          </span>
          <button
            type="button"
            onClick={() => {
              const nuevaVersion = formData.version_calculo === 'FLUIDA' ? 'truncado' : 'FLUIDA'
              console.log(`🔄 Cambiando versión: ${formData.version_calculo} → ${nuevaVersion}`)
              manejarCambioFormulario('version_calculo', nuevaVersion)
            }}
            className="relative inline-flex h-8 w-16 items-center rounded-full transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2"
            style={{ 
              backgroundColor: formData.version_calculo === 'FLUIDA' ? '#821417' : '#bd4c42'
            }}
          >
            <span 
              className="inline-block h-6 w-6 transform rounded-full bg-white shadow-lg transition-transform duration-300"
              style={{
                transform: formData.version_calculo === 'FLUIDA' ? 'translateX(2px)' : 'translateX(34px)'
              }}
            />
          </button>
          <span 
            className={`font-medium transition-colors ${
              formData.version_calculo === 'truncado' ? 'text-gray-900' : 'text-gray-400'
            }`}
            style={{ 
              fontWeight: formData.version_calculo === 'truncado' ? '600' : '400',
              textTransform: 'uppercase'
            }}
          >
            TRUNCADO
          </span>
        </div>
      </div>
      
      <div className="mt-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${formData.version_calculo === 'FLUIDA' ? 'bg-green-500' : 'bg-blue-500'}`}></div>
          <span className="text-xs text-gray-600">
            Usando datos: <strong className="uppercase">{formData.version_calculo}</strong>
          </span>
        </div>
        
        <div className="text-xs text-gray-500">
          📊 {familiasDisponibles.length} familias | {tiposDisponibles.length} tipos
        </div>
      </div>
    </div>
  ), [formData.version_calculo, cargandoFamilias, cargandoTipos, familiasDisponibles.length, tiposDisponibles.length, manejarCambioFormulario])

  // ✅ COMPONENTE: Campo código estilo corregido
  const CampoCodigoEstilo = useMemo(() => (
    <div className="space-y-2">
      <label className="block text-sm font-semibold" style={{ color: "#821417" }}>
        Código de Estilo
      </label>
      <div className="relative">
        <input
          type="text"
          value={formData.codigo_estilo}
          onChange={(e) => manejarCambioFormulario("codigo_estilo", e.target.value.toUpperCase().trim())}
          className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-opacity-50 transition-colors"
          placeholder="ej: LAC001-V25, GRY2024-P01"
          autoComplete="off"
          spellCheck={false}
        />
        {buscandoEstilo && (
          <div className="absolute right-3 top-4">
            <RefreshCw className="h-5 w-5 animate-spin" style={{ color: "#bd4c42" }} />
          </div>
        )}
      </div>

      {/* ✅ NUEVO: Información de auto-completado */}
      {infoAutoCompletado?.autocompletado_disponible && (
        <div
          className="mt-2 p-3 rounded-xl border-2"
          style={{ backgroundColor: "#e8f5e8", borderColor: "#4ade80" }}
        >
          <div className="text-sm font-semibold mb-2" style={{ color: "#15803d" }}>
            ✅ Auto-completado aplicado:
          </div>
          <div className="text-xs text-green-700">
            📁 Familia: <strong>{infoAutoCompletado.campos_sugeridos?.familia_producto}</strong> | 
            🏷️ Tipo: <strong>{infoAutoCompletado.campos_sugeridos?.tipo_prenda}</strong> | 
            📊 Categoría: <strong>{infoAutoCompletado.info_estilo?.categoria}</strong>
          </div>
        </div>
      )}

      {/* Estilos similares */}
      {estilosEncontrados.length > 0 && (
        <div
          className="mt-2 p-3 rounded-xl border-2"
          style={{ backgroundColor: "#fff4e1", borderColor: "#ffbba8" }}
        >
          <div className="text-sm font-semibold mb-2" style={{ color: "#821417" }}>
            Estilos similares encontrados:
          </div>
          {estilosEncontrados.map((estilo, idx) => (
            <button
              key={idx}
              onClick={() => seleccionarEstiloSimilar(estilo)}
              className="w-full text-left p-2 rounded-lg hover:shadow-md transition-all mb-2"
              style={{ backgroundColor: "#ffbba8" }}
            >
              <div className="font-semibold text-sm" style={{ color: "#821417" }}>
                {estilo.codigo}
              </div>
              <div className="text-xs" style={{ color: "#bd4c42" }}>
                {estilo.familia_producto} - {estilo.tipo_prenda} | {estilo.ops_encontradas} OPs | $
                {estilo.costo_promedio.toFixed(2)}
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Indicador de estado del estilo */}
      {formData.codigo_estilo && !buscandoEstilo && (
        <div className="flex items-center gap-2">
          <div
            className={`text-xs px-2 py-1 rounded-full inline-block text-white`}
            style={{
              backgroundColor: esEstiloNuevo ? "#fa8072" : "#bd4c42",
            }}
          >
            {esEstiloNuevo ? "🆕 Estilo Nuevo" : "🔄 Estilo Recurrente"}
          </div>
          
          {infoAutoCompletado?.info_estilo?.volumen_total && (
            <div className="text-xs text-gray-600">
              📦 Volumen histórico: {infoAutoCompletado.info_estilo.volumen_total.toLocaleString()} prendas
            </div>
          )}
        </div>
      )}
    </div>
  ), [
    formData.codigo_estilo, 
    buscandoEstilo, 
    estilosEncontrados, 
    esEstiloNuevo, 
    infoAutoCompletado,
    manejarCambioFormulario, 
    seleccionarEstiloSimilar
  ])

  // ✅ COMPONENTE: Ruta textil recomendada corregida
  const RutaTextilRecomendada = React.memo(() => {
  const [rutaTextil, setRutaTextil] = useState<any>(null)
  const [cargandoRuta, setCargandoRuta] = useState(false)
  const [errorRuta, setErrorRuta] = useState<string | null>(null)

  useEffect(() => {
    const cargarRutaTextil = async () => {
      // ✅ NUEVA LÓGICA: Cargar siempre que haya tipo_prenda
      if (!formData.tipo_prenda) {
        setRutaTextil(null)
        return
      }
      
      // ✅ MOSTRAR SIEMPRE para estilos nuevos, independiente de WIPs seleccionadas
      if (!esEstiloNuevo) {
        setRutaTextil(null)
        return
      }
      
      setCargandoRuta(true)
      setErrorRuta(null)
      
      try {
        console.log(`🔍 Cargando ruta textil para: ${formData.tipo_prenda} (${formData.version_calculo})`)
        
        const response = await fetch(
          `${API_BASE_URL}/ruta-textil-recomendada/${encodeURIComponent(formData.tipo_prenda)}?version_calculo=${formData.version_calculo}`,
          {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            }
          }
        )
        
        if (response.ok) {
          const data = await response.json()
          console.log(`✅ Ruta textil cargada:`, data)
          
          // ✅ VALIDAR QUE TENGA WIPS_RECOMENDADAS
          if (data && Array.isArray(data.wips_recomendadas) && data.wips_recomendadas.length > 0) {
            setRutaTextil(data)
          } else {
            console.log(`⚠️ Ruta textil sin WIPs recomendadas:`, data)
            setRutaTextil({
              ...data,
              wips_recomendadas: [],
              mensaje: 'Sin WIPs específicas encontradas para este tipo de prenda'
            })
          }
        } else {
          const errorData = await response.text()
          console.error(`❌ Error cargando ruta textil:`, response.status, errorData)
          setErrorRuta(`Error ${response.status}: ${errorData}`)
        }
      } catch (error) {
        console.error('❌ Error conectando ruta textil:', error)
        setErrorRuta('Error de conexión al cargar ruta textil')
      } finally {
        setCargandoRuta(false)
      }
    }

    cargarRutaTextil()
  }, [
    formData.tipo_prenda, 
    formData.version_calculo, 
    esEstiloNuevo
  ]) // ✅ DEPENDENCIAS CORRECTAS (sin wipsTextiles/wipsManufactura)

  // ✅ CONDICIONES DE MOSTRAR CORREGIDAS
  if (!formData.tipo_prenda) {
    return (
      <div className="mb-6 p-4 rounded-xl border-2" style={{ backgroundColor: "#fff4e1", borderColor: "#ffbba8" }}>
        <div className="text-sm text-gray-600">
          💡 Selecciona un tipo de prenda para ver recomendaciones de WIPs
        </div>
      </div>
    )
  }
  
  if (!esEstiloNuevo) {
    return null // Solo mostrar para estilos nuevos
  }

  return (
    <div className="mb-6 p-4 rounded-xl border-2" style={{ backgroundColor: "#fff4e1", borderColor: "#ffbba8" }}>
      <h4 className="font-bold mb-3 flex items-center gap-2" style={{ color: "#821417" }}>
        🧵 Ruta Textil Recomendada para {formData.tipo_prenda}
        <span className="text-sm bg-orange-100 px-2 py-1 rounded text-orange-800">
          Estilo Nuevo
        </span>
        <span className="text-xs bg-blue-100 px-2 py-1 rounded text-blue-800">
          {formData.version_calculo}
        </span>
      </h4>
      
      {cargandoRuta ? (
        <div className="flex items-center gap-2" style={{ color: "#bd4c42" }}>
          <RefreshCw className="h-4 w-4 animate-spin" />
          <span>Cargando ruta recomendada...</span>
        </div>
      ) : errorRuta ? (
        <div className="text-sm p-3 rounded bg-red-50 border border-red-200">
          <div className="text-red-700 font-semibold mb-1">❌ Error cargando ruta:</div>
          <div className="text-red-600 text-xs">{errorRuta}</div>
        </div>
      ) : rutaTextil ? (
        <div className="space-y-3">
          {/* ✅ MOSTRAR WIPS SI EXISTEN */}
          {rutaTextil.wips_recomendadas && rutaTextil.wips_recomendadas.length > 0 ? (
            <>
              <div className="grid grid-cols-4 gap-2 text-sm">
                {rutaTextil.wips_recomendadas.slice(0, 12).map((wip: any, idx: number) => (
                  <div 
                    key={idx} 
                    className="p-2 rounded-lg text-center hover:shadow-md transition-all cursor-pointer" 
                    style={{ backgroundColor: "#ffbba8" }}
                    title={`Frecuencia: ${wip.frecuencia_uso || 0} usos | Recomendación: ${wip.recomendacion || 'Media'}`}
                  >
                    <div className="font-semibold" style={{ color: "#821417" }}>
                      WIP {wip.wip_id}
                    </div>
                    <div className="text-xs" style={{ color: "#bd4c42" }}>
                      {wip.nombre || `WIP ${wip.wip_id}`}
                    </div>
                    <div className="text-xs font-bold">
                      ${wip.costo_promedio?.toFixed(2) || '0.00'}
                    </div>
                    <div className="text-xs text-gray-600">
                      {wip.frecuencia_uso || 0} usos
                    </div>
                    {/* ✅ INDICADOR DE RECOMENDACIÓN */}
                    <div className={`text-xs px-1 py-0.5 rounded mt-1 ${
                      wip.recomendacion === 'Alta' ? 'bg-green-100 text-green-700' :
                      wip.recomendacion === 'Media' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {wip.recomendacion || 'Media'}
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="text-xs text-gray-600 bg-white p-2 rounded">
                💡 <strong>Tip:</strong> Estas WIPs son las más utilizadas para {formData.tipo_prenda}. 
                Puedes seleccionar las que mejor se adapten a tu estilo específico.
              </div>
            </>
          ) : (
            <div className="text-sm p-3 rounded bg-yellow-50 border border-yellow-200">
              <div className="text-yellow-700 font-semibold mb-1">⚠️ Sin WIPs específicas</div>
              <div className="text-yellow-600 text-xs">
                No se encontraron WIPs frecuentemente utilizadas para {formData.tipo_prenda} en versión {formData.version_calculo}.
                Puedes seleccionar WIPs manualmente en la sección de configuración.
              </div>
            </div>
          )}
          
          {/* ✅ INFORMACIÓN TÉCNICA */}
          <div className="mt-3 text-xs text-gray-500 border-t pt-2 flex justify-between">
            <span>
              📊 Método: {rutaTextil.metodo || 'frecuencia_uso'} | 
              📈 Total encontradas: {rutaTextil.total_recomendadas || 0}
            </span>
            <span>🕒 {new Date().toLocaleTimeString()}</span>
          </div>
        </div>
      ) : (
        <div className="text-sm text-gray-600">
          Cargando información de ruta textil...
        </div>
      )}
    </div>
  )
})

  // ✅ COMPONENTE: OPs reales (mantenido igual pero mejorado)
  // ✅ CORRECCIÓN: ComponenteOpsReales con validaciones completas
// Reemplazar el componente ComponenteOpsReales

const ComponenteOpsReales = React.memo(() => {
  if (!cotizacionActual) return null

  const { info_comercial } = cotizacionActual

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
      <div className="p-6 border-b border-gray-100" style={{ backgroundColor: "#821417" }}>
        <h2 className="text-xl font-bold flex items-center gap-3 text-white">
          <FileText className="h-6 w-6" />
          OPs de Referencia Utilizadas para el Cálculo
        </h2>
        <p className="text-white/80 mt-1">
          {opsReales ? (
            <>
              Base histórica: {opsReales.total_ops_encontradas} órdenes | 
              Método: {opsReales.ops_data.metodo_utilizado} | 
              Versión: {opsReales.ops_data.parametros_busqueda.version_calculo}
              {opsReales.ops_data.rangos_aplicados && (
                <span className="ml-2 px-2 py-1 bg-yellow-500/30 rounded text-xs">
                  ✓ Rangos de seguridad aplicados
                </span>
              )}
            </>
          ) : (
            <>Base histórica: {info_comercial?.ops_utilizadas || 0} órdenes procesadas | 
            Volumen: {info_comercial?.historico_volumen?.volumen_total_6m?.toLocaleString() || 0} prendas</>
          )}
        </p>
      </div>

      <div className="p-6">
        {cargandoOps ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-8 w-8 animate-spin mr-3" style={{ color: "#bd4c42" }} />
            <span className="text-lg" style={{ color: "#821417" }}>
              Cargando OPs de referencia...
            </span>
          </div>
        ) : errorOps ? (
          <div className="text-center py-8">
            <AlertTriangle className="h-12 w-12 mx-auto mb-4" style={{ color: "#fa8072" }} />
            <p className="text-lg font-semibold mb-2" style={{ color: "#821417" }}>
              Error al cargar OPs
            </p>
            <p className="text-sm text-gray-600">{errorOps}</p>
            <button
              onClick={() => cargarOpsReales(cotizacionActual)}
              className="mt-4 px-4 py-2 rounded-lg text-white"
              style={{ backgroundColor: "#bd4c42" }}
            >
              Reintentar
            </button>
          </div>
        ) : opsReales && opsReales.ops_data.ops_utilizadas.length > 0 ? (
          <>
            <div className="grid grid-cols-5 gap-4">
              {opsReales.ops_data.ops_utilizadas.slice(0, 10).map((op, idx) => {
                // ✅ VALIDACIONES DEFENSIVAS COMPLETAS
                const costoTotalUnitario = op.costo_total_unitario || 0
                const costoPromedio = opsReales.ops_data.estadisticas?.costo_promedio || 1
                const costoPorcentual = costoPromedio > 0 
                  ? (costoTotalUnitario / costoPromedio) * 100 
                  : 100
                
                // ✅ VALIDAR SI TIENE AJUSTES
                const tieneAjustes = op.costos_componentes && Object.values(op.costos_componentes).some(c => c !== (op.costos_componentes as any).original)
                
                return (
                  <div
                    key={idx}
                    className="relative p-4 rounded-xl border-2 border-transparent hover:shadow-lg transition-all duration-300 group"
                    style={{ backgroundColor: "#fff4e1" }}
                  >
                    <div className="mb-3">
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            backgroundColor: costoTotalUnitario > costoPromedio ? "#fa8072" : "#bd4c42",
                            width: `${Math.min(100, Math.max(10, costoPorcentual))}%`
                          }}
                        />
                      </div>
                    </div>

                    <div className="text-center">
                      <div className="font-bold text-sm mb-1" style={{ color: "#821417" }}>
                        {op.cod_ordpro}
                        {tieneAjustes && (
                          <span className="ml-1 text-xs text-orange-600">*</span>
                        )}
                      </div>
                      <div className="text-lg font-bold" style={{ color: "#bd4c42" }}>
                        ${costoTotalUnitario.toFixed(2)}
                      </div>
                     <div className="text-xs text-gray-600 mt-1">
                      {op.costo_total_original ? (
                        <>
                          Original: <span className="font-semibold">${op.costo_total_original.toFixed(2)}</span>
                          {op.fue_ajustado && (
                            <span className="text-orange-600 ml-1 font-semibold">→ Ajustado</span>
                          )}
                        </>
                      ) : (
                        <span className="text-gray-500">Sin datos originales</span>
                      )}
                    </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {(op.prendas_requeridas || 0).toLocaleString()} prendas
                      </div>
                      {op.fecha_facturacion && (
                        <div className="text-xs text-gray-500">
                          {new Date(op.fecha_facturacion).toLocaleDateString()}
                        </div>
                      )}
                    </div>

                    {/* ✅ TOOLTIP MEJORADO CON DESGLOSE */}
                    <div className="absolute -top-20 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs px-3 py-2 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none z-10 min-w-max">
                      <div className="font-semibold">{op.cod_ordpro}</div>
                      <div>Cliente: {op.cliente}</div>
                      <div>Estilo: {op.estilo_propio}</div>
                      <div>Esfuerzo: {op.esfuerzo_total || 6}/10</div>
                      <div>Precio facturado: ${(op.precio_unitario || 0).toFixed(2)}</div>
                      {op.costos_componentes && (
                        <div className="border-t border-gray-600 mt-1 pt-1">
                          <div>Textil: ${(op.costos_componentes.textil || 0).toFixed(2)}</div>
                          <div>Manufactura: ${(op.costos_componentes.manufactura || 0).toFixed(2)}</div>
                          <div>Total: ${costoTotalUnitario.toFixed(2)}</div>
                        </div>
                      )}
                      {tieneAjustes && (
                        <div className="text-orange-300 text-xs mt-1">* Ajustado por rangos</div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>

            {/* ✅ ESTADÍSTICAS CON VALIDACIONES */}
            {opsReales.ops_data.estadisticas && (
              <div className="mt-6 grid grid-cols-4 gap-4">
                <div className="text-center p-3 rounded-xl" style={{ backgroundColor: "#ffbba8" }}>
                  <div className="text-sm font-semibold" style={{ color: "#821417" }}>
                    Costo Promedio
                  </div>
                  <div className="text-lg font-bold" style={{ color: "#bd4c42" }}>
                    ${(opsReales.ops_data.estadisticas.costo_promedio || 0).toFixed(2)}
                  </div>
                </div>

                <div className="text-center p-3 rounded-xl" style={{ backgroundColor: "#ffbba8" }}>
                  <div className="text-sm font-semibold" style={{ color: "#821417" }}>
                    Rango Costos
                  </div>
                  <div className="text-sm font-bold" style={{ color: "#bd4c42" }}>
                    ${(opsReales.ops_data.estadisticas.costo_min || 0).toFixed(2)} - ${(opsReales.ops_data.estadisticas.costo_max || 0).toFixed(2)}
                  </div>
                </div>

                <div className="text-center p-3 rounded-xl" style={{ backgroundColor: "#ffbba8" }}>
                  <div className="text-sm font-semibold" style={{ color: "#821417" }}>
                    Esfuerzo Promedio
                  </div>
                  <div className="text-lg font-bold" style={{ color: "#bd4c42" }}>
                    {(opsReales.ops_data.estadisticas.esfuerzo_promedio || 6).toFixed(1)}/10
                  </div>
                </div>

                <div className="text-center p-3 rounded-xl" style={{ backgroundColor: "#ffbba8" }}>
                  <div className="text-sm font-semibold" style={{ color: "#821417" }}>
                    Total OPs
                  </div>
                  <div className="text-lg font-bold text-green-600">
                    {opsReales.ops_data.estadisticas.total_ops || 0}
                  </div>
                </div>
              </div>
            )}

            <div className="mt-4 p-3 rounded-lg text-center text-sm" style={{ backgroundColor: "#f0f0f0", color: "#666" }}>
              <strong>Método:</strong> {opsReales.ops_data.metodo_utilizado} | 
              <strong> Versión:</strong> {opsReales.ops_data.parametros_busqueda.version_calculo}
              {opsReales.ops_data.estadisticas?.rango_fechas && (
                <> | <strong>Período:</strong> {new Date(opsReales.ops_data.estadisticas.rango_fechas.desde).toLocaleDateString()} - {new Date(opsReales.ops_data.estadisticas.rango_fechas.hasta).toLocaleDateString()}</>
              )}
              {opsReales.ops_data.rangos_aplicados && (
                <> | <span className="text-orange-600 font-semibold">✓ Rangos de seguridad aplicados</span></>
              )}
            </div>
          </>
        ) : (
          <div className="text-center py-8">
            <Package className="h-12 w-12 mx-auto mb-4" style={{ color: "#bd4c42" }} />
            <p className="text-lg font-semibold mb-2" style={{ color: "#821417" }}>
              Sin OPs de referencia
            </p>
            <p className="text-sm text-gray-600">
              No se encontraron órdenes de producción para los criterios especificados
            </p>
          </div>
        )}
      </div>
    </div>
  )
})

  // ========================================
  // 🎨 FORMULARIO PRINCIPAL CORREGIDO
  // ========================================

  const FormularioPrincipal = () => (
    <div className="space-y-8">
      {/* Header */}
      <div
        className="relative overflow-hidden rounded-2xl"
        style={{ background: "linear-gradient(135deg, #821417 0%, #bd4c42 100%)" }}
      >
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative p-8 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-3 mb-2">
                <div className="p-2 bg-white/20 rounded-xl backdrop-blur-sm">
                  <DollarSign className="h-8 w-8" />
                </div>
                Sistema Cotizador TDV
              </h1>
              <p className="text-white/90 text-lg">Metodología WIP - Cotización Inteligente</p>
              <p className="text-white/70 text-sm mt-1">
                Basado en costos históricos y configuración modular • 
                Versión activa: <strong>{formData.version_calculo}</strong>
              </p>
            </div>
            <div className="text-right">
              <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4">
                <div className="text-2xl font-bold">TDV</div>
                <div className="text-white/80 text-sm">Sistema v2.0</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Switch de versión */}
      {SwitchVersionCalculo}

      {/* Información básica */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100" style={{ backgroundColor: "#821417" }}>
          <h2 className="text-xl font-bold flex items-center gap-3 text-white">
            <Package className="h-6 w-6" />
            Información del Producto
          </h2>
          <p className="text-white/80 mt-1">
            Datos básicos para la cotización • Versión: {formData.version_calculo}
          </p>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-2 gap-6">
            {/* Cliente/Marca */}
            <div className="space-y-2">
              <label className="block text-sm font-semibold" style={{ color: "#821417" }}>
                Cliente/Marca
              </label>
              <select
                value={formData.cliente_marca}
                onChange={(e) => manejarCambioFormulario("cliente_marca", e.target.value)}
                className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-opacity-50 transition-colors"
              >
                {clientesDisponibles.map((cliente) => (
                  <option key={cliente} value={cliente}>
                    {cliente}
                  </option>
                ))}
              </select>
            </div>

            {/* Temporada */}
            <div className="space-y-2">
              <label className="block text-sm font-semibold" style={{ color: "#821417" }}>
                Temporada
              </label>
              <input
                type="text"
                value={formData.temporada}
                onChange={(e) => manejarCambioFormulario("temporada", e.target.value)}
                className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-opacity-50 transition-colors"
                placeholder="ej: Verano 2025, Otoño 2024"
              />
            </div>

            {/* Código de estilo */}
            {CampoCodigoEstilo}

            {/* Categoría de lote */}
            <div className="space-y-2">
              <label className="block text-sm font-semibold" style={{ color: "#821417" }}>
                Categoría de Lote
              </label>
              <select
                value={formData.categoria_lote}
                onChange={(e) => manejarCambioFormulario("categoria_lote", e.target.value)}
                className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-opacity-50 transition-colors"
              >
                {Object.entries(CATEGORIAS_LOTE).map(([categoria, info]) => (
                  <option key={categoria} value={categoria}>
                    {categoria} ({info.rango} prendas)
                  </option>
                ))}
              </select>
            </div>

            {/* Familia de producto */}
            <div className="space-y-2">
              <label className="block text-sm font-semibold" style={{ color: "#821417" }}>
                Familia de Producto
              </label>
              <div className="relative">
                <select
                  value={formData.familia_producto}
                  onChange={(e) => manejarCambioFormulario("familia_producto", e.target.value)}
                  className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-opacity-50 transition-colors appearance-none"
                  disabled={cargandoFamilias}
                >
                  <option value="">
                    {cargandoFamilias 
                      ? "Cargando familias..." 
                      : familiasDisponibles.length === 0 
                      ? "⚠️ Error cargando familias - Verifique backend" 
                      : "Seleccionar familia"}
                  </option>
                  {familiasDisponibles.map((familia) => (
                    <option key={familia} value={familia}>
                      {familia}
                    </option>
                  ))}
                </select>
                {cargandoFamilias && (
                  <div className="absolute right-3 top-4">
                    <RefreshCw className="h-5 w-5 animate-spin" style={{ color: "#bd4c42" }} />
                  </div>
                )}
              </div>
            </div>

            {/* Tipo de prenda */}
            <div className="space-y-2">
              <label className="block text-sm font-semibold" style={{ color: "#821417" }}>
                Tipo de Prenda
              </label>
              <div className="relative">
                <select
                  value={formData.tipo_prenda}
                  onChange={(e) => manejarCambioFormulario("tipo_prenda", e.target.value)}
                  className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-opacity-50 transition-colors appearance-none"
                  disabled={cargandoTipos || !formData.familia_producto}
                >
                  <option value="">
                    {!formData.familia_producto 
                      ? "Primero selecciona familia" 
                      : cargandoTipos 
                      ? "Cargando tipos..." 
                      : "Seleccionar tipo"}
                  </option>
                  {tiposDisponibles.map((tipo) => (
                    <option key={tipo} value={tipo}>
                      {tipo}
                    </option>
                  ))}
                </select>
                {cargandoTipos && (
                  <div className="absolute right-3 top-4">
                    <RefreshCw className="h-5 w-5 animate-spin" style={{ color: "#bd4c42" }} />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Configurador WIPs */}
      {esEstiloNuevo && formData.codigo_estilo && (
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="p-6 border-b border-gray-100" style={{ backgroundColor: "#fff4e1" }}>
            <h2 className="text-xl font-bold flex items-center gap-3" style={{ color: "#821417" }}>
              <Settings className="h-6 w-6" />
              Configurador de WIPs - Estilo Nuevo
            </h2>
            <p className="text-gray-600 mt-1">
              Código: <strong>{formData.codigo_estilo}</strong> • 
              Tipo: <strong>{formData.tipo_prenda || 'Selecciona tipo'}</strong> • 
              Versión: <strong>{formData.version_calculo}</strong>
            </p>
            
            <RutaTextilRecomendada />
          </div>

          <div className="p-6 space-y-8">
            {/* WIPs Textiles */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold flex items-center gap-3" style={{ color: "#bd4c42" }}>
                  🧵 WIPs Textiles
                  <span
                    className="text-sm font-normal px-3 py-1 rounded-full"
                    style={{ backgroundColor: "#ffbba8", color: "#821417" }}
                  >
                    {wipsTextiles.length} seleccionadas
                  </span>
                </h3>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {wipsDisponibles.wips_textiles.map((wip) => {
                  const seleccionada = wipsTextiles.find(w => w.wip_id === wip.wip_id)
                  return (
                    <div
                      key={wip.wip_id}
                      className={`p-4 rounded-xl border-2 transition-all duration-300 ${
                        seleccionada ? "border-transparent shadow-lg" : "border-gray-200 hover:border-gray-300"
                      }`}
                      style={{ backgroundColor: seleccionada ? "#ffbba8" : "#fff4e1" }}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            checked={!!seleccionada}
                            onChange={() => toggleWipTextil(wip)}
                            className="h-5 w-5 rounded"
                            style={{ accentColor: "#821417" }}
                          />
                          <div>
                            <div className="font-semibold" style={{ color: "#821417" }}>
                              {wip.nombre}
                            </div>
                            <div className="text-sm" style={{ color: "#bd4c42" }}>
                              ${wip.costo_actual?.toFixed(2)}/prenda
                            </div>
                          </div>
                        </div>
                      </div>

                      {seleccionada && (
                        <div className="space-y-2 pt-3 border-t border-white/50">
                          <label className="text-xs font-semibold" style={{ color: "#821417" }}>
                            Factor de Ajuste:
                          </label>
                          <input
                            type="number"
                            value={seleccionada.factor_ajuste}
                            onChange={(e) =>
                              actualizarFactorWip(setWipsTextiles, wip.wip_id, e.target.value)
                            }
                            min="0.5"
                            max="2.0"
                            step="0.05"
                            className="w-full p-2 text-sm border border-gray-300 rounded-lg"
                          />
                          <div className="text-xs font-semibold" style={{ color: "#bd4c42" }}>
                            Costo final: ${(wip.costo_actual * seleccionada.factor_ajuste).toFixed(2)}
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            {/* WIPs Manufactura */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold flex items-center gap-3" style={{ color: "#bd4c42" }}>
                  🏭 WIPs Manufactura
                  <span
                    className="text-sm font-normal px-3 py-1 rounded-full"
                    style={{ backgroundColor: "#ffbba8", color: "#821417" }}
                  >
                    {wipsManufactura.length} seleccionadas
                  </span>
                </h3>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {wipsDisponibles.wips_manufactura.map((wip) => {
                  const seleccionada = wipsManufactura.find(w => w.wip_id === wip.wip_id)
                  return (
                    <div
                      key={wip.wip_id}
                      className={`p-4 rounded-xl border-2 transition-all duration-300 ${
                        seleccionada ? "border-transparent shadow-lg" : "border-gray-200 hover:border-gray-300"
                      }`}
                      style={{ backgroundColor: seleccionada ? "#ffbba8" : "#fff4e1" }}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            checked={!!seleccionada}
                            onChange={() => toggleWipManufactura(wip)}
                            className="h-5 w-5 rounded"
                            style={{ accentColor: "#821417" }}
                          />
                          <div>
                            <div className="font-semibold" style={{ color: "#821417" }}>
                              {wip.nombre}
                            </div>
                            <div className="text-sm" style={{ color: "#bd4c42" }}>
                              ${wip.costo_actual?.toFixed(2)}/prenda
                            </div>
                          </div>
                        </div>
                      </div>

                      {seleccionada && (
                        <div className="space-y-2 pt-3 border-t border-white/50">
                          <label className="text-xs font-semibold" style={{ color: "#821417" }}>
                            Factor de Ajuste:
                          </label>
                          <input
                            type="number"
                            value={seleccionada.factor_ajuste}
                            onChange={(e) =>
                              actualizarFactorWip(setWipsManufactura, wip.wip_id, e.target.value)
                            }
                            min="0.5"
                            max="2.0"
                            step="0.05"
                            className="w-full p-2 text-sm border border-gray-300 rounded-lg"
                          />
                          <div className="text-xs font-semibold" style={{ color: "#bd4c42" }}>
                            Costo final: ${(wip.costo_actual * seleccionada.factor_ajuste).toFixed(2)}
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Botón de cotización */}
      <div className="flex justify-center">
        <div className="flex flex-col items-center space-y-4">
          {validarFormulario().length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 max-w-md">
              <h4 className="font-semibold text-red-800 mb-2">Campos requeridos:</h4>
              <ul className="text-sm text-red-600 space-y-1">
                {validarFormulario().map((error, idx) => (
                  <li key={idx} className="flex items-center gap-2">
                    <div className="w-1 h-1 bg-red-400 rounded-full"></div>
                    {error}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          <button
            onClick={procesarCotizacion}
            disabled={cargando || validarFormulario().length > 0}
            className="group relative px-12 py-4 font-bold text-white rounded-2xl shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105"
            style={{ background: "linear-gradient(135deg, #821417 0%, #bd4c42 100%)" }}
          >
            {cargando ? (
              <div className="flex items-center gap-3">
                <RefreshCw className="h-6 w-6 animate-spin" />
                <span className="text-lg">Procesando Cotización...</span>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <DollarSign className="h-6 w-6" />
                <span className="text-lg">Generar Cotización</span>
              </div>
            )}
          </button>
        </div>
      </div>
    </div>
  )

  // ========================================
  // 🎨 PANTALLA RESULTADOS
  // ========================================

  // ✅ PANTALLA RESULTADOS COMPLETA - CON TODAS LAS CORRECCIONES
  const PantallaResultados = () => {
    if (!cotizacionActual) return null

    const { info_comercial } = cotizacionActual

    // ✅ NUEVO: Agrupar componentes por tipo, no mostrar WIPs individuales
    const componentesAgrupados = React.useMemo(() => {
        if (!cotizacionActual) return []
        
        // ✅ USAR DIRECTAMENTE LOS TOTALES AJUSTADOS DE LA RESPUESTA
        return [
          {
            nombre: 'Costo Textil',
            costo_unitario: cotizacionActual.costo_textil,
            fuente: 'wip',
            badge: esEstiloNuevo ? `${(wipsTextiles?.length || 0)} WIPs` : 'histórico',
            es_agrupado: false
          },
          {
            nombre: 'Costo Manufactura',
            costo_unitario: cotizacionActual.costo_manufactura,
            fuente: 'wip', 
            badge: esEstiloNuevo ? `${(wipsManufactura?.length || 0)} WIPs` : 'histórico',
            es_agrupado: false
          },
          {
            nombre: 'Costo Materia Prima',
            costo_unitario: cotizacionActual.costo_materia_prima,
            fuente: 'ultimo_costo',
            badge: 'último costo',
            es_agrupado: false
          },
          {
            nombre: 'Costo Avíos',
            costo_unitario: cotizacionActual.costo_avios,
            fuente: 'ultimo_costo',
            badge: 'último costo', 
            es_agrupado: false
          },
          {
            nombre: 'Costo Indirecto Fijo',
            costo_unitario: cotizacionActual.costo_indirecto_fijo,
            fuente: 'formula',
            badge: 'fórmula',
            es_agrupado: false
          },
          {
            nombre: 'Gasto Administración',
            costo_unitario: cotizacionActual.gasto_administracion,
            fuente: 'formula',
            badge: 'fórmula',
            es_agrupado: false
          },
          {
            nombre: 'Gasto Ventas',
            costo_unitario: cotizacionActual.gasto_ventas,
            fuente: 'formula',
            badge: 'fórmula',
            es_agrupado: false
          }
        ]
      }, [cotizacionActual, esEstiloNuevo, wipsTextiles?.length, wipsManufactura?.length])

    // ✅ COMPONENTE OPS REALES CORREGIDO
    const ComponenteOpsReales = React.memo(() => {
      return (
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="p-6 border-b border-gray-100" style={{ backgroundColor: "#821417" }}>
            <h2 className="text-xl font-bold flex items-center gap-3 text-white">
              <FileText className="h-6 w-6" />
              OPs de Referencia Utilizadas para el Cálculo
            </h2>
            <p className="text-white/80 mt-1">
              {opsReales ? (
                <>
                  Base histórica: {opsReales.total_ops_encontradas} órdenes | 
                  Método: {opsReales.ops_data.metodo_utilizado} | 
                  Versión: {opsReales.ops_data.parametros_busqueda.version_calculo}
                  {opsReales.ops_data.rangos_aplicados && (
                    <span className="ml-2 px-2 py-1 bg-yellow-500/30 rounded text-xs">
                      ✓ Rangos de seguridad aplicados
                    </span>
                  )}
                </>
              ) : (
                <>Base histórica: {info_comercial?.ops_utilizadas || 0} órdenes procesadas | 
                Volumen: {info_comercial?.historico_volumen?.volumen_total_6m?.toLocaleString() || 0} prendas</>
              )}
            </p>
          </div>

          <div className="p-6">
            {cargandoOps ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="h-8 w-8 animate-spin mr-3" style={{ color: "#bd4c42" }} />
                <span className="text-lg" style={{ color: "#821417" }}>
                  Cargando OPs de referencia...
                </span>
              </div>
            ) : errorOps ? (
              <div className="text-center py-8">
                <AlertTriangle className="h-12 w-12 mx-auto mb-4" style={{ color: "#fa8072" }} />
                <p className="text-lg font-semibold mb-2" style={{ color: "#821417" }}>
                  Error al cargar OPs
                </p>
                <p className="text-sm text-gray-600">{errorOps}</p>
                <button
                  onClick={() => cargarOpsReales(cotizacionActual)}
                  className="mt-4 px-4 py-2 rounded-lg text-white"
                  style={{ backgroundColor: "#bd4c42" }}
                >
                  Reintentar
                </button>
              </div>
            ) : opsReales && opsReales.ops_data.ops_utilizadas.length > 0 ? (
              <>
                <div className="grid grid-cols-5 gap-4">
                  {opsReales.ops_data.ops_utilizadas.slice(0, 10).map((op, idx) => {
                    // ✅ VALIDACIONES DEFENSIVAS COMPLETAS
                    const costoTotalUnitario = op.costo_total_unitario || 0
                    const costoPromedio = opsReales.ops_data.estadisticas?.costo_promedio || 1
                    const costoPorcentual = costoPromedio > 0 
                      ? (costoTotalUnitario / costoPromedio) * 100 
                      : 100
                    
                    // ✅ VALIDAR SI TIENE AJUSTES
                    const tieneAjustes = op.costos_componentes && Object.values(op.costos_componentes).some(c => c !== (op.costos_componentes as any).original)
                    
                    return (
                      <div
                        key={idx}
                        className="relative p-4 rounded-xl border-2 border-transparent hover:shadow-lg transition-all duration-300 group"
                        style={{ backgroundColor: "#fff4e1" }}
                      >
                        <div className="mb-3">
                          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-500"
                              style={{
                                backgroundColor: costoTotalUnitario > costoPromedio ? "#fa8072" : "#bd4c42",
                                width: `${Math.min(100, Math.max(10, costoPorcentual))}%`
                              }}
                            />
                          </div>
                        </div>

                        <div className="text-center">
                        <div className="font-bold text-sm mb-1" style={{ color: "#821417" }}>
                          {op.cod_ordpro}
                          {tieneAjustes && (
                            <span className="ml-1 text-xs text-orange-600">*</span>
                          )}
                        </div>
                        <div className="text-lg font-bold" style={{ color: "#bd4c42" }}>
                          ${costoTotalUnitario.toFixed(2)}
                        </div>
                        
                        {/* ✅ CÓDIGO CORREGIDO - Mostrar precio original en lugar de porcentaje */}
                        <div className="text-xs text-gray-600 mt-1">
                          {op.costo_total_original ? (
                            <>
                              Original: <span className="font-semibold">${op.costo_total_original.toFixed(2)}</span>
                              {op.fue_ajustado && (
                                <span className="text-orange-600 ml-1 font-semibold">→ Ajustado</span>
                              )}
                            </>
                          ) : (
                            <span className="text-gray-500">Sin datos originales</span>
                          )}
                        </div>
                        
                        <div className="text-xs text-gray-500 mt-1">
                          {(op.prendas_requeridas || 0).toLocaleString()} prendas
                        </div>
                        {op.fecha_facturacion && (
                          <div className="text-xs text-gray-500">
                            {new Date(op.fecha_facturacion).toLocaleDateString()}
                          </div>
                        )}
                      </div>

                        {/* ✅ TOOLTIP MEJORADO CON DESGLOSE */}
                        <div className="absolute -top-20 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs px-3 py-2 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none z-10 min-w-max">
                          <div className="font-semibold">{op.cod_ordpro}</div>
                          <div>Cliente: {op.cliente}</div>
                          <div>Estilo: {op.estilo_propio}</div>
                          <div>Esfuerzo: {op.esfuerzo_total || 6}/10</div>
                          <div>Precio facturado: ${(op.precio_unitario || 0).toFixed(2)}</div>
                          {op.costos_componentes && (
                            <div className="border-t border-gray-600 mt-1 pt-1">
                              <div>Textil: ${(op.costos_componentes.textil || 0).toFixed(2)}</div>
                              <div>Manufactura: ${(op.costos_componentes.manufactura || 0).toFixed(2)}</div>
                              <div>Total: ${costoTotalUnitario.toFixed(2)}</div>
                            </div>
                          )}
                          {tieneAjustes && (
                            <div className="text-orange-300 text-xs mt-1">* Ajustado por rangos</div>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>

                {/* ✅ ESTADÍSTICAS CON VALIDACIONES */}
                {opsReales.ops_data.estadisticas && (
                  <div className="mt-6 grid grid-cols-4 gap-4">
                    <div className="text-center p-3 rounded-xl" style={{ backgroundColor: "#ffbba8" }}>
                      <div className="text-sm font-semibold" style={{ color: "#821417" }}>
                        Costo Promedio
                      </div>
                      <div className="text-lg font-bold" style={{ color: "#bd4c42" }}>
                        ${(opsReales.ops_data.estadisticas.costo_promedio || 0).toFixed(2)}
                      </div>
                    </div>

                    <div className="text-center p-3 rounded-xl" style={{ backgroundColor: "#ffbba8" }}>
                      <div className="text-sm font-semibold" style={{ color: "#821417" }}>
                        Rango Costos
                      </div>
                      <div className="text-sm font-bold" style={{ color: "#bd4c42" }}>
                        ${(opsReales.ops_data.estadisticas.costo_min || 0).toFixed(2)} - ${(opsReales.ops_data.estadisticas.costo_max || 0).toFixed(2)}
                      </div>
                    </div>

                    <div className="text-center p-3 rounded-xl" style={{ backgroundColor: "#ffbba8" }}>
                      <div className="text-sm font-semibold" style={{ color: "#821417" }}>
                        Esfuerzo Promedio
                      </div>
                      <div className="text-lg font-bold" style={{ color: "#bd4c42" }}>
                        {(opsReales.ops_data.estadisticas.esfuerzo_promedio || 6).toFixed(1)}/10
                      </div>
                    </div>

                    <div className="text-center p-3 rounded-xl" style={{ backgroundColor: "#ffbba8" }}>
                      <div className="text-sm font-semibold" style={{ color: "#821417" }}>
                        Total OPs
                      </div>
                      <div className="text-lg font-bold text-green-600">
                        {opsReales.ops_data.estadisticas.total_ops || 0}
                      </div>
                    </div>
                  </div>
                )}

                <div className="mt-4 p-3 rounded-lg text-center text-sm" style={{ backgroundColor: "#f0f0f0", color: "#666" }}>
                  <strong>Método:</strong> {opsReales.ops_data.metodo_utilizado} | 
                  <strong> Versión:</strong> {opsReales.ops_data.parametros_busqueda.version_calculo}
                  {opsReales.ops_data.estadisticas?.rango_fechas && (
                    <> | <strong>Período:</strong> {new Date(opsReales.ops_data.estadisticas.rango_fechas.desde).toLocaleDateString()} - {new Date(opsReales.ops_data.estadisticas.rango_fechas.hasta).toLocaleDateString()}</>
                  )}
                  {opsReales.ops_data.rangos_aplicados && (
                    <> | <span className="text-orange-600 font-semibold">✓ Rangos de seguridad aplicados</span></>
                  )}
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <Package className="h-12 w-12 mx-auto mb-4" style={{ color: "#bd4c42" }} />
                <p className="text-lg font-semibold mb-2" style={{ color: "#821417" }}>
                  Sin OPs de referencia
                </p>
                <p className="text-sm text-gray-600">
                  No se encontraron órdenes de producción para los criterios especificados
                </p>
              </div>
            )}
          </div>
        </div>
      )
    })

    return (
      <div className="space-y-8">
        {/* Header con resultado */}
        <div
          className="relative overflow-hidden rounded-2xl"
          style={{ background: "linear-gradient(135deg, #821417 0%, #bd4c42 100%)" }}
        >
          <div className="absolute inset-0 bg-black/10"></div>
          <div className="relative p-8 text-white">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold mb-2">Cotización Generada</h1>
                <p className="text-white/90 text-lg">ID: {cotizacionActual.id_cotizacion}</p>
                <p className="text-white/70 text-sm">
                  Fecha: {new Date(cotizacionActual.fecha_cotizacion).toLocaleString()}
                </p>
                <div className="mt-3 flex gap-3">
                  <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
                    {cotizacionActual.categoria_estilo}
                  </span>
                  <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
                    Esfuerzo: {cotizacionActual.categoria_esfuerzo}/10
                  </span>
                  <span className="px-3 py-1 bg-yellow-500/30 rounded-full text-sm font-semibold">
                    Versión: {cotizacionActual.version_calculo_usada || cotizacionActual.inputs.version_calculo}
                  </span>
                  {cotizacionActual.volumen_historico && (
                    <span className="px-3 py-1 bg-green-500/30 rounded-full text-sm">
                      Volumen: {cotizacionActual.volumen_historico.toLocaleString()}
                    </span>
                  )}
                </div>
              </div>
              <div className="text-right">
                <div className="bg-white/20 backdrop-blur-sm rounded-2xl p-6">
                  <div className="text-4xl font-bold mb-1">${(cotizacionActual.precio_final || 0).toFixed(2)}</div>
                  <div className="text-white/90 text-lg">por prenda</div>
                  <div className="text-sm text-white/80 mt-2 px-3 py-1 bg-white/20 rounded-full">
                    Margen: {(cotizacionActual.margen_aplicado || 0).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* OPs de referencia */}
        <ComponenteOpsReales />

        {/* ✅ DESGLOSE CORREGIDO */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="p-6 border-b border-gray-100" style={{ backgroundColor: "#821417" }}>
            <h2 className="text-xl font-bold flex items-center gap-3 text-white">
              <BarChart3 className="h-6 w-6" />
              Desglose Detallado de Costos
            </h2>
            <p className="text-white/80 mt-1">
              Análisis completo de componentes y factores de ajuste • 
              Versión: {cotizacionActual.version_calculo_usada || cotizacionActual.inputs.version_calculo}
            </p>
          </div>

          <div className="p-6">
            <div className="grid grid-cols-2 gap-8">
              {/* ✅ COMPONENTES AGRUPADOS CORRECTAMENTE */}
              <div>
                <h3 className="font-bold mb-4" style={{ color: "#bd4c42" }}>
                  Componentes de Costo
                </h3>
                <div className="space-y-3">
                  {componentesAgrupados.map((comp, idx) => (
                    <div key={idx}>
                      <div
                        className="flex justify-between items-center p-3 rounded-xl"
                        style={{ backgroundColor: "#fff4e1" }}
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold" style={{ color: "#821417" }}>
                              {comp.nombre}
                            </span>
                            <span
                              className={`px-2 py-1 rounded-full text-xs font-semibold text-white`}
                              style={{
                                backgroundColor:
                                  comp.fuente === "wip" ? "#bd4c42" : 
                                  comp.fuente === "historico" ? "#fa8072" : "#6b7280",
                              }}
                            >
                              {comp.fuente}
                            </span>
                            {comp.es_agrupado && (
                              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                                {comp.badge}
                              </span>
                            )}
                          </div>
                          
                          {/* Mostrar solo badge informativo, NO detalles individuales */}
                          <div className="text-xs text-gray-600 mt-1">
                            {comp.badge}
                          </div>
                        </div>
                        <span className="font-bold text-lg ml-4" style={{ color: "#821417" }}>
                          ${comp.costo_unitario.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  ))}

                  <div className="border-t-2 pt-3 mt-4" style={{ borderColor: "#ffbba8" }}>
                    <div
                      className="flex justify-between items-center font-bold text-lg p-3 rounded-xl"
                      style={{ backgroundColor: "#ffbba8", color: "#821417" }}
                    >
                      <span>Costo Base Total</span>
                      <span>${(cotizacionActual.costo_base_total || 0).toFixed(2)}</span>
                    </div>
                  </div>
                  
                  {/* ✅ NOTA SOBRE AJUSTES */}
                  {/* Si necesitas mostrar una nota sobre ajustes, deberás revisar la estructura de tus datos.
                      Por ahora, se elimina la referencia a 'detalles' para evitar el error. */}
                </div>
              </div>

              {/* Vector de ajuste */}
              <div>
                <h3 className="font-bold mb-4" style={{ color: "#bd4c42" }}>
                  Vector de Ajuste
                </h3>
                <div className="space-y-3">
                  <div
                    className="flex justify-between items-center p-3 rounded-xl"
                    style={{ backgroundColor: "#fff4e1" }}
                  >
                    <span className="font-semibold" style={{ color: "#821417" }}>
                      Factor Lote ({cotizacionActual.inputs.categoria_lote})
                    </span>
                    <span className="font-bold" style={{ color: "#bd4c42" }}>
                      {(cotizacionActual.factor_lote || 1).toFixed(2)}
                    </span>
                  </div>
                  <div
                    className="flex justify-between items-center p-3 rounded-xl"
                    style={{ backgroundColor: "#fff4e1" }}
                  >
                    <span className="font-semibold" style={{ color: "#821417" }}>
                      Factor Esfuerzo ({cotizacionActual.categoria_esfuerzo || 6}/10)
                    </span>
                    <span className="font-bold" style={{ color: "#bd4c42" }}>
                      {(cotizacionActual.factor_esfuerzo || 1).toFixed(2)}
                    </span>
                  </div>
                  <div
                    className="flex justify-between items-center p-3 rounded-xl"
                    style={{ backgroundColor: "#fff4e1" }}
                  >
                    <span className="font-semibold" style={{ color: "#821417" }}>
                      Factor Estilo ({cotizacionActual.categoria_estilo || "Nuevo"})
                    </span>
                    <span className="font-bold" style={{ color: "#bd4c42" }}>
                      {(cotizacionActual.factor_estilo || 1).toFixed(2)}
                    </span>
                  </div>
                  <div
                    className="flex justify-between items-center p-3 rounded-xl"
                    style={{ backgroundColor: "#fff4e1" }}
                  >
                    <span className="font-semibold" style={{ color: "#821417" }}>
                      Factor Marca ({cotizacionActual.inputs.cliente_marca})
                    </span>
                    <span className="font-bold" style={{ color: "#bd4c42" }}>
                      {(cotizacionActual.factor_marca || 1).toFixed(2)}
                    </span>
                  </div>

                  <div className="border-t-2 pt-3 mt-4" style={{ borderColor: "#ffbba8" }}>
                    <div
                      className="flex justify-between items-center font-bold text-lg p-3 rounded-xl"
                      style={{ backgroundColor: "#ffbba8", color: "#821417" }}
                    >
                      <span>Vector Total</span>
                      <span>{(cotizacionActual.vector_total || 1).toFixed(3)}</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl text-center" style={{ backgroundColor: "#fa8072" }}>
                    <div className="text-sm text-white/90 mb-1">Precio Final</div>
                    <div className="text-xl font-bold text-white">
                      ${(cotizacionActual.costo_base_total || 0).toFixed(2)} × (1 + 15% × {(cotizacionActual.vector_total || 1).toFixed(3)}) = 
                      ${(cotizacionActual.precio_final || 0).toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Botones de acción */}
        <div className="flex justify-center gap-4">
          <button
            onClick={() => setPestanaActiva("formulario")}
            className="px-8 py-3 font-semibold text-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
            style={{ backgroundColor: "#bd4c42" }}
          >
            Nueva Cotización
          </button>

          <button
            onClick={() => window.print()}
            className="px-8 py-3 font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 flex items-center gap-2"
            style={{ backgroundColor: "#fff4e1", color: "#821417" }}
          >
            <Printer className="h-5 w-5" />
            Imprimir
          </button>

          <button
            onClick={() => {
              const data = JSON.stringify(cotizacionActual, null, 2)
              const blob = new Blob([data], { type: "application/json" })
              const url = URL.createObjectURL(blob)
              const a = document.createElement("a")
              a.href = url
              a.download = `cotizacion_${cotizacionActual.id_cotizacion}.json`
              a.click()
            }}
            className="px-8 py-3 font-semibold text-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 flex items-center gap-2"
            style={{ backgroundColor: "#fa8072" }}
          >
            <Download className="h-5 w-5" />
            Descargar
          </button>
        </div>
      </div>
    )
  }

  // ========================================
  // 🎨 RENDER PRINCIPAL
  // ========================================

  return (
    <div className="min-h-screen p-6" style={{ backgroundColor: "#fff4e1" }}>
      <div className="max-w-7xl mx-auto">
        {/* Navegación */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 mb-8 overflow-hidden">
          <div className="flex">
            <button
              onClick={() => setPestanaActiva("formulario")}
              className={`px-8 py-4 font-bold transition-all duration-300 flex items-center gap-3 ${
                pestanaActiva === "formulario" ? "text-white shadow-lg" : "hover:shadow-md"
              }`}
              style={{
                backgroundColor: pestanaActiva === "formulario" ? "#821417" : "transparent",
                color: pestanaActiva === "formulario" ? "white" : "#bd4c42",
              }}
            >
              <FileText className="h-5 w-5" />
              Formulario de Cotización
            </button>

            <button
              onClick={() => setPestanaActiva("resultados")}
              disabled={!cotizacionActual}
              className={`px-8 py-4 font-bold transition-all duration-300 flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed ${
                pestanaActiva === "resultados" ? "text-white shadow-lg" : "hover:shadow-md"
              }`}
              style={{
                backgroundColor: pestanaActiva === "resultados" ? "#821417" : "transparent",
                color: pestanaActiva === "resultados" ? "white" : "#bd4c42",
              }}
            >
              <BarChart3 className="h-5 w-5" />
              Resultados
            </button>

            <div
              className="ml-auto px-8 py-4 text-sm font-semibold flex items-center gap-2"
              style={{ color: "#bd4c42" }}
            >
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: "#fa8072" }}></div>
              Sistema TDV - Metodología WIP-Based
              <span className="px-2 py-1 rounded bg-gray-100 text-xs font-bold uppercase">
                {formData.version_calculo}
              </span>
              
              {/* ✅ NUEVO: Debug en desarrollo */}
              {process.env.NODE_ENV === 'development' && (
                <button
                  onClick={() => {
                    console.group('🔍 Debug Estado Sistema')
                    console.log('📝 FormData:', formData)
                    console.log('🎨 EstiloNuevo:', esEstiloNuevo)
                    console.log('🔍 EstilosEncontrados:', estilosEncontrados.length)
                    console.log('⚙️ WIPs:', { textiles: wipsTextiles.length, manufactura: wipsManufactura.length })
                    console.log('📊 Datos:', { familias: familiasDisponibles.length, tipos: tiposDisponibles.length })
                    console.log('💰 Cotización:', !!cotizacionActual)
                    console.groupEnd()
                  }}
                  className="ml-2 text-xs bg-gray-100 px-2 py-1 rounded hover:bg-gray-200"
                  title="Debug estado sistema"
                >
                  🔍
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Contenido principal */}
        {pestanaActiva === "formulario" && <FormularioPrincipal />}
        {pestanaActiva === "resultados" && <PantallaResultados />}
      </div>
    </div>
  )
}

export default SistemaCotizadorTDV