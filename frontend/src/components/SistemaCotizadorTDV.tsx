"use client";

import React, {
  useState,
  useEffect,
  useCallback,
  useRef,
  useMemo,
} from "react";
import type { OpsSelectionTableRef } from "./OpsSelectionTable";
import { get, post } from "@/libs/api";
import {
  Settings,
  DollarSign,
  Package,
  AlertTriangle,
  BarChart3,
  FileText,
  Download,
  Printer,
  RefreshCw,
  Database,
} from "lucide-react";
import { OpsSelectionTable } from "./OpsSelectionTable";
import { WipDesgloseTable } from "./WipDesgloseTable";

// Constantes del sistema
const CATEGORIAS_LOTE = {
  "Micro Lote": { rango: "1-50" },
  "Lote Pequeño": { rango: "51-500" },
  "Lote Mediano": { rango: "501-1000" },
  "Lote Grande": { rango: "1001-4000" },
  "Lote Masivo": { rango: "4001+" },
};

// Componente puro para el input de código de estilo - evita re-renders innecesarios
interface InputCodigoEstiloProps {
  value: string;
  buscandoEstilo: boolean;
  onChange: (valor: string) => void;
  onBuscar: () => void;
}

const InputCodigoEstilo = React.memo(({ value, buscandoEstilo, onChange, onBuscar }: InputCodigoEstiloProps) => (
  <div className="relative">
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value.toUpperCase().trim())}
      className="w-full p-4 pr-12 border-2 border-gray-200 rounded-xl focus:border-red-500 focus:border-opacity-50 transition-colors"
      placeholder="ej: LAC001-V25, GRY2024-P01"
      autoComplete="off"
      spellCheck={false}
    />
    <button
      type="button"
      onClick={onBuscar}
      disabled={buscandoEstilo || value.length < 3}
      className="absolute right-2 top-3 p-1 rounded-lg hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      title={value.length < 3 ? "Ingresa al menos 3 caracteres" : "Buscar estilo"}
    >
      {buscandoEstilo ? (
        <RefreshCw className="h-5 w-5 text-red-500 animate-spin" />
      ) : (
        <svg className="h-5 w-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      )}
    </button>
  </div>
));

// Componente CampoCodigoEstilo completo como React.memo - evita que se remonte en cada keystroke
interface CampoCodigoEstiloProps {
  value: string;
  buscandoEstilo: boolean;
  estilosEncontrados: any[];
  esEstiloNuevo: boolean;
  infoAutoCompletado: any;
  onChange: (valor: string) => void;
  onBuscar: () => void;
  onSelectStyle: (estilo: any) => void;
}

const CampoCodigoEstiloComponent = React.memo(
  ({
    value,
    buscandoEstilo,
    estilosEncontrados,
    esEstiloNuevo,
    infoAutoCompletado,
    onChange,
    onBuscar,
    onSelectStyle,
  }: CampoCodigoEstiloProps) => (
    <div className="space-y-2">
      <label className="block text-sm font-semibold text-red-900">
        Código de estilo propio
      </label>
      <InputCodigoEstilo
        value={value}
        buscandoEstilo={buscandoEstilo}
        onChange={onChange}
        onBuscar={onBuscar}
      />

      {/* Información de auto-completado */}
      {infoAutoCompletado?.autocompletado_disponible && (
        <div className="mt-2 p-3 rounded-xl border-2 bg-green-100 border-green-400">
          <div className="text-sm font-semibold mb-2 text-green-700">
            ✅ Auto-completado aplicado:
          </div>
          <div className="text-xs text-green-700">
            📁 Familia:{" "}
            <strong>
              {infoAutoCompletado.campos_sugeridos?.familia_producto}
            </strong>{" "}
            | 🏷️ Tipo:{" "}
            <strong>{infoAutoCompletado.campos_sugeridos?.tipo_prenda}</strong> | 📊
            Categoría: <strong>{infoAutoCompletado.info_estilo?.categoria}</strong>
          </div>
        </div>
      )}

      {/* Estilos similares */}
      {estilosEncontrados.length > 0 && (
        <div className="mt-2 p-3 rounded-xl border-2 bg-orange-50 border-orange-400">
          <div className="text-sm font-semibold mb-2 text-red-900">
            Estilos similares encontrados:
          </div>
          {estilosEncontrados.map((estilo, idx) => (
            <button
              key={idx}
              onClick={() => onSelectStyle(estilo)}
              className="w-full text-left p-2 rounded-lg hover:shadow-md transition-all mb-2 bg-orange-200"
            >
              <div className="font-semibold text-sm text-red-900">
                {estilo.codigo}
              </div>
              <div className="text-xs text-red-500">
                {estilo.familia_producto} - {estilo.tipo_prenda} |{" "}
                {estilo.ops_encontradas} OPs | ${estilo.costo_promedio.toFixed(2)}
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Indicador de estado del estilo */}
      {value && !buscandoEstilo && (
        <div className="flex items-center gap-2">
          <div
            className={`text-xs px-2 py-1 rounded-full inline-block text-white ${
              esEstiloNuevo ? "bg-red-500" : "bg-red-600"
            }`}
          >
            {esEstiloNuevo ? "🆕 Estilo Nuevo" : "🔄 Estilo Recurrente"}
          </div>

          {infoAutoCompletado?.info_estilo?.volumen_total && (
            <div className="text-xs text-gray-600">
              📦 Volumen histórico:{" "}
              {infoAutoCompletado.info_estilo.volumen_total.toLocaleString()}{" "}
              prendas
            </div>
          )}
        </div>
      )}
    </div>
  )
);
CampoCodigoEstiloComponent.displayName = "CampoCodigoEstiloComponent";

// ========================================
// 📋 FORM INPUT COMPONENTS - Memoized para evitar re-renders innecesarios
// ========================================

// Cliente/Marca select input
interface ClienteSelectProps {
  value: string;
  clientesDisponibles: string[];
  onChange: (value: string) => void;
}

const ClienteSelect = React.memo(({ value, clientesDisponibles, onChange }: ClienteSelectProps) => (
  <div className="space-y-2">
    <label className="block text-sm font-semibold text-red-900">
      Cliente/Marca
    </label>
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-red-500 focus:border-opacity-50 transition-colors"
    >
      {clientesDisponibles.map((cliente) => (
        <option key={cliente} value={cliente}>
          {cliente}
        </option>
      ))}
    </select>
  </div>
));
ClienteSelect.displayName = "ClienteSelect";

// NOTA: TemporadaInput fue eliminado - temporada ya no se usa en la UI

// Categoría de Lote select
interface CategoriaLoteSelectProps {
  value: string;
  onChange: (value: string) => void;
}

const CategoriaLoteSelect = React.memo(({ value, onChange }: CategoriaLoteSelectProps) => (
  <div className="space-y-2">
    <label className="block text-sm font-semibold text-red-900">
      Categoría de Lote
    </label>
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-red-500 focus:border-opacity-50 transition-colors"
    >
      {Object.entries(CATEGORIAS_LOTE).map(([categoria, info]) => (
        <option key={categoria} value={categoria}>
          {categoria} ({info.rango} prendas)
        </option>
      ))}
    </select>
  </div>
));
CategoriaLoteSelect.displayName = "CategoriaLoteSelect";

// NOTA: FamiliaProductoSelect fue eliminado - familia_producto ya no se usa en la UI

// Tipo de Prenda select con loading state
interface TipoPrendaSelectProps {
  value: string;
  tiposDisponibles: string[];
  cargandoTipos: boolean;
  onChange: (value: string) => void;
}

const TipoPrendaSelect = React.memo(
  ({ value, tiposDisponibles, cargandoTipos, onChange }: TipoPrendaSelectProps) => (
    <div className="space-y-2">
      <label className="block text-sm font-semibold text-red-900">
        Tipo de Prenda
      </label>
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-red-500 focus:border-opacity-50 transition-colors appearance-none"
          disabled={cargandoTipos}
        >
          <option value="">
            {cargandoTipos
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
            <RefreshCw className="h-5 w-5 animate-spin text-red-500" />
          </div>
        )}
      </div>
    </div>
  )
);
TipoPrendaSelect.displayName = "TipoPrendaSelect";

// Interfaces TypeScript
interface WipDisponible {
  wip_id: string;
  nombre: string;
  costo_actual: number;
  disponible: boolean;
  grupo: string;
}

interface WipSeleccionada {
  wip_id: string;
  factor_ajuste: number;
  costo_base: number;
}

interface EstiloSimilar {
  codigo: string;
  familia_producto: string;
  tipo_prenda: string;
  temporada: string;
  ops_encontradas: number;
  costo_promedio: number;
}

interface FormData {
  cliente_marca: string;
  temporada: string;
  categoria_lote: string;
  familia_producto: string;
  tipo_prenda: string;
  codigo_estilo: string;
  usuario: string;
  version_calculo: string;
}

interface ComponenteCosto {
  nombre: string;
  costo_unitario: number;
  fuente: string;
  ajustado_por_rango?: boolean;
}

interface InfoComercial {
  ops_utilizadas: number;
  historico_volumen: {
    volumen_total_6m: number;
    volumen_promedio: number;
    ops_producidas: number;
  };
  tendencias_costos: Array<{
    año: number;
    mes: number;
    costo_textil_promedio: number;
    costo_manufactura_promedio: number;
    ops_mes: number;
  }>;
}

interface ResultadoCotizacion {
  id_cotizacion: string;
  fecha_cotizacion: string;
  inputs: FormData;
  componentes: ComponenteCosto[];
  costo_textil: number;
  costo_manufactura: number;
  costo_avios: number;
  costo_materia_prima: number;
  costo_indirecto_fijo: number;
  gasto_administracion: number;
  gasto_ventas: number;
  costo_base_total: number;
  factor_lote: number;
  factor_esfuerzo: number;
  factor_estilo: number;
  factor_marca: number;
  vector_total: number;
  precio_final: number;
  margen_aplicado: number;
  validaciones: string[];
  alertas: string[];
  info_comercial: InfoComercial;
  categoria_esfuerzo: number;
  categoria_estilo: string;
  version_calculo_usada?: string;
  volumen_historico?: number;
}

interface OpReal {
  cod_ordpro: string;
  estilo_propio: string;
  cliente: string;
  fecha_facturacion: string | null;
  prendas_requeridas: number;
  monto_factura: number;
  precio_unitario: number;
  costos_componentes: {
    textil: number;
    manufactura: number;
    avios: number;
    materia_prima: number;
    indirecto_fijo: number;
    gasto_admin: number;
    gasto_ventas: number;
  };
  costo_total_unitario: number;
  costo_total_original?: number;
  fue_ajustado?: boolean;
  esfuerzo_total: number;
}

interface OpsResponse {
  ops_data: {
    ops_utilizadas: OpReal[];
    metodo_utilizado: string;
    estadisticas: {
      total_ops: number;
      costo_promedio: number;
      costo_min: number;
      costo_max: number;
      esfuerzo_promedio: number;
      rango_fechas?: {
        desde: string;
        hasta: string;
      };
    };
    parametros_busqueda: {
      codigo_estilo: string | null;
      familia_producto: string | null;
      tipo_prenda: string | null;
      cliente: string | null;
      version_calculo: string;
    };
    rangos_aplicados?: boolean;
  };
  timestamp: string;
  total_ops_encontradas: number;
}

interface AutoCompletadoInfo {
  autocompletado_disponible: boolean;
  info_estilo?: {
    familia_producto?: string;
    tipo_prenda: string;
    categoria: string;
    volumen_total: number;
  };
  campos_sugeridos?: {
    familia_producto?: string;
    tipo_prenda: string;
  };
}

const SistemaCotizadorTDV = () => {
  // Estados principales
  const [pestanaActiva, setPestanaActiva] = useState<
    "formulario" | "resultados"
  >("formulario");
  const [wipsDisponibles, setWipsDisponibles] = useState<{
    wips_textiles: WipDisponible[];
    wips_manufactura: WipDisponible[];
  }>({ wips_textiles: [], wips_manufactura: [] });
  const [cotizacionActual, setCotizacionActual] =
    useState<ResultadoCotizacion | null>(null);
  const [cargando, setCargando] = useState(false);

  // Estados de datos maestros dinámicos
  const [clientesDisponibles, setClientesDisponibles] = useState<string[]>([]);
  const [familiasDisponibles, setFamiliasDisponibles] = useState<string[]>([]);
  const [tiposDisponibles, setTiposDisponibles] = useState<string[]>([]);
  const [cargandoFamilias, setCargandoFamilias] = useState(false);
  const [cargandoTipos, setCargandoTipos] = useState(false);

  // Estados para OPs reales
  const [opsReales, setOpsReales] = useState<OpsResponse | null>(null);
  const [cargandoOps, setCargandoOps] = useState(false);
  const [errorOps, setErrorOps] = useState<string | null>(null);

  // Estado para OPs seleccionadas en la tabla interactiva
  const [selectedOpsCode, setSelectedOpsCode] = useState<string[]>([]);

  // Estados para costos calculados del WIP (para sobrescribir backend values)
  const [costosWipCalculados, setCostosWipCalculados] = useState<{
    textil_por_prenda: number | null;
    manufactura_por_prenda: number | null;
  }>({
    textil_por_prenda: null,
    manufactura_por_prenda: null,
  });

  // Estados para formulario - separados para evitar pérdida de foco
  const [formData, setFormData] = useState<FormData>({
    cliente_marca: "LACOSTE",
    temporada: "", // NOTA: Ya no se usa en la UI
    categoria_lote: "Lote Mediano",
    familia_producto: "", // NOTA: Ya no se usa en la UI
    tipo_prenda: "",
    codigo_estilo: "",
    usuario: "Usuario Demo",
    version_calculo: "FLUIDO",
  });

  // Estado debounced para los efectos - evita que se disparen en cada keystroke
  const [debouncedFormData, setDebouncedFormData] = useState<FormData>(formData);

  // Estados para búsqueda de estilos
  const [estilosEncontrados, setEstilosEncontrados] = useState<EstiloSimilar[]>(
    [],
  );
  const [buscandoEstilo, setBuscandoEstilo] = useState(false);
  const [esEstiloNuevo, setEsEstiloNuevo] = useState(false);

  const [infoAutoCompletado, setInfoAutoCompletado] =
    useState<AutoCompletadoInfo | null>(null);

  // Estados para WIPs seleccionadas
  const [wipsTextiles, setWipsTextiles] = useState<WipSeleccionada[]>([]);
  const [wipsManufactura, setWipsManufactura] = useState<WipSeleccionada[]>([]);

  // Referencias para evitar re-renders y debouncing
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const familiaDebounceRef = useRef<NodeJS.Timeout | null>(null);
  const tipoDebounceRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const opsSelectionTableRef = useRef<OpsSelectionTableRef>(null); // Ref para dispara búsqueda de OPs

  // Memoized validation
  const erroresFormulario = useMemo(() => {
    const errores = [];

    if (!formData.cliente_marca) errores.push("Cliente/Marca es requerido");
    // NOTA: temporada y familia_producto ya no son requeridas
    if (!formData.tipo_prenda) errores.push("Tipo de Prenda es requerido");
    if (!formData.codigo_estilo) errores.push("Código de estilo propio es requerido");

    // NOTA: Se removió validación de WIPs requeridas - ahora es opcional

    return errores;
  }, [formData]);

  // Manejador de cambio de formulario con actualización inmediata
  const manejarCambioFormulario = useCallback(
    (campo: keyof FormData, valor: string) => {
      // Actualizar formData inmediatamente para que el input muestre el valor
      setFormData((prev) => ({
        ...prev,
        [campo]: valor,
        // NOTA: ya no se limpia tipo_prenda (familia_producto fue eliminado)
      }));

      // Para tipo_prenda, debounce triggers disparará el re-render después
      // Esto evita que los efectos se disparen en cada keystroke
    },
    [],
  );

  // Handler memoizado específicamente para el código de estilo
  const handleCodigoEstiloChange = useCallback(
    (valor: string) => {
      manejarCambioFormulario("codigo_estilo", valor);
    },
    [manejarCambioFormulario],
  );

  // ✨ MEMOIZED CALLBACKS para evitar re-renders innecesarios en child components
  // Callback memoizado para WipDesgloseTable - evita infinite requests por cambio de función
  const handleCostosWipCalculados = useCallback(
    (textil: number, manufactura: number) => {
      setCostosWipCalculados({
        textil_por_prenda: textil,
        manufactura_por_prenda: manufactura,
      });
    },
    []
  );

  // Callback memoizado para OpsSelectionTable - evita re-renders innecesarios
  const handleOpsSelectionError = useCallback(
    (error: string) => {
      setErrorOps(error);
    },
    []
  );

  // Efecto 3: Cargar WIPs cuando cambia tipo (usando debouncedFormData, solo para estilos nuevos)
  useEffect(() => {
    if (debouncedFormData.tipo_prenda && esEstiloNuevo) {
      cargarWipsPorTipoPrenda(debouncedFormData.tipo_prenda, debouncedFormData.version_calculo);
    }
  }, [debouncedFormData.tipo_prenda, debouncedFormData.version_calculo, esEstiloNuevo]);

  // Efecto 4 (removido): Búsqueda debounced de estilos - Ahora se busca con botón manual
  // Limpieza de búsqueda cuando el código se vacía
  useEffect(() => {
    if (!formData.codigo_estilo || formData.codigo_estilo.length < 3) {
      setEstilosEncontrados([]);
      setEsEstiloNuevo(true);
      setInfoAutoCompletado(null);
    }
  }, [formData.codigo_estilo]);

  // Cargar datos iniciales
  useEffect(() => {
    const cargarDatosIniciales = async () => {
      await Promise.all([
        cargarWipsDisponibles(formData.version_calculo),
        cargarClientesDisponibles(formData.version_calculo),
        cargarFamiliasProductos(formData.version_calculo),
      ]);
    };
    cargarDatosIniciales();
  }, []); // Solo una vez al montar

  // Limpiar al desmontar
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Debounce formData para evitar pérdida de foco - actualiza debouncedFormData después de 3 segundos sin cambios
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedFormData(formData);
    }, 3000); // 3 segundos de espera sin escribir

    return () => {
      clearTimeout(timer);
    };
  }, [formData]);

  // ========================================
  // 🔧 FUNCIONES DE CARGA CORREGIDAS
  // ========================================

  const cargarWipsDisponibles = useCallback(
    async (versionCalculo: string = "FLUIDO") => {
      try {
        const data = await get<{
          wips_textiles: any[];
          wips_manufactura: any[];
        }>(
          `wips-disponibles?version_calculo=${encodeURIComponent(versionCalculo)}`,
        );
        setWipsDisponibles(data);
        // console.log(
        //   `✅ WIPs cargadas para ${versionCalculo}: ${
        //     data.wips_textiles.length + data.wips_manufactura.length
        //   }`,
        // );
      } catch (error) {
        console.error("Error cargando WIPs o conectando con backend:", error);
        setWipsDisponibles({ wips_textiles: [], wips_manufactura: [] });
      }
    },
    [],
  );

  const cargarWipsPorTipoPrenda = useCallback(
    async (tipoPrenda: string, versionCalculo: string) => {
      if (!tipoPrenda) {
        setWipsDisponibles({ wips_textiles: [], wips_manufactura: [] });
        return;
      }

      try {
        const data = await get<{
          wips_textiles: any[];
          wips_manufactura: any[];
        }>(
          `wips-disponibles?tipo_prenda=${encodeURIComponent(tipoPrenda)}&version_calculo=${encodeURIComponent(
            versionCalculo,
          )}`,
        );
        setWipsDisponibles(data);
        setWipsTextiles([]);
        setWipsManufactura([]);
        // console.log(
        //   `✅ WIPs específicas cargadas para ${tipoPrenda} (${versionCalculo})`,
        // );
      } catch (error) {
        console.error("Error cargando WIPs específicas:", error);
      }
    },
    [],
  );

  const cargarClientesDisponibles = useCallback(
    async (versionCalculo: string = "FLUIDO") => {
      try {
        const data = await get<{ clientes: any[] }>(
          `clientes?version_calculo=${encodeURIComponent(versionCalculo)}`,
        );
        setClientesDisponibles(data.clientes);
        // console.log(
        //   `✅ Clientes cargados para ${versionCalculo}: ${data.clientes.length}`,
        // );
      } catch /*(error)*/ {
        // console.error("Error cargando clientes:", error);
        setClientesDisponibles([]);
      }
    },
    [],
  );

  const cargarFamiliasProductos = useCallback(
    async (versionCalculo: string = "FLUIDO") => {
      setCargandoFamilias(true);
      try {
        const data = await get<{ familias: any[] }>(
          `familias-productos?version_calculo=${encodeURIComponent(versionCalculo)}`,
        );
        setFamiliasDisponibles(data.familias);
        // console.log(
        //   `✅ Familias cargadas para ${versionCalculo}: ${data.familias.length}`,
        // );
      } /*catch (error) {
        // console.error("Error cargando familias:", error);
        setFamiliasDisponibles([]);
      }*/ finally {
        setCargandoFamilias(false);
      }
    },
    [],
  );

  const cargarTiposPrenda = useCallback(
    async (familia: string, versionCalculo: string = "FLUIDO") => {
      if (!familia) {
        setTiposDisponibles([]);
        return;
      }

      setCargandoTipos(true);
      try {
        const data = await get<{ tipos: any[] }>(
          `tipos-prenda/${encodeURIComponent(familia)}?version_calculo=${encodeURIComponent(versionCalculo)}`,
        );
        setTiposDisponibles(data.tipos);
        // console.log(
        //   `✅ Tipos cargados para ${familia} (${versionCalculo}): ${data.tipos.length}`,
        // );
      } catch /*(error)*/ {
        // console.error("Error cargando tipos:", error);
        setTiposDisponibles([]);
      } finally {
        setCargandoTipos(false);
      }
    },
    [],
  );

  // Cargar TODOS los tipos de prenda (sin filtrar por familia)
  const cargarTodosTipos = useCallback(
    async (versionCalculo: string = "FLUIDO") => {
      setCargandoTipos(true);
      try {
        // Obtener todas las familias primero
        const familiasData = await get<{ familias: string[] }>(
          `familias-productos?version_calculo=${encodeURIComponent(versionCalculo)}`,
        );

        // Obtener tipos para todas las familias y combinarlos
        const todasLasFamilias = familiasData.familias;
        const tiposUnicos = new Set<string>();

        for (const familia of todasLasFamilias) {
          try {
            const tiposData = await get<{ tipos: string[] }>(
              `tipos-prenda/${encodeURIComponent(familia)}?version_calculo=${encodeURIComponent(versionCalculo)}`,
            );
            tiposData.tipos.forEach(tipo => tiposUnicos.add(tipo));
          } catch {
            // Ignorar errores de familias individuales
          }
        }

        setTiposDisponibles(Array.from(tiposUnicos).sort());
      } catch {
        // Si no funciona, al menos mantener vacío en lugar de error
        setTiposDisponibles([]);
      } finally {
        setCargandoTipos(false);
      }
    },
    [get],
  );

  // Efecto 1: Recargar cuando cambia version_calculo (usando debouncedFormData)
  useEffect(() => {
    const recargarDatosVersion = async () => {
      try {
        // Cargar datos principales
        await Promise.all([
          cargarWipsDisponibles(debouncedFormData.version_calculo),
          cargarClientesDisponibles(debouncedFormData.version_calculo),
          cargarTodosTipos(debouncedFormData.version_calculo), // ✅ Cargar TODOS los tipos
        ]);

        // Recargar WIPs si hay tipo y es nuevo
        if (debouncedFormData.tipo_prenda && esEstiloNuevo) {
          await cargarWipsPorTipoPrenda(
            debouncedFormData.tipo_prenda,
            debouncedFormData.version_calculo,
          );
        }
      } catch (error) {
        console.error(`❌ Error recargando datos:`, error);
      }
    };

    recargarDatosVersion();
  }, [debouncedFormData.version_calculo, cargarTodosTipos, esEstiloNuevo, debouncedFormData.tipo_prenda]); // Usa debouncedFormData para evitar actualizaciones frecuentes

  // NOTA: Efecto 2 (cargar tipos cuando cambia familia) fue eliminado
  // Ahora se cargan TODOS los tipos al iniciar (cargarTodosTipos) para que estilos nuevos puedan seleccionar tipo_prenda

  const verificarYBuscarEstilo = useCallback(
    async (codigoEstilo: string, cliente: string, versionCalculo: string) => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      if (!codigoEstilo || codigoEstilo.length < 3) {
        setEstilosEncontrados([]);
        setEsEstiloNuevo(true);
        setInfoAutoCompletado(null);
        return;
      }

      setBuscandoEstilo(true);
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      try {
        // Paso 1: verificación completa
        const verificacion = await get<any>(
          `verificar-estilo-completo/${encodeURIComponent(codigoEstilo)}?version_calculo=${encodeURIComponent(
            versionCalculo,
          )}`,
          { signal: abortController.signal },
        );
        if (!abortController.signal.aborted) {
          // console.log(
          //   `🔍 Verificación completa ${codigoEstilo}:`,
          //   verificacion,
          // );
          const esNuevo = verificacion.es_estilo_nuevo;
          setEsEstiloNuevo(esNuevo);

          if (!esNuevo && verificacion.autocompletado?.disponible) {
            const { tipo_prenda } = verificacion.autocompletado;
            // NOTA: Ya no se preseteea familia_producto
            if (tipo_prenda) {
              // console.log(`🎯 Auto-completando: ${tipo_prenda}`);
              setFormData((prev) => ({
                ...prev,
                tipo_prenda,
              }));

              // ✅ IMPORTANTE: Actualizar debouncedFormData inmediatamente para evitar pérdida de valor
              // Esto previene que se pierda el tipo_prenda mientras el debounce timer sigue corriendo
              setDebouncedFormData((prev) => ({
                ...prev,
                tipo_prenda,
              }));

              // Agregar tipo_prenda al array de tipos disponibles si no está ya
              setTiposDisponibles((prev) => {
                if (!prev.includes(tipo_prenda)) {
                  return [...prev, tipo_prenda];
                }
                return prev;
              });

              setInfoAutoCompletado({
                autocompletado_disponible: true,
                info_estilo: {
                  tipo_prenda,
                  categoria: verificacion.categoria,
                  volumen_total: verificacion.volumen_historico,
                },
                campos_sugeridos: { tipo_prenda },
              });
            }
          } else {
            setInfoAutoCompletado(null);
          }
        }

        // Paso 2: buscar estilos similares
        const estilos = await get<any[]>(
          `buscar-estilos/${encodeURIComponent(codigoEstilo)}?cliente=${encodeURIComponent(cliente)}&limite=10&version_calculo=${encodeURIComponent(
            versionCalculo,
          )}`,
          { signal: abortController.signal },
        );
        if (!abortController.signal.aborted) {
          setEstilosEncontrados(estilos);
          // console.log(`🔍 Estilos similares encontrados: ${estilos.length}`);
        }
      } catch (error: any) {
        if (error.name !== "AbortError") {
          // console.error("Error en verificación:", error);
          setEstilosEncontrados([]);
          setEsEstiloNuevo(true);
          setInfoAutoCompletado(null);
        }
      } finally {
        if (!abortController.signal.aborted) {
          setBuscandoEstilo(false);
        }
      }
    },
    [cargarTiposPrenda],
  );

  // Handler para buscar estilo manualmente (sin debounce)
  const onBuscarEstilo = useCallback(() => {
    if (formData.codigo_estilo && formData.codigo_estilo.length >= 3) {
      verificarYBuscarEstilo(
        formData.codigo_estilo,
        formData.cliente_marca,
        formData.version_calculo,
      );
    }
  }, [formData.codigo_estilo, formData.cliente_marca, formData.version_calculo, verificarYBuscarEstilo]);

  // cargarOpsReales (POST)
  const cargarOpsReales = useCallback(
    async (cotizacion: ResultadoCotizacion) => {
      setCargandoOps(true);
      setErrorOps(null);

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
          wips_manufactura: null,
        };

        const resultado = await post<any>(
          "/ops-utilizadas-cotizacion",
          payload,
        );
        setOpsReales(resultado);
        // console.log(
        //   `✅ OPs reales cargadas: ${resultado.total_ops_encontradas}`,
        // );
      } catch (error: any) {
        // console.error("Error cargando OPs reales:", error);
        setErrorOps(
          error?.message || "Error de conexión al cargar OPs de referencia",
        );
      } finally {
        setCargandoOps(false);
      }
    },
    [],
  );

  // ========================================
  // 🔧 FUNCIONES DE INTERACCIÓN MEJORADAS
  // ========================================

  const seleccionarEstiloSimilar = useCallback(
    (estilo: EstiloSimilar) => {
      // console.log(`🎯 Seleccionando estilo similar:`, estilo);

      // NOTA: Ya no se preseteea familia_producto
      setFormData((prev) => ({
        ...prev,
        tipo_prenda: estilo.tipo_prenda,
      }));
      setEstilosEncontrados([]);
    },
    [],
  );

  const toggleWipTextil = useCallback((wip: WipDisponible) => {
    setWipsTextiles((prev) => {
      const existe = prev.find((w) => w.wip_id === wip.wip_id);
      if (existe) {
        return prev.filter((w) => w.wip_id !== wip.wip_id);
      } else {
        return [
          ...prev,
          {
            wip_id: wip.wip_id,
            factor_ajuste: 1.0,
            costo_base: wip.costo_actual,
          },
        ];
      }
    });
  }, []);

  const toggleWipManufactura = useCallback((wip: WipDisponible) => {
    setWipsManufactura((prev) => {
      const existe = prev.find((w) => w.wip_id === wip.wip_id);
      if (existe) {
        return prev.filter((w) => w.wip_id !== wip.wip_id);
      } else {
        return [
          ...prev,
          {
            wip_id: wip.wip_id,
            factor_ajuste: 1.0,
            costo_base: wip.costo_actual,
          },
        ];
      }
    });
  }, []);

  const actualizarFactorWip = useCallback(
    (
      setWips: React.Dispatch<React.SetStateAction<WipSeleccionada[]>>,
      wipId: string,
      nuevoFactor: string,
    ) => {
      const factor = parseFloat(nuevoFactor) || 1.0;
      setWips((prev) =>
        prev.map((w) =>
          w.wip_id === wipId ? { ...w, factor_ajuste: factor } : w,
        ),
      );
    },
    [],
  );

  const procesarCotizacion = useCallback(async () => {
    setCargando(true);
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
        cod_ordpros: selectedOpsCode && selectedOpsCode.length > 0 ? selectedOpsCode : null,
      };

      // console.log("🚀 Procesando cotización:", payload);

      const resultado = await post<any>("/cotizar", payload);
      console.log("🔍 BACKEND RESPONSE (Tab 1) - costo_textil:", resultado.costo_textil, "costo_manufactura:", resultado.costo_manufactura);
      console.log("📊 selectedOpsCode being used:", selectedOpsCode);
      console.log("📋 Full resultado from backend:", resultado);
      setCotizacionActual(resultado);

      // Dispara la búsqueda de OPs en OpsSelectionTable (sin búsqueda automática)
      opsSelectionTableRef.current?.iniciarBusqueda();

      await cargarOpsReales(resultado);

      setPestanaActiva("resultados");
      // console.log(`✅ Cotización exitosa: ${resultado.id_cotizacion}`);
    } catch (error: any) {
      // console.error("Error procesando cotización:", error);
      const msg =
        error?.message ||
        (error?.response
          ? "Error procesando cotización"
          : "Error de conexión con el servidor. Verifique que el backend esté ejecutándose.");
      alert(`Error: ${msg}`);
    } finally {
      setCargando(false);
    }
  }, [formData, esEstiloNuevo, wipsTextiles, wipsManufactura, selectedOpsCode, cargarOpsReales]);

  // ========================================
  // 🎨 COMPONENTES MEMOIZADOS CORREGIDOS
  // ========================================

  // Memoized SwitchVersionCalculo
  const SwitchVersionCalculo = useMemo(
    () => (
      <div className="bg-white rounded-xl shadow-md border border-gray-100 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Database className="h-5 w-5 text-red-900" />
            <div>
              <h3 className="font-semibold text-red-900">Versión de Datos</h3>
              <p className="text-sm text-gray-600">
                Selecciona el tipo de cálculo para la cotización
              </p>
              <div className="text-xs text-gray-500 mt-1">
                {cargandoFamilias || cargandoTipos
                  ? "🔄 Recargando datos..."
                  : "✅ Datos actualizados"}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4 bg-gray-50 px-4 py-2 rounded-lg">
            <span
              className={`font-medium transition-colors ${
                formData.version_calculo === "FLUIDO"
                  ? "text-gray-900"
                  : "text-gray-400"
              }`}
              style={{
                fontWeight:
                  formData.version_calculo === "FLUIDO" ? "600" : "400",
                textTransform: "uppercase",
              }}
            >
              FLUIDO
            </span>
            <button
              type="button"
              onClick={() => {
                const nuevaVersion =
                  formData.version_calculo === "FLUIDO" ? "truncado" : "FLUIDO";
                // console.log(
                //   `🔄 Cambiando versión: ${formData.version_calculo} → ${nuevaVersion}`,
                // );
                manejarCambioFormulario("version_calculo", nuevaVersion);
              }}
              className="relative inline-flex h-8 w-16 items-center rounded-full transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2"
              style={{
                backgroundColor:
                  formData.version_calculo === "FLUIDO" ? "#821417" : "#bd4c42",
              }}
            >
              <span
                className="inline-block h-6 w-6 transform rounded-full bg-white shadow-lg transition-transform duration-300"
                style={{
                  transform:
                    formData.version_calculo === "FLUIDO"
                      ? "translateX(2px)"
                      : "translateX(34px)",
                }}
              />
            </button>
            <span
              className={`font-medium transition-colors ${
                formData.version_calculo === "truncado"
                  ? "text-gray-900"
                  : "text-gray-400"
              }`}
              style={{
                fontWeight:
                  formData.version_calculo === "truncado" ? "600" : "400",
                textTransform: "uppercase",
              }}
            >
              TRUNCADO
            </span>
          </div>
        </div>

        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${formData.version_calculo === "FLUIDO" ? "bg-green-500" : "bg-blue-500"}`}
            ></div>
            <span className="text-xs text-gray-600">
              Usando datos:{" "}
              <strong className="uppercase">{formData.version_calculo}</strong>
            </span>
          </div>

          <div className="text-xs text-gray-500">
            📊 {familiasDisponibles.length} familias | {tiposDisponibles.length}{" "}
            tipos
          </div>
        </div>
      </div>
    ),
    [
      formData.version_calculo,
      cargandoFamilias,
      cargandoTipos,
      familiasDisponibles.length,
      tiposDisponibles.length,
      manejarCambioFormulario,
    ],
  );


  // Memoized RutaTextilRecomendada
  const RutaTextilRecomendada = React.memo(() => {
    const [rutaTextil, setRutaTextil] = useState<any>(null);
    const [cargandoRuta, setCargandoRuta] = useState(false);
    const [errorRuta, setErrorRuta] = useState<string | null>(null);

    useEffect(() => {
      const cargarRutaTextil = async () => {
        if (!formData.tipo_prenda) {
          setRutaTextil(null);
          return;
        }

        if (!esEstiloNuevo) {
          setRutaTextil(null);
          return;
        }

        setCargandoRuta(true);
        setErrorRuta(null);

        try {
          // console.log(
          //   `🔍 Cargando ruta textil para: ${formData.tipo_prenda} (${formData.version_calculo})`,
          // );

          const data = await get<any>(
            `ruta-textil-recomendada/${encodeURIComponent(formData.tipo_prenda)}?version_calculo=${encodeURIComponent(
              formData.version_calculo,
            )}`,
          );

          // console.log(`✅ Ruta textil cargada:`, data);

          if (
            data &&
            Array.isArray(data.wips_recomendadas) &&
            data.wips_recomendadas.length > 0
          ) {
            setRutaTextil(data);
          } else {
            // console.log(`⚠️ Ruta textil sin WIPs recomendadas:`, data);
            setRutaTextil({
              ...data,
              wips_recomendadas: [],
              mensaje:
                "Sin WIPs específicas encontradas para este tipo de prenda",
            });
          }
        } catch (error: any) {
          // console.error("❌ Error conectando ruta textil:", error);
          setErrorRuta(
            error?.message || "Error de conexión al cargar ruta textil",
          );
        } finally {
          setCargandoRuta(false);
        }
      };

      cargarRutaTextil();
    }, [formData.tipo_prenda, formData.version_calculo, esEstiloNuevo]);

    // CONDICIONES DE MOSTRAR CORREGIDAS
    if (!formData.tipo_prenda) {
      return (
        <div className="mb-6 p-4 rounded-xl border-2 bg-orange-50 border-orange-400">
          <div className="text-sm text-gray-600">
            💡 Selecciona un tipo de prenda para ver recomendaciones de WIPs
          </div>
        </div>
      );
    }

    if (!esEstiloNuevo) {
      return null; // Solo mostrar para estilos nuevos
    }

    return (
      <div className="mb-6 p-4 rounded-xl border-2 bg-orange-50 border-orange-400">
        <h4 className="font-bold mb-3 flex items-center gap-2 text-red-900">
          🧵 Ruta Textil Recomendada para {formData.tipo_prenda}
          <span className="text-sm bg-orange-100 px-2 py-1 rounded text-orange-800">
            Estilo Nuevo
          </span>
          <span className="text-xs bg-blue-100 px-2 py-1 rounded text-blue-800">
            {formData.version_calculo}
          </span>
        </h4>

        {cargandoRuta ? (
          <div className="flex items-center gap-2 text-red-500">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Cargando ruta recomendada...</span>
          </div>
        ) : errorRuta ? (
          <div className="text-sm p-3 rounded bg-red-50 border border-red-200">
            <div className="text-red-700 font-semibold mb-1">
              ❌ Error cargando ruta:
            </div>
            <div className="text-red-600 text-xs">{errorRuta}</div>
          </div>
        ) : rutaTextil ? (
          <div className="space-y-3">
            {/* MOSTRAR WIPS SI EXISTEN */}
            {rutaTextil.wips_recomendadas &&
            rutaTextil.wips_recomendadas.length > 0 ? (
              <>
                <div className="grid grid-cols-4 gap-2 text-sm">
                  {rutaTextil.wips_recomendadas
                    .slice(0, 12)
                    .map((wip: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-2 rounded-lg text-center hover:shadow-md transition-all cursor-pointer bg-orange-200"
                        title={`Frecuencia: ${wip.frecuencia_uso || 0} usos | Recomendación: ${wip.recomendacion || "Media"}`}
                      >
                        <div className="font-semibold text-red-900">
                          WIP {wip.wip_id}
                        </div>
                        <div className="text-xs text-red-500">
                          {wip.nombre || `WIP ${wip.wip_id}`}
                        </div>
                        <div className="text-xs font-bold">
                          ${wip.costo_promedio?.toFixed(2) || "0.00"}
                        </div>
                        <div className="text-xs text-gray-600">
                          {wip.frecuencia_uso || 0} usos
                        </div>
                        {/* INDICADOR DE RECOMENDACIÓN */}
                        <div
                          className={`text-xs px-1 py-0.5 rounded mt-1 ${
                            wip.recomendacion === "Alta"
                              ? "bg-green-100 text-green-700"
                              : wip.recomendacion === "Media"
                                ? "bg-yellow-100 text-yellow-700"
                                : "bg-gray-100 text-gray-600"
                          }`}
                        >
                          {wip.recomendacion || "Media"}
                        </div>
                      </div>
                    ))}
                </div>

                <div className="text-xs text-gray-600 bg-white p-2 rounded">
                  💡 <strong>Tip:</strong> Estas WIPs son las más utilizadas
                  para {formData.tipo_prenda}. Puedes seleccionar las que mejor
                  se adapten a tu estilo específico.
                </div>
              </>
            ) : (
              <div className="text-sm p-3 rounded bg-yellow-50 border border-yellow-200">
                <div className="text-yellow-700 font-semibold mb-1">
                  ⚠️ Sin WIPs específicas
                </div>
                <div className="text-yellow-600 text-xs">
                  No se encontraron WIPs frecuentemente utilizadas para{" "}
                  {formData.tipo_prenda} en versión {formData.version_calculo}.
                  Puedes seleccionar WIPs manualmente en la sección de
                  configuración.
                </div>
              </div>
            )}

            {/* INFORMACIÓN TÉCNICA */}
            <div className="mt-3 text-xs text-gray-500 border-t pt-2 flex justify-between">
              <span>
                📊 Método: {rutaTextil.metodo || "frecuencia_uso"} | 📈 Total
                encontradas: {rutaTextil.total_recomendadas || 0}
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
    );
  });

  RutaTextilRecomendada.displayName = "RutaTextilRecomendada";

  // Memoized ComponenteOpsReales
  const ComponenteOpsReales = React.memo(() => {
    if (!cotizacionActual) return null;

    const { info_comercial } = cotizacionActual;

    return (
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100 bg-red-800">
          <h2 className="text-xl font-bold flex items-center gap-3 text-white">
            <FileText className="h-6 w-6" />
            OPs de Referencia Utilizadas para el Cálculo
          </h2>
          <p className="text-white/80 mt-1">
            {opsReales ? (
              <>
                Base histórica: {opsReales.total_ops_encontradas} órdenes |
                Método: {opsReales.ops_data.metodo_utilizado} | Versión:{" "}
                {opsReales.ops_data.parametros_busqueda.version_calculo}
                {opsReales.ops_data.rangos_aplicados === true && (
                  <span className="ml-2 px-2 py-1 bg-yellow-500/30 rounded text-xs">
                    ✓ Rangos de seguridad aplicados
                  </span>
                )}
              </>
            ) : (
              <>
                Base histórica: {info_comercial?.ops_utilizadas || 0} órdenes
                procesadas | Volumen:{" "}
                {info_comercial?.historico_volumen?.volumen_total_6m?.toLocaleString() ||
                  0}{" "}
                prendas
              </>
            )}
          </p>
        </div>

        <div className="p-6">
          {cargandoOps ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin mr-3 text-red-500" />
              <span className="text-lg text-red-900">
                Cargando OPs de referencia...
              </span>
            </div>
          ) : errorOps ? (
            <div className="text-center py-8">
              <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-red-400" />
              <p className="text-lg font-semibold mb-2 text-red-900">
                Error al cargar OPs
              </p>
              <p className="text-sm text-gray-600">{errorOps}</p>
              <button
                onClick={() => cargarOpsReales(cotizacionActual)}
                className="mt-4 px-4 py-2 rounded-lg text-white bg-red-500"
              >
                Reintentar
              </button>
            </div>
          ) : cotizacionActual ? (
            <>
              <OpsSelectionTable
                ref={opsSelectionTableRef}
                codigoEstilo={cotizacionActual.inputs.codigo_estilo}
                versionCalculo={cotizacionActual.inputs.version_calculo}
                opsSeleccionadasPrevia={selectedOpsCode}
                onOpsSelected={async (opsSeleccionadas) => {
                  try {
                    // Guardar los códigos de OP seleccionadas
                    const codOrdpros = opsSeleccionadas.map((op) => op.cod_ordpro);
                    setSelectedOpsCode(codOrdpros);

                    setFormData(prev => ({
                      ...prev,
                      cod_ordpros: codOrdpros
                    }));

                    // Procesar la cotización completa
                    setCargando(true);
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
                      cod_ordpros: codOrdpros,
                    };

                    console.log("📤 PAYLOAD ENVIADO AL BACKEND:", JSON.stringify(payload, null, 2));
                    const resultado = await post<any>("/cotizar", payload);
                    console.log("🔍 BACKEND RESPONSE - costo_textil:", resultado.costo_textil, "costo_manufactura:", resultado.costo_manufactura);
                    console.log("📊 OPs seleccionadas siendo procesadas:", codOrdpros);
                    console.log("📋 Full resultado from backend:", resultado);
                    setCotizacionActual(resultado);

                    await cargarOpsReales(resultado);
                  } catch (error) {
                    console.error("Error generando cotización:", error);
                    alert("Error al generar cotización: " + (error instanceof Error ? error.message : "Error desconocido"));
                  } finally {
                    setCargando(false);
                  }
                }}
                onError={handleOpsSelectionError}
              />

              {/* Mostrar desglose WIP cuando hay OPs seleccionadas */}
              {selectedOpsCode.length > 0 && (
                <div className="mt-8">
                  <h3 className="text-lg font-bold text-red-900 mb-4">
                    Análisis de Costos por WIP
                  </h3>
                  <WipDesgloseTable
                    codigoEstilo={cotizacionActual.inputs.codigo_estilo}
                    versionCalculo={cotizacionActual.inputs.version_calculo}
                    codOrdpros={selectedOpsCode}
                    onCostosCalculados={handleCostosWipCalculados}
                  />
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-8">
              <Package className="h-12 w-12 mx-auto mb-4 text-red-500" />
              <p className="text-lg font-semibold mb-2 text-red-900">
                Sin OPs de referencia
              </p>
              <p className="text-sm text-gray-600">
                No se encontraron órdenes de producción para los criterios
                especificados
              </p>
            </div>
          )}
        </div>
      </div>
    );
  });

  ComponenteOpsReales.displayName = "ComponenteOpsReales";

  // ========================================
  // 🎨 FORMULARIO PRINCIPAL CORREGIDO
  // ========================================

  const FormularioPrincipal = React.memo(() => (
    <div className="space-y-8">
      {/* Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-red-800 via-red-700 to-red-600">
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
              <p className="text-white/90 text-lg">
                Metodología WIP - Cotización Inteligente
              </p>
              <p className="text-white/70 text-sm mt-1">
                Basado en costos históricos y configuración modular • Versión
                activa: <strong>{formData.version_calculo}</strong>
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
        <div className="p-6 border-b border-gray-100 bg-red-800">
          <h2 className="text-xl font-bold flex items-center gap-3 text-white">
            <Package className="h-6 w-6" />
            Información del Producto
          </h2>
          <p className="text-white/80 mt-1">
            Datos básicos para la cotización • Versión:{" "}
            {formData.version_calculo}
          </p>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-2 gap-6">
            <ClienteSelect
              value={formData.cliente_marca}
              clientesDisponibles={clientesDisponibles}
              onChange={(valor) =>
                manejarCambioFormulario("cliente_marca", valor)
              }
            />

            <CampoCodigoEstiloComponent
              value={formData.codigo_estilo}
              buscandoEstilo={buscandoEstilo}
              estilosEncontrados={estilosEncontrados}
              esEstiloNuevo={esEstiloNuevo}
              infoAutoCompletado={infoAutoCompletado}
              onChange={handleCodigoEstiloChange}
              onBuscar={onBuscarEstilo}
              onSelectStyle={seleccionarEstiloSimilar}
            />

            <CategoriaLoteSelect
              value={formData.categoria_lote}
              onChange={(valor) =>
                manejarCambioFormulario("categoria_lote", valor)
              }
            />

            <TipoPrendaSelect
              value={formData.tipo_prenda}
              tiposDisponibles={tiposDisponibles}
              cargandoTipos={cargandoTipos}
              onChange={(valor) =>
                manejarCambioFormulario("tipo_prenda", valor)
              }
            />
          </div>
        </div>
      </div>

      {/* Botón de cotización */}
      <div className="flex justify-center">
        <div className="flex flex-col items-center space-y-4">
          {erroresFormulario.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 max-w-md">
              <h4 className="font-semibold text-red-900 mb-2">
                Campos requeridos:
              </h4>
              <ul className="text-sm text-red-600 space-y-1">
                {erroresFormulario.map((error, idx) => (
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
            disabled={cargando || erroresFormulario.length > 0}
            className="group relative px-12 py-4 font-bold text-white rounded-2xl shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 bg-gradient-to-r from-red-800 via-red-700 to-red-600"
          >
            {cargando ? (
              <div className="flex items-center gap-3">
                <RefreshCw className="h-6 w-6 animate-spin" />
                <span className="text-lg">Procesando Cotización...</span>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <DollarSign className="h-6 w-6" />
                <span className="text-lg">Configurar Producción</span>
              </div>
            )}
          </button>
        </div>
      </div>
    </div>
  ));

  FormularioPrincipal.displayName = "FormularioPrincipal";

  // ========================================
  // 🎨 PANTALLA RESULTADOS
  // ========================================

  const PantallaResultados = React.memo(() => {
    // Memoized componentesAgrupados
    const componentesAgrupados = useMemo(() => {
      if (!cotizacionActual) return []; // Safe: inside callback, not hook

      // Usar costos del WIP si están disponibles, sino usar los del backend
      const costoTextil = costosWipCalculados.textil_por_prenda ?? cotizacionActual.costo_textil;
      const costoManufactura = costosWipCalculados.manufactura_por_prenda ?? cotizacionActual.costo_manufactura;

      return [
        {
          nombre: "Costo Textil",
          costo_unitario: costoTextil,
          fuente: costosWipCalculados.textil_por_prenda ? "wip" : "historico",
          badge: costosWipCalculados.textil_por_prenda
            ? `${selectedOpsCode.length} OPs seleccionadas`
            : esEstiloNuevo
            ? `${wipsTextiles?.length || 0} WIPs`
            : "histórico",
          es_agrupado: false,
        },
        {
          nombre: "Costo Manufactura",
          costo_unitario: costoManufactura,
          fuente: costosWipCalculados.manufactura_por_prenda ? "wip" : "historico",
          badge: costosWipCalculados.manufactura_por_prenda
            ? `${selectedOpsCode.length} OPs seleccionadas`
            : esEstiloNuevo
            ? `${wipsManufactura?.length || 0} WIPs`
            : "histórico",
          es_agrupado: false,
        },
        {
          nombre: "Costo Materia Prima",
          costo_unitario: cotizacionActual.costo_materia_prima,
          fuente: "ultimo_costo",
          badge: "último costo",
          es_agrupado: false,
        },
        {
          nombre: "Costo Avíos",
          costo_unitario: cotizacionActual.costo_avios,
          fuente: "ultimo_costo",
          badge: "último costo",
          es_agrupado: false,
        },
        {
          nombre: "Costo Indirecto Fijo",
          costo_unitario: cotizacionActual.costo_indirecto_fijo,
          fuente: "formula",
          badge: "fórmula",
          es_agrupado: false,
        },
        {
          nombre: "Gasto Administración",
          costo_unitario: cotizacionActual.gasto_administracion,
          fuente: "formula",
          badge: "fórmula",
          es_agrupado: false,
        },
        {
          nombre: "Gasto Ventas",
          costo_unitario: cotizacionActual.gasto_ventas,
          fuente: "formula",
          badge: "fórmula",
          es_agrupado: false,
        },
      ];
    }, [
      cotizacionActual,
      esEstiloNuevo,
      wipsTextiles.length,
      wipsManufactura.length,
      costosWipCalculados.textil_por_prenda,
      costosWipCalculados.manufactura_por_prenda,
      selectedOpsCode.length,
    ]);

    // Early return after hooks (safe)
    if (!cotizacionActual) {
      return (
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 text-center">
          <p className="text-lg font-semibold text-red-800">
            No hay cotización disponible
          </p>
        </div>
      );
    }

    return (
      <div className="space-y-8">
        {/* Header con resultado */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-red-800 via-red-700 to-red-600">
          <div className="absolute inset-0 bg-black/10"></div>
          <div className="relative p-8 text-white">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold mb-2">Cotización Generada</h1>
                <p className="text-white/90 text-lg">
                  ID: {cotizacionActual.id_cotizacion}
                </p>
                <p className="text-white/70 text-sm">
                  Fecha:{" "}
                  {new Date(cotizacionActual.fecha_cotizacion).toLocaleString()}
                </p>
                <div className="mt-3 flex gap-3">
                  <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
                    {cotizacionActual.categoria_estilo}
                  </span>
                  <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
                    Esfuerzo: {cotizacionActual.categoria_esfuerzo}/10
                  </span>
                  <span className="px-3 py-1 bg-yellow-500/30 rounded-full text-sm font-semibold">
                    Versión:{" "}
                    {cotizacionActual.version_calculo_usada ||
                      cotizacionActual.inputs.version_calculo}
                  </span>
                  {cotizacionActual.volumen_historico && (
                    <span className="px-3 py-1 bg-green-500/30 rounded-full text-sm">
                      Volumen:{" "}
                      {cotizacionActual.volumen_historico.toLocaleString()}
                    </span>
                  )}
                </div>
              </div>
              <div className="text-right">
                <div className="bg-white/20 backdrop-blur-sm rounded-2xl p-6">
                  <div className="text-4xl font-bold mb-1">
                    ${(cotizacionActual.precio_final || 0).toFixed(2)}
                  </div>
                  <div className="text-white/90 text-lg">por prenda</div>
                  <div className="text-sm text-white/80 mt-2 px-3 py-1 bg-white/20 rounded-full">
                    Margen: {(cotizacionActual.margen_aplicado || 0).toFixed(1)}
                    %
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* OPs de referencia */}
        <ComponenteOpsReales />

        {/* DESGLOSE CORREGIDO */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="p-6 border-b border-gray-100 bg-red-800">
            <h2 className="text-xl font-bold flex items-center gap-3 text-white">
              <BarChart3 className="h-6 w-6" />
              Desglose Detallado de Costos
            </h2>
            <p className="text-white/80 mt-1">
              Análisis completo de componentes y factores de ajuste • Versión:{" "}
              {cotizacionActual.version_calculo_usada ||
                cotizacionActual.inputs.version_calculo}
            </p>
          </div>

          <div className="p-6">
            <div className="grid grid-cols-2 gap-8">
              {/* COMPONENTES AGRUPADOS CORRECTAMENTE */}
              <div>
                <h3 className="font-bold mb-4 text-red-500">
                  Componentes de Costo
                </h3>
                <div className="space-y-3">
                  {componentesAgrupados.map((comp, idx) => (
                    <div key={idx}>
                      <div className="flex justify-between items-center p-3 rounded-xl bg-orange-50">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-red-900">
                              {comp.nombre}
                            </span>
                            <span
                              className={`px-2 py-1 rounded-full text-xs font-semibold text-white ${
                                comp.fuente === "wip"
                                  ? "bg-red-600"
                                  : comp.fuente === "historico"
                                    ? "bg-red-500"
                                    : "bg-gray-500"
                              }`}
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
                        <span className="font-bold text-lg ml-4 text-red-900">
                          ${comp.costo_unitario.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  ))}

                  <div className="border-t-2 pt-3 mt-4 border-orange-400">
                    <div className="flex justify-between items-center font-bold text-lg p-3 rounded-xl bg-orange-200 text-red-900">
                      <span>Costo Base Total</span>
                      <span>
                        ${(cotizacionActual.costo_base_total || 0).toFixed(2)}
                      </span>
                    </div>
                  </div>

                  {/* NOTA SOBRE AJUSTES */}
                </div>
              </div>

              {/* Vector de ajuste */}
              <div>
                <h3 className="font-bold mb-4 text-red-500">
                  Vector de Ajuste
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 rounded-xl bg-orange-50">
                    <span className="font-semibold text-red-900">
                      Factor Lote ({cotizacionActual.inputs.categoria_lote})
                    </span>
                    <span className="font-bold text-red-500">
                      {(cotizacionActual.factor_lote || 1).toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 rounded-xl bg-orange-50">
                    <span className="font-semibold text-red-900">
                      Factor Esfuerzo (
                      {cotizacionActual.categoria_esfuerzo || 6}/10)
                    </span>
                    <span className="font-bold text-red-500">
                      {(cotizacionActual.factor_esfuerzo || 1).toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 rounded-xl bg-orange-50">
                    <span className="font-semibold text-red-900">
                      Factor Estilo (
                      {cotizacionActual.categoria_estilo || "Nuevo"})
                    </span>
                    <span className="font-bold text-red-500">
                      {(cotizacionActual.factor_estilo || 1).toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 rounded-xl bg-orange-50">
                    <span className="font-semibold text-red-900">
                      Factor Marca ({cotizacionActual.inputs.cliente_marca})
                    </span>
                    <span className="font-bold text-red-500">
                      {(cotizacionActual.factor_marca || 1).toFixed(2)}
                    </span>
                  </div>

                  <div className="border-t-2 pt-3 mt-4 border-orange-400">
                    <div className="flex justify-between items-center font-bold text-lg p-3 rounded-xl bg-orange-200 text-red-900">
                      <span>Vector Total</span>
                      <span>
                        {(cotizacionActual.vector_total || 1).toFixed(3)}
                      </span>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl text-center bg-red-500">
                    <div className="text-sm text-white/90 mb-1">
                      Precio Final
                    </div>
                    <div className="text-xl font-bold text-white">
                      ${(cotizacionActual.costo_base_total || 0).toFixed(2)} ×
                      (1 + 15% ×{" "}
                      {(cotizacionActual.vector_total || 1).toFixed(3)}) = $
                      {(cotizacionActual.precio_final || 0).toFixed(2)}
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
            className="px-8 py-3 font-semibold text-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 bg-red-500"
          >
            Nueva Cotización
          </button>

          <button
            onClick={() => window.print()}
            className="px-8 py-3 font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 flex items-center gap-2 bg-orange-50 text-red-900"
          >
            <Printer className="h-5 w-5" />
            Imprimir
          </button>

          <button
            onClick={() => {
              const data = JSON.stringify(cotizacionActual, null, 2);
              const blob = new Blob([data], { type: "application/json" });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = `cotizacion_${cotizacionActual.id_cotizacion}.json`;
              a.click();
            }}
            className="px-8 py-3 font-semibold text-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 flex items-center gap-2 bg-red-400"
          >
            <Download className="h-5 w-5" />
            Descargar
          </button>
        </div>
      </div>
    );
  });

  PantallaResultados.displayName = "PantallaResultados";

  // ========================================
  // 🎨 RENDER PRINCIPAL
  // ========================================

  return (
    <div className="min-h-screen p-6 bg-orange-50">
      <div className="max-w-7xl mx-auto">
        {/* Navegación */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 mb-8 overflow-hidden">
          <div className="flex">
            <button
              onClick={() => setPestanaActiva("formulario")}
              className={`px-8 py-4 font-bold transition-all duration-300 flex items-center gap-3 ${
                pestanaActiva === "formulario"
                  ? "text-white shadow-lg"
                  : "hover:shadow-md"
              }`}
              style={{
                backgroundColor:
                  pestanaActiva === "formulario" ? "#821417" : "transparent",
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
                pestanaActiva === "resultados"
                  ? "text-white shadow-lg"
                  : "hover:shadow-md"
              }`}
              style={{
                backgroundColor:
                  pestanaActiva === "resultados" ? "#821417" : "transparent",
                color: pestanaActiva === "resultados" ? "white" : "#bd4c42",
              }}
            >
              <BarChart3 className="h-5 w-5" />
              Resultados
            </button>

            <div className="ml-auto px-8 py-4 text-sm font-semibold flex items-center gap-2 text-red-500">
              <div className="w-2 h-2 rounded-full bg-red-500"></div>
              Sistema TDV - Metodología WIP-Based
              <span className="px-2 py-1 rounded bg-gray-100 text-xs font-bold uppercase">
                {formData.version_calculo}
              </span>
              {/* NUEVO: Debug en desarrollo */}
              {process.env.NODE_ENV === "development" && (
                <button
                  onClick={() => {
                    console.group("🔍 Debug Estado Sistema");
                    console.log("📝 FormData:", formData);
                    console.log("🎨 EstiloNuevo:", esEstiloNuevo);
                    console.log(
                      "🔍 EstilosEncontrados:",
                      estilosEncontrados.length,
                    );
                    console.log("⚙️ WIPs:", {
                      textiles: wipsTextiles.length,
                      manufactura: wipsManufactura.length,
                    });
                    console.log("📊 Datos:", {
                      familias: familiasDisponibles.length,
                      tipos: tiposDisponibles.length,
                    });
                    console.log("💰 Cotización:", !!cotizacionActual);
                    console.groupEnd();
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
  );
};

export default SistemaCotizadorTDV;
