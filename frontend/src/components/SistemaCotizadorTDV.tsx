"use client";

import React, {
  useState,
  useEffect,
  useCallback,
  useRef,
  useMemo,
} from "react";
import { get, post } from "@/libs/api";
import {
  DollarSign,
  Package,
  BarChart3,
  FileText,
  Download,
  Printer,
  RefreshCw,
  Database,
  Search,
  Layers,
} from "lucide-react";
import { OpsSelectionTable } from "./OpsSelectionTable";
import { WipDesgloseTable, WipDesgloseTableRef } from "./WipDesgloseTable";
import { HilosDesgloseTable, HilosDesgloseTableRef } from "./HilosDesgloseTable";
import { AviosDesgloseTable, AviosDesgloseTableRef } from "./AviosDesgloseTable";
import { TelasDesgloseTable, TelasDesgloseTableRef } from "./TelasDesgloseTable";

// Constantes del sistema
const CATEGORIAS_LOTE = {
  "Micro Lote": { rango: "1-50" },
  "Lote Pequeño": { rango: "51-500" },
  "Lote Mediano": { rango: "501-1000" },
  "Lote Grande": { rango: "1001-4000" },
  "Lote Masivo": { rango: "4001+" },
};

// NOTA: InputCodigoEstiloProps removido - no se usa más

// ✨ INPUT HTML PURO - ESTADO LOCAL para evitar pérdida de foco
const PureInputCodigoEstilo: React.FC<{ value?: string; onChange: (valor: string) => void }> = ({
  value: externalValue,
  onChange,
}) => {
  // Estado local del input - Se actualiza INMEDIATAMENTE sin depender de re-renders del padre
  const [localValue, setLocalValue] = useState<string>(externalValue || "");

  // ⚡ SOLO sincronizar cuando viene un valor externo IMPORTANTE (búsqueda exitosa, no estado de botón)
  // Usar un ref para detectar si el valor externo cambió SIGNIFICATIVAMENTE
  const prevExternalValueRef = useRef<string>(externalValue || "");

  useEffect(() => {
    // ✨ Sincronizar cuando el valor externo cambió (incluyendo cadenas vacías para limpiar)
    // Comparar sin la condición "truthy" para permitir limpiar el campo
    if (externalValue !== prevExternalValueRef.current) {
      prevExternalValueRef.current = externalValue || "";
      setLocalValue(externalValue || "");
    }
  }, [externalValue]);

  // ⚡ Handler interno - Sin transformación en keystroke
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    // 1. Actualizar estado local INMEDIATAMENTE (el input lo verá al instante)
    setLocalValue(newValue);
    // 2. Reportar al padre (sin transformación)
    onChange(newValue);
  };

  return (
    <input
      type="text"
      value={localValue}  // ✅ Usa estado LOCAL, no prop del padre
      onChange={handleChange}
      className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-red-500 focus:border-opacity-50 transition-colors"
      placeholder="ej: LAC001-V25, GRY2024-P01"
      autoComplete="off"
      spellCheck={false}
    />
  );
};

// ✨ v2.0: INPUT HTML PURO para Estilo Cliente - ESTADO LOCAL para evitar pérdida de foco
const PureInputEstiloCliente: React.FC<{ value?: string; onChange: (valor: string) => void }> = ({
  value: externalValue,
  onChange,
}) => {
  const [localValue, setLocalValue] = useState<string>(externalValue || "");
  const prevExternalValueRef = useRef<string>(externalValue || "");

  useEffect(() => {
    // ✨ Sincronizar también cuando recibe cadena vacía (para limpiar el campo)
    console.log(`🔄 PureInputEstiloCliente sync: external="${externalValue}" vs prev="${prevExternalValueRef.current}"`);
    if (externalValue !== prevExternalValueRef.current) {
      console.log(`✅ Sincronizando: setLocalValue("${externalValue || ""}")`);
      prevExternalValueRef.current = externalValue || "";
      setLocalValue(externalValue || "");
    }
  }, [externalValue]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setLocalValue(newValue);
    onChange(newValue);
  };

  return (
    <input
      type="text"
      value={localValue}
      onChange={handleChange}
      className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-red-500 focus:border-opacity-50 transition-colors"
      placeholder="ej: LAC001-V25, GRY2024-P01"
      autoComplete="off"
      spellCheck={false}
    />
  );
};

// Botón de búsqueda - SIN MEMO (ICONO DE LUPA)
const BuscarEstiloButton: React.FC<{
  value: string;
  buscandoEstilo: boolean;
  onBuscar: () => void;
}> = ({ value, buscandoEstilo, onBuscar }) => (
  <button
    type="button"
    onClick={onBuscar}
    disabled={buscandoEstilo || value.length < 5}
    className="mt-2 w-full py-3 px-4 bg-red-700 hover:bg-red-800 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
    title={value.length < 5 ? "Ingresa al menos 5 caracteres" : "Buscar estilo"}
  >
    {buscandoEstilo ? (
      <>
        <RefreshCw className="h-5 w-5 animate-spin" />
        <span>Buscando...</span>
      </>
    ) : (
      <>
        <Search className="h-5 w-5" />
        <span>Buscar</span>
      </>
    )}
  </button>
);

// v2.0: Botón de búsqueda para Estilo Cliente - SIN MEMO (ICONO DE LUPA)
const BuscarEstiloClienteButton: React.FC<{
  value: string;
  buscandoEstilo: boolean;
  onBuscar: () => void;
}> = ({ value, buscandoEstilo, onBuscar }) => (
  <button
    type="button"
    onClick={onBuscar}
    disabled={buscandoEstilo || value.length === 0}
    className="mt-2 w-full py-3 px-4 bg-red-700 hover:bg-red-800 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
    title={value.length === 0 ? "Ingresa un código de estilo" : "Buscar estilo cliente"}
  >
    {buscandoEstilo ? (
      <>
        <RefreshCw className="h-5 w-5 animate-spin" />
        <span>Buscando...</span>
      </>
    ) : (
      <>
        <Search className="h-5 w-5" />
        <span>Buscar</span>
      </>
    )}
  </button>
);

// Componente CampoCodigoEstilo completo como React.memo - evita que se remonte en cada keystroke
interface CampoCodigoEstiloProps {
  value: string;
  buscandoEstilo: boolean;
  estilosEncontrados: any[];
  esEstiloNuevo: boolean | null;
  infoAutoCompletado: any;
  onChange: (valor: string) => void;
  onBuscar: () => void;
  onSelectStyle: (estilo: any) => void;
}

// Información de auto-completado - Componente separado para no afectar el input
interface InfoAutocompletadoComponentProps {
  infoAutoCompletado: AutoCompletadoInfo | null;
}

const InfoAutocompletadoComponent = React.memo(
  ({ infoAutoCompletado }: InfoAutocompletadoComponentProps) => {
    if (!infoAutoCompletado?.autocompletado_disponible) return null;

    return (
      <div className="mt-2 p-3 rounded-xl border-2 bg-green-100 border-green-400">
        <div className="text-sm font-semibold mb-2 text-green-700">
          ✅ Auto-completado:
        </div>
        <div className="text-xs text-green-700">
          📁 {infoAutoCompletado.campos_sugeridos?.familia_producto} | 🏷️{" "}
          {infoAutoCompletado.campos_sugeridos?.tipo_prenda}
        </div>
      </div>
    );
  }
);
InfoAutocompletadoComponent.displayName = "InfoAutocompletadoComponent";

// Estado del estilo - Componente separado
interface EstadoEstiloComponentProps {
  esEstiloNuevo: boolean | null;
  buscandoEstilo: boolean;
  value: string;
  infoAutoCompletado: AutoCompletadoInfo | null;
}

const EstadoEstiloComponent = React.memo(
  ({ esEstiloNuevo, buscandoEstilo, value, infoAutoCompletado }: EstadoEstiloComponentProps) => {
    if (!value || buscandoEstilo || esEstiloNuevo === null) return null;

    return (
      <div className="flex items-center gap-2 mt-2">
        <div
          className={`text-xs px-2 py-1 rounded-full inline-block text-white ${
            esEstiloNuevo ? "bg-red-500" : "bg-green-600"
          }`}
        >
          {esEstiloNuevo ? "🆕 Nuevo" : "✅ Recurrente"}
        </div>

        {infoAutoCompletado?.info_estilo?.volumen_total && (
          <div className="text-xs text-gray-600">
            📦 {infoAutoCompletado.info_estilo.volumen_total.toLocaleString()} prendas
          </div>
        )}
      </div>
    );
  }
);
EstadoEstiloComponent.displayName = "EstadoEstiloComponent";

// ✨ v2.0: Componente de estado para Estilo Cliente - Muestra badge Nuevo/Recurrente
interface EstadoEstiloClienteComponentProps {
  esEstiloClienteNuevo: boolean | null;
  buscandoEstilo: boolean;
  value: string;
}

const EstadoEstiloClienteComponent = React.memo(
  ({ esEstiloClienteNuevo, buscandoEstilo, value }: EstadoEstiloClienteComponentProps) => {
    if (!value || buscandoEstilo || esEstiloClienteNuevo === null) return null;

    return (
      <div className="mt-3 inline-block">
        <div
          className={`px-4 py-2 rounded-full text-white text-sm font-bold ${
            esEstiloClienteNuevo ? "bg-red-500" : "bg-green-600"
          }`}
        >
          {esEstiloClienteNuevo ? "🆕 Nuevo" : "✅ Recurrente"}
        </div>
      </div>
    );
  }
);

EstadoEstiloClienteComponent.displayName = "EstadoEstiloClienteComponent";

// Estilos similares - Componente separado
interface EstilosSimilaresComponentProps {
  estilosEncontrados: EstiloSimilar[];
  onSelectStyle: (estilo: EstiloSimilar) => void;
}

const EstilosSimilaresComponent = React.memo(
  ({ estilosEncontrados, onSelectStyle }: EstilosSimilaresComponentProps) => {
    if (estilosEncontrados.length === 0) return null;

    return (
      <div className="mt-2 p-3 rounded-xl border-2 bg-orange-50 border-orange-400">
        <div className="text-sm font-semibold mb-2 text-red-900">
          Estilos similares:
        </div>
        {estilosEncontrados.slice(0, 3).map((estilo, idx) => (
          <button
            key={idx}
            onClick={() => onSelectStyle(estilo)}
            className="w-full text-left p-2 rounded-lg hover:shadow-md transition-all mb-2 bg-orange-200"
          >
            <div className="font-semibold text-sm text-red-900">
              {estilo.codigo}
            </div>
            <div className="text-xs text-red-500">
              {estilo.tipo_prenda} | {estilo.ops_encontradas} OPs
            </div>
          </button>
        ))}
      </div>
    );
  }
);
EstilosSimilaresComponent.displayName = "EstilosSimilaresComponent";

// ⚡ COMPONENTE MEMOIZADO con comparación personalizada para evitar re-renders innecesarios
const CampoCodigoEstiloComponent = React.memo<CampoCodigoEstiloProps>(
  ({
    value,
    buscandoEstilo,
    estilosEncontrados,
    esEstiloNuevo,
    infoAutoCompletado,
    onChange,
    onBuscar,
    onSelectStyle,
  }) => {
    return (
      <div className="space-y-2">
        <label className="block text-sm font-semibold text-red-900">Código de estilo propio</label>

        {/* Input puro - SIN MEMO */}
        <PureInputCodigoEstilo value={value} onChange={onChange} />

        {/* Botón de búsqueda - SIN MEMO */}
        <BuscarEstiloButton value={value} buscandoEstilo={buscandoEstilo} onBuscar={onBuscar} />

        {/* Información - componentes memoizados separados */}
        <InfoAutocompletadoComponent infoAutoCompletado={infoAutoCompletado} />
        <EstadoEstiloComponent
          esEstiloNuevo={esEstiloNuevo}
          buscandoEstilo={buscandoEstilo}
          value={value}
          infoAutoCompletado={infoAutoCompletado}
        />
        <EstilosSimilaresComponent
          estilosEncontrados={estilosEncontrados}
          onSelectStyle={onSelectStyle}
        />
      </div>
    );
  },
  // Función de comparación personalizada: solo re-renderizar si cambió algo relevante
  (prevProps: CampoCodigoEstiloProps, nextProps: CampoCodigoEstiloProps) => {
    return (
      prevProps.value === nextProps.value &&
      prevProps.buscandoEstilo === nextProps.buscandoEstilo &&
      prevProps.estilosEncontrados === nextProps.estilosEncontrados &&
      prevProps.esEstiloNuevo === nextProps.esEstiloNuevo &&
      prevProps.infoAutoCompletado === nextProps.infoAutoCompletado
    );
  }
);

CampoCodigoEstiloComponent.displayName = "CampoCodigoEstiloComponent";

// ✨ v2.0: COMPONENTE MEMOIZADO para Estilo Cliente (usa misma lógica de búsqueda que estilo_propio)
interface CampoEstiloClienteProps {
  value: string;
  buscandoEstilo: boolean;
  infoAutoCompletadoCliente: any;
  esEstiloClienteNuevo: boolean | null;
  onChange: (valor: string) => void;
  onBuscar: () => void;
}

const CampoEstiloClienteComponent = React.memo<CampoEstiloClienteProps>(
  ({
    value,
    buscandoEstilo,
    infoAutoCompletadoCliente,
    esEstiloClienteNuevo,
    onChange,
    onBuscar,
  }) => {
    return (
      <div className="space-y-2">
        <label className="block text-sm font-semibold text-red-900">Código de Estilo Cliente</label>

        {/* Input puro - SIN MEMO */}
        <PureInputEstiloCliente value={value} onChange={onChange} />

        {/* Botón de búsqueda - SIN MEMO */}
        <BuscarEstiloClienteButton value={value} buscandoEstilo={buscandoEstilo} onBuscar={onBuscar} />

        {/* ✨ Estado del estilo cliente (Nuevo/Recurrente) */}
        <EstadoEstiloClienteComponent
          esEstiloClienteNuevo={esEstiloClienteNuevo}
          buscandoEstilo={buscandoEstilo}
          value={value}
        />

        {/* Información de auto-completado si está disponible */}
        {infoAutoCompletadoCliente?.autocompletado_disponible && (
          <div className="mt-2 p-3 rounded-xl border-2 bg-green-100 border-green-400">
            <div className="text-sm font-semibold mb-2 text-green-700">
              ✅ Auto-completado:
            </div>
            <div className="text-xs text-green-700">
              📁 {infoAutoCompletadoCliente.campos_sugeridos?.familia_producto} | 🏷️{" "}
              {infoAutoCompletadoCliente.campos_sugeridos?.tipo_prenda}
            </div>
          </div>
        )}
      </div>
    );
  },
  (prevProps: CampoEstiloClienteProps, nextProps: CampoEstiloClienteProps) => {
    return (
      prevProps.value === nextProps.value &&
      prevProps.buscandoEstilo === nextProps.buscandoEstilo &&
      prevProps.infoAutoCompletadoCliente === nextProps.infoAutoCompletadoCliente &&
      prevProps.esEstiloClienteNuevo === nextProps.esEstiloClienteNuevo
    );
  }
);

CampoEstiloClienteComponent.displayName = "CampoEstiloClienteComponent";

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
// NOTA: EstiloClienteInput fue reemplazado por CampoEstiloClienteComponent

// Categoría de Lote select (DEPRECATED v2.0, se mantiene para compatibilidad)
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
// NOTA: WipDisponible removido - no se usa más

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
  estilo_cliente: string; // v2.0: Búsqueda principal
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
  costo_hilos_materia_prima?: number; // ✨ Materia Prima Hilos (separado)
  costo_telas_compradas?: number; // ✨ Tela Comprada (separado)
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
    "formulario" | "resultados" | "materiales" | "costos"
  >("formulario");
  const [cotizacionActual, setCotizacionActual] =
    useState<ResultadoCotizacion | null>(null);
  const [cargando, setCargando] = useState(false);

  // Estados de datos maestros dinámicos
  const [clientesDisponibles, setClientesDisponibles] = useState<string[]>([]);
    const [tiposDisponibles, setTiposDisponibles] = useState<string[]>([]);
  const [cargandoTipos, setCargandoTipos] = useState(false);

  // Estado para OPs seleccionadas en la tabla interactiva
  const [selectedOpsCode, setSelectedOpsCode] = useState<string[]>([]);
  const [selectedOpsData, setSelectedOpsData] = useState<any[]>([]); // ✨ Guardar datos completos de las OPs
  const formDataRef = useRef<FormData | null>(null); // ✨ Mantiene formData actual sin affecting dependencies
  const wipDesgloseTableRef = useRef<WipDesgloseTableRef>(null); // ✨ Ref para acceder a WIPs seleccionados
  const selectedWipsRef = useRef<string[]>([]); // ✨ Mantener WIPs seleccionados en ref para persistencia visual
  const hilosDesgloseTableRef = useRef<HilosDesgloseTableRef>(null); // ✨ Ref para acceder a Hilos seleccionados
  const aviosDesgloseTableRef = useRef<AviosDesgloseTableRef>(null); // ✨ Ref para acceder a Avios seleccionados
  const telasDesgloseTableRef = useRef<TelasDesgloseTableRef>(null); // ✨ Ref para acceder a Telas seleccionadas

  // Estados para costos calculados del WIP (para sobrescribir backend values)
  const [costosWipCalculados, setCostosWipCalculados] = useState<{
    textil_por_prenda: number | null;
    manufactura_por_prenda: number | null;
  }>({
    textil_por_prenda: null,
    manufactura_por_prenda: null,
  });

  // ✨ Estado para factores de ajuste WIP - PERSISTENTE entre pestañas
  const [factoresWip, setFactoresWip] = useState<Record<string, number>>({});


  // ✨ Estados para guardar costos calculados de materiales (para usar en Costos Finales)
  const [costosMaterialesFinales, setCostosMaterialesFinales] = useState<{
    costo_materia_prima: number;
    costo_avios: number;
    costo_hilos_materia_prima?: number;
    costo_telas_compradas?: number;
  } | null>(null);

  // ✨ Estado para controlar si la pestaña de Costos Finales debe estar habilitada
  // Solo se habilita después de hacer clic en "Calcular Costos Finales"
  const [costosFinalCalculados, setCostosFinalCalculados] = useState(false);

  // Estados para formulario - separados para evitar pérdida de foco
  const [formData, setFormData] = useState<FormData>({
    estilo_cliente: "", // v2.0: Código de estilo cliente
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

  // ⚡ REF LOCAL DEL INPUT (NO useState) - Esto evita re-renders del padre en cada keystroke
  // El input se mantiene controlado pero los cambios NO disparan renders
  const codigoEstiloLocalRef = useRef<string>("");
  const estiloClienteLocalRef = useRef<string>("");

  // ⚡ Ref adicional para almacenar el valor actual del input de estilo cliente (para búsqueda)
  const estiloClienteInputRef = useRef<string>("");

  // Estado para forzar un render SOLO cuando es necesario (búsqueda, validación, etc)
  const [codigoEstiloForceRender, setCodigoEstiloForceRender] = useState<string>("");
  const [estiloClienteForceRender, setEstiloClienteForceRender] = useState<string>("");

  // ⚡ Estado para controlar si el input ha sido sincronizado (evita loops)
  const inputSyncedRef = useRef<boolean>(false);
  const estiloClienteSyncedRef = useRef<boolean>(false);

  // Estados para búsqueda de estilos
  const [estilosEncontrados, setEstilosEncontrados] = useState<EstiloSimilar[]>(
    [],
  );
  const [buscandoEstilo, setBuscandoEstilo] = useState(false);
  const [esEstiloNuevo, setEsEstiloNuevo] = useState<boolean | null>(null);

  const [infoAutoCompletado, setInfoAutoCompletado] =
    useState<AutoCompletadoInfo | null>(null);

  // v2.0: Estados para búsqueda de estilo_cliente (reutiliza misma función, diferentes estados)
  const [infoAutoCompletadoCliente, setInfoAutoCompletadoCliente] =
    useState<AutoCompletadoInfo | null>(null);
  const [esEstiloClienteNuevo, setEsEstiloClienteNuevo] = useState<boolean | null>(null);

  // Estados para WIPs seleccionadas
  const [wipsTextiles] = useState<WipSeleccionada[]>([]);
  const [wipsManufactura] = useState<WipSeleccionada[]>([]);

  // Referencias para evitar re-renders y debouncing
  const abortControllerRef = useRef<AbortController | null>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null); // ✨ Para debounce de Estilo Cliente

  // Sincronizar formDataRef con formData
  React.useEffect(() => {
    formDataRef.current = formData;
  }, [formData]);

  // ✨ Cleanup: Limpiar debounce timer cuando el componente se desmonta
  React.useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  // Memoized validation
  const erroresFormulario = useMemo(() => {
    const errores = [];

    if (!formData.cliente_marca) errores.push("Cliente/Marca es requerido");
    // NOTA: temporada y familia_producto ya no son requeridas
    if (!formData.tipo_prenda) errores.push("Tipo de Prenda es requerido");

    // ✨ v2.0: Validación UNO U OTRO - Estilo Cliente OR Estilo Propio
    const tieneEstiloCliente = estiloClienteInputRef.current.trim().length > 0;
    const tieneEstiloPropio = codigoEstiloLocalRef.current.trim().length > 0;

    if (!tieneEstiloCliente && !tieneEstiloPropio) {
      errores.push("Ingresa Estilo Cliente O Estilo Propio (uno es suficiente)");
    }

    // NOTA: Se removió validación de WIPs requeridas - ahora es opcional

    return errores;
  }, [formData.cliente_marca, formData.tipo_prenda, formData.codigo_estilo]);

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

  // ⚡ Handler para código de estilo - SOLO ESTADO LOCAL, sin tocar formData
  // Esto evita re-renders del padre en cada keystroke
  const handleCodigoEstiloChange = useCallback(
    (valor: string) => {
      // ⚡ USAR REF EN LUGAR DE ESTADO - Esto evita re-renders del padre
      codigoEstiloLocalRef.current = valor;
      inputSyncedRef.current = false; // Marcar como no sincronizado

      // ✨ DEBOUNCE: Solo hacer setState después de 500ms sin cambios
      // Limpiar timeout anterior
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      // Crear nuevo timeout
      debounceTimerRef.current = setTimeout(() => {
        // ✅ Forzar un render MÍNIMO cuando el usuario escriba 5+ caracteres
        // o cuando está vacío (para desactivar botón)
        if (valor.length >= 5 || valor.length === 0) {
          console.log(`⏱️ Debounce completado: actualizando ForceRender a "${valor}"`);
          setCodigoEstiloForceRender(valor);
        }
      }, 1000); // 1 segundo de debounce
    },
    [],  // Sin dependencias - nunca cambia
  );

  const handleTipoPrendaChange = useCallback(
    (valor: string) => {
      manejarCambioFormulario("tipo_prenda", valor);
    },
    [manejarCambioFormulario],
  );

  const handleClienteChange = useCallback(
    (valor: string) => {
      manejarCambioFormulario("cliente_marca", valor);
    },
    [manejarCambioFormulario],
  );

  // v2.0: Handler para estilo_cliente - SOLO ESTADO LOCAL, sin tocar formData
  const handleEstiloClienteChange = useCallback(
    (valor: string) => {
      // ✨ Actualizar inmediatamente en refs (sin setState, mantiene el foco)
      estiloClienteLocalRef.current = valor;
      estiloClienteInputRef.current = valor;
      estiloClienteSyncedRef.current = false;

      // ✨ DEBOUNCE: Solo hacer setState después de 500ms sin cambios
      // Limpiar timeout anterior
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      // Crear nuevo timeout
      debounceTimerRef.current = setTimeout(() => {
        // Actualizar UI solo cuando el usuario deja de escribir
        if (valor.length >= 3 || valor.length === 0) {
          console.log(`⏱️ Debounce completado: actualizando ForceRender a "${valor}"`);
          setEstiloClienteForceRender(valor);
        }
      }, 1000); // 1 segundo de debounce
    },
    [],
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

  // Callback para OPs seleccionadas - SOLO SETEA, SIN CALCULAR
  // Manejar OPs seleccionadas desde OpsSelectionTable
  const handleOpsSelected = useCallback((opsSeleccionadas: any[]) => {
    const codOrdpros = opsSeleccionadas.map((op) => op.cod_ordpro);
    setSelectedOpsCode(codOrdpros);
    setSelectedOpsData(opsSeleccionadas); // ✨ Guardar datos completos para cálculo posterior
    // 🔍 DEBUG: Mostrar OPs seleccionadas con sus esfuerzo values
    console.log(`📊 OPs Seleccionadas (${opsSeleccionadas.length}):`, opsSeleccionadas.map(op => ({
      cod: op.cod_ordpro,
      esfuerzo: op.esfuerzo_total,
      prendas: op.prendas_requeridas,
      cliente: op.cliente
    })));
    setFormData((prev) => ({
      ...prev,
      cod_ordpros: codOrdpros,
    }));
  }, []);

  // NOTA: Efecto 3 (cargar WIPs cuando cambia tipo) fue eliminado - cargarWipsPorTipoPrenda removido

  // ⚡ DESHABILITADO - Este efecto causaba re-renders en cada keystroke
  // La limpieza se maneja solo cuando se busca explícitamente o cuando formData cambia
  // useEffect(() => {
  //   if (!codigoEstiloLocal || codigoEstiloLocal.length < 3) {
  //     setEstilosEncontrados([]);
  //     setEsEstiloNuevo(null);
  //     setInfoAutoCompletado(null);
  //   }
  // }, [codigoEstiloLocal]);

  // Cargar datos iniciales - OPTIMIZADO: Un único request en lugar de 3
  useEffect(() => {
    const cargarDatosIniciales = async () => {
      try {
        const data = await get<{
          clientes: string[];
          tipos: string[];
          wips: Record<string, any>;
          total_clientes: number;
          total_tipos: number;
          total_wips: number;
        }>("inicializar?version_calculo=FLUIDO");

        // Desempaquetar todos los datos en los estados correspondientes
        setClientesDisponibles(data.clientes || []);
        setTiposDisponibles(data.tipos || []);


        // console.log(
        //   `✅ Datos iniciales cargados: ${data.total_clientes} clientes, ${data.total_tipos} tipos, ${data.total_wips} WIPs`
        // );
      } catch {
        // console.error("Error cargando datos iniciales:", error);
        setClientesDisponibles([]);
        setTiposDisponibles([]);

      }
    };
    cargarDatosIniciales();
  }, []); // Solo una vez al montar

  // Limpiar al desmontar
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Actualizar formDataRef cuando cambia formData (sin afectar otros effects)
  useEffect(() => {
    formDataRef.current = formData;
  }, [formData]);

  // ⚡ DESHABILITADO - Este efecto causaba pérdida de foco al crear/limpiar timers constantemente
  // El debounce ahora se maneja solo cuando se hace click en "Buscar Estilo"
  // useEffect(() => {
  //   const timer = setTimeout(() => {
  //     setDebouncedFormData(formDataRef.current);
  //   }, 3000);
  //   return () => {
  //     clearTimeout(timer);
  //   };
  // }, [formData.codigo_estilo]);

  // ========================================
  // 🔧 FUNCIONES DE CARGA CORREGIDAS
  // ========================================

  // NOTA: cargarWipsPorTipoPrenda removido - no se usa más en el flujo actual

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

  // NOTA: cargarFamiliasProductos y cargarTiposPrenda removidos - no se usan más

  // Cargar TODOS los tipos de prenda (sin filtrar por familia)
  const cargarTodosTipos = useCallback(
    async (versionCalculo: string = "FLUIDO") => {
      setCargandoTipos(true);
      try {
        // Obtener todas las familias primero
        const familiasData = await get<{ familias: string[] }>(
          `tipos-prenda?version_calculo=${encodeURIComponent(versionCalculo)}`,
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
          cargarClientesDisponibles(debouncedFormData.version_calculo),
          cargarTodosTipos(debouncedFormData.version_calculo), // ✅ Cargar TODOS los tipos
        ]);
      } catch {
        // Silenciar errores de carga
      }
    };

    recargarDatosVersion();
  }, [debouncedFormData.version_calculo, cargarTodosTipos, cargarClientesDisponibles]); // Usa debouncedFormData para evitar actualizaciones frecuentes

  // NOTA: Efecto 2 (cargar tipos cuando cambia familia) fue eliminado
  // Ahora se cargan TODOS los tipos al iniciar (cargarTodosTipos) para que estilos nuevos puedan seleccionar tipo_prenda

  // ✨ Función GENÉRICA para verificar y buscar estilos (funciona para estilo_propio y estilo_cliente)
  const verificarYBuscarEstilo = useCallback(
    async (
      codigo: string,
      versionCalculo: string,
      tipo: 'estilo_propio' | 'estilo_cliente' = 'estilo_propio',
      cliente?: string
    ) => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Validar longitud mínima según tipo
      const minLength = tipo === 'estilo_cliente' ? 3 : 5;
      if (!codigo || codigo.length < minLength) {
        if (tipo === 'estilo_propio') {
          setEstilosEncontrados([]);
          setEsEstiloNuevo(true);
          setInfoAutoCompletado(null);
        } else {
          setInfoAutoCompletadoCliente(null);
        }
        return;
      }

      setBuscandoEstilo(true);
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      // ✨ v2.0: Endpoint genérico que maneja ambos tipos
      const endpoint = `verificar-estilo/${encodeURIComponent(codigo)}?tipo=${encodeURIComponent(tipo)}&version_calculo=${encodeURIComponent(versionCalculo)}`;

      try {
        const verificacion = await get<any>(endpoint, { signal: abortController.signal });

        if (!abortController.signal.aborted) {
          if (tipo === 'estilo_propio') {
            // Lógica para estilo propio
            const esNuevo = verificacion.es_estilo_nuevo;
            setEsEstiloNuevo(esNuevo);

            if (!esNuevo && verificacion.autocompletado?.disponible) {
              const { tipo_prenda, cliente_principal } = verificacion.autocompletado;
              if (tipo_prenda) {
                setFormData((prev) => ({
                  ...prev,
                  tipo_prenda,
                  // ✨ v2.0: También auto-completar cliente_marca para estilo_propio
                  cliente_marca: cliente_principal || prev.cliente_marca,
                }));

                setDebouncedFormData((prev) => ({
                  ...prev,
                  tipo_prenda,
                }));

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

            // Buscar estilos similares solo para estilo_propio
            if (cliente) {
              const estilos = await get<any[]>(
                `buscar-estilos/${encodeURIComponent(codigo)}?cliente=${encodeURIComponent(cliente)}&limite=10&version_calculo=${encodeURIComponent(versionCalculo)}`,
                { signal: abortController.signal },
              );
              if (!abortController.signal.aborted) {
                setEstilosEncontrados(estilos);
              }
            }
          } else {
            // Lógica para estilo_cliente (v2.0)
            // ✨ Capturar es_estilo_nuevo del backend
            const esClienteNuevo = verificacion.es_estilo_nuevo;
            setEsEstiloClienteNuevo(esClienteNuevo);

            if (verificacion && verificacion.autocompletado?.disponible) {
              const { tipo_prenda, cliente_principal, familia_producto } = verificacion.autocompletado;

              // Auto-completar tipo_prenda y cliente_marca
              if (tipo_prenda) {
                setFormData((prev) => ({
                  ...prev,
                  tipo_prenda,
                  cliente_marca: cliente_principal || prev.cliente_marca, // v2.0: Auto-completa cliente_marca
                }));

                setTiposDisponibles((prev) => {
                  if (!prev.includes(tipo_prenda)) {
                    return [...prev, tipo_prenda];
                  }
                  return prev;
                });
              }

              setInfoAutoCompletadoCliente({
                autocompletado_disponible: true,
                info_estilo: {
                  tipo_prenda,
                  familia_producto,
                  categoria: verificacion.categoria,
                  volumen_total: verificacion.volumen_historico,
                },
                campos_sugeridos: { tipo_prenda, familia_producto },
              });
            } else {
              setInfoAutoCompletadoCliente(null);
            }
          }
        }
      } catch (error: any) {
        if (error.name !== "AbortError") {
          if (tipo === 'estilo_propio') {
            setEstilosEncontrados([]);
            setEsEstiloNuevo(true);
            setInfoAutoCompletado(null);
          } else {
            setEsEstiloClienteNuevo(null); // ✨ Limpiar en caso de error
            setInfoAutoCompletadoCliente(null);
          }
        }
      } finally {
        if (!abortController.signal.aborted) {
          setBuscandoEstilo(false);
        }
      }
    },
    [],
  );

  // ✨ Handler para buscar estilo propio
  const onBuscarEstilo = useCallback(() => {
    const codigoActual = codigoEstiloLocalRef.current.toUpperCase().trim();
    if (codigoActual && codigoActual.length >= 5) {
      inputSyncedRef.current = true;
      setFormData(prev => ({
        ...prev,
        codigo_estilo: codigoActual,
        estilo_cliente: "" // ✨ Limpiar también en formData
      }));

      setEstilosEncontrados([]);
      setEsEstiloNuevo(null);
      setInfoAutoCompletado(null);

      // ✨ v2.0: Limpiar completamente estilo cliente (valor + visualización + refs)
      console.log(`🧹 Limpiando Estilo Cliente desde onBuscarEstilo`);
      estiloClienteInputRef.current = "";
      estiloClienteLocalRef.current = ""; // ✨ IMPORTANTE: Limpiar también este ref
      estiloClienteSyncedRef.current = false; // Reset sync flag
      setEstiloClienteForceRender(""); // ✨ Esto dispara re-render y actualiza externalValue
      setEsEstiloClienteNuevo(null); // ✨ Limpiar estado de estilo cliente nuevo
      setInfoAutoCompletadoCliente(null);
      console.log(`✅ Estilo Cliente limpiado`);

      verificarYBuscarEstilo(
        codigoActual,
        formData.version_calculo,
        'estilo_propio',
        formData.cliente_marca
      );
    }
  }, [formData.cliente_marca, formData.version_calculo, verificarYBuscarEstilo]);

  // ✨ Handler para buscar estilo cliente (v2.0)
  const onBuscarEstiloCliente = useCallback(() => {
    const estiloClienteActual = estiloClienteInputRef.current.toUpperCase().trim();
    if (estiloClienteActual && estiloClienteActual.length >= 3) {
      estiloClienteSyncedRef.current = true;
      setFormData(prev => ({
        ...prev,
        estilo_cliente: estiloClienteActual,
        codigo_estilo: "" // ✨ Limpiar también en formData
      }));

      setInfoAutoCompletadoCliente(null);

      // ✨ v2.0: Limpiar completamente estilo propio (valor + visualización)
      codigoEstiloLocalRef.current = "";
      inputSyncedRef.current = false; // Reset sync flag
      setCodigoEstiloForceRender("");
      setEstilosEncontrados([]);
      setEsEstiloNuevo(null);
      setEsEstiloClienteNuevo(null); // ✨ Limpiar estado de estilo cliente nuevo
      setInfoAutoCompletado(null);

      verificarYBuscarEstilo(
        estiloClienteActual,
        formData.version_calculo,
        'estilo_cliente'
      );
    }
  }, [formData.version_calculo, verificarYBuscarEstilo]);

  // cargarOpsReales (POST)
  const cargarOpsReales = useCallback(
    async (cotizacion: ResultadoCotizacion) => {
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

        await post<any>(
          "/ops-utilizadas-cotizacion",
          payload,
        );
        // console.log(
        //   `✅ OPs reales cargadas`,
        // );
      } catch {
        // console.error("Error cargando OPs reales");
        // Error handling for ops is handled in the parent component
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

  // NOTA: toggleWipTextil, toggleWipManufactura, actualizarFactorWip removidos - no se usan más

  const procesarCotizacion = useCallback(async () => {
    setCargando(true);
    try {
      // ✨ v2.0: Obtener valores actuales de ambos inputs
      const codigoEstiloActual = codigoEstiloLocalRef.current.toUpperCase().trim();
      const estiloClienteActual = estiloClienteInputRef.current.toUpperCase().trim();

      // Sincronizar a formData si es necesario
      if (!inputSyncedRef.current && codigoEstiloActual) {
        setFormData(prev => ({
          ...prev,
          codigo_estilo: codigoEstiloActual
        }));
        inputSyncedRef.current = true;
      }

      if (!estiloClienteSyncedRef.current && estiloClienteActual) {
        setFormData(prev => ({
          ...prev,
          estilo_cliente: estiloClienteActual
        }));
        estiloClienteSyncedRef.current = true;
      }

      // ✨ v2.0: Calcular esfuerzo promedio de OPs seleccionadas
      let esforzoPromedio = 6; // Default
      console.log(`🔍 DEBUG COTIZACIÓN:`);
      console.log(`   selectedOpsCode: ${JSON.stringify(selectedOpsCode)}`);
      console.log(`   selectedOpsData length: ${selectedOpsData?.length || 0}`);
      if (selectedOpsData && selectedOpsData.length > 0) {
        const totalEsfuerzo = selectedOpsData.reduce((sum, op) => sum + (op.esfuerzo_total || 6), 0);
        esforzoPromedio = Math.round(totalEsfuerzo / selectedOpsData.length);
        console.log(`✅ Esfuerzo Promedio: ${esforzoPromedio} (${selectedOpsData.length} OPs seleccionadas)`);
        console.log(`📝 Detalles OPs:`, selectedOpsData.map(op => ({
          cod: op.cod_ordpro,
          esfuerzo: op.esfuerzo_total,
          prendas: op.prendas_requeridas,
          cliente: op.cliente
        })));
      } else {
        console.log(`⚠️ No hay OPs seleccionadas, usando esfuerzo default: 6`);
        console.log(`⚠️ selectedOpsCode: ${selectedOpsCode?.length || 0} elementos`);
      }

      // ✨ v2.0: El payload permite ambos campos (uno u otro será el principal)
      const payload = {
        estilo_cliente: estiloClienteActual || null, // Puede ser vacío si usa estilo_propio
        cliente_marca: formData.cliente_marca,
        temporada: formData.temporada,
        categoria_lote: formData.categoria_lote,
        familia_producto: formData.familia_producto,
        tipo_prenda: formData.tipo_prenda,
        codigo_estilo: codigoEstiloActual || null, // Puede ser vacío si usa estilo_cliente
        usuario: formData.usuario,
        version_calculo: formData.version_calculo,
        esfuerzo_total: selectedOpsCode && selectedOpsCode.length > 0 ? esforzoPromedio : null, // v2.0: Promedio de OPs seleccionadas
        wips_textiles: esEstiloNuevo ? wipsTextiles : null,
        wips_manufactura: esEstiloNuevo ? wipsManufactura : null,
        cod_ordpros: selectedOpsCode && selectedOpsCode.length > 0 ? selectedOpsCode : null,
        // ✨ Agregar costos de materiales configurados (hilos y telas separados)
        costo_hilos_materia_prima: costosMaterialesFinales?.costo_hilos_materia_prima ?? null,
        costo_telas_compradas: costosMaterialesFinales?.costo_telas_compradas ?? null,
        costo_avios: costosMaterialesFinales?.costo_avios ?? null,
      };

      // 🚀 DEBUG: Mostrar payload completo con esfuerzo_total
      console.log(`🚀 Enviando Cotización:`, {
        ...payload,
        esfuerzo_total: payload.esfuerzo_total,
        cod_ordpros_count: payload.cod_ordpros?.length || 0
      });

      const resultado = await post<any>("/cotizar", payload);
      setCotizacionActual(resultado);
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
  }, [formData, esEstiloNuevo, wipsTextiles, wipsManufactura, selectedOpsCode, selectedOpsData, cargarOpsReales, costosMaterialesFinales]);

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
                {cargandoTipos
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
            📊 {tiposDisponibles.length} tipos
          </div>
        </div>
      </div>
    ),
    [
      formData.version_calculo,
      cargandoTipos,
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
            {/* v2.0: Estilo Cliente encima de Cliente/Marca - COMPONENTE COMPLETO CON BÚSQUEDA */}
            <CampoEstiloClienteComponent
              value={estiloClienteForceRender || estiloClienteLocalRef.current}
              buscandoEstilo={buscandoEstilo}
              infoAutoCompletadoCliente={infoAutoCompletadoCliente}
              esEstiloClienteNuevo={esEstiloClienteNuevo}
              onChange={handleEstiloClienteChange}
              onBuscar={onBuscarEstiloCliente}
            />

            <ClienteSelect
              value={formData.cliente_marca}
              clientesDisponibles={clientesDisponibles}
              onChange={handleClienteChange}
            />

            <CampoCodigoEstiloComponent
              value={codigoEstiloForceRender || codigoEstiloLocalRef.current}
              buscandoEstilo={buscandoEstilo}
              estilosEncontrados={estilosEncontrados}
              esEstiloNuevo={esEstiloNuevo}
              infoAutoCompletado={infoAutoCompletado}
              onChange={handleCodigoEstiloChange}
              onBuscar={onBuscarEstilo}
              onSelectStyle={seleccionarEstiloSimilar}
            />

            <TipoPrendaSelect
              value={formData.tipo_prenda}
              tiposDisponibles={tiposDisponibles}
              cargandoTipos={cargandoTipos}
              onChange={handleTipoPrendaChange}
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
  // 🎨 PANTALLA COSTOS FINALES
  // ========================================

  const PantallaCostosFinales = React.memo(() => {
    // ✨ Calcular promedio de kg_prenda de las OPs seleccionadas
    const kgPrendaPromedio = selectedOpsData.length > 0
      ? selectedOpsData.reduce((sum, op) => sum + (op.kg_prenda || 0), 0) / selectedOpsData.length
      : 0;

    // Memoized componentesAgrupados (misma lógica que en PantallaResultados)
    const componentesAgrupados = useMemo(() => {
      if (!cotizacionActual) return [];

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
          nombre: "Costo Materia Prima (Hilos)",
          costo_unitario: costosMaterialesFinales?.costo_hilos_materia_prima ?? cotizacionActual.costo_hilos_materia_prima ?? cotizacionActual.costo_materia_prima,
          fuente: costosMaterialesFinales || cotizacionActual.costo_hilos_materia_prima ? "configurado" : "ultimo_costo",
          badge: costosMaterialesFinales || cotizacionActual.costo_hilos_materia_prima ? "hilos" : "último costo",
          es_agrupado: false,
        },
        {
          nombre: "Costo Tela Comprada",
          costo_unitario: costosMaterialesFinales?.costo_telas_compradas ?? cotizacionActual.costo_telas_compradas ?? 0,
          fuente: costosMaterialesFinales || cotizacionActual.costo_telas_compradas ? "configurado" : "ultimo_costo",
          badge: costosMaterialesFinales || cotizacionActual.costo_telas_compradas ? "telas" : "sin datos",
          es_agrupado: false,
        },
        {
          nombre: "Costo Avíos",
          costo_unitario: costosMaterialesFinales?.costo_avios ?? cotizacionActual.costo_avios,
          fuente: costosMaterialesFinales ? "configurado" : "ultimo_costo",
          badge: costosMaterialesFinales ? "configurado" : "último costo",
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
      kgPrendaPromedio, // ✨ Agregar a dependencias
      costosMaterialesFinales, // ✨ Actualizar cuando cambian los costos de materiales
    ]);

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
        {/* DESGLOSE DETALLADO DE COSTOS */}
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
                  {componentesAgrupados.map((comp, idx) => {
                    // ✨ Función para obtener la descripción correcta según el nombre del componente
                    const getDescripcion = (nombre: string) => {
                      if (nombre.includes("Textil")) return "en base a ruta textil";
                      if (nombre.includes("Manufactura")) return "en base a ruta manufactura";
                      if (nombre.includes("Materia Prima") || nombre.includes("Avíos") || nombre.includes("Tela"))
                        return "en base a configuración de inputs para producción";
                      if (nombre.includes("Indirecto") || nombre.includes("Administración") || nombre.includes("Ventas"))
                        return "en base a la bolsa anual de gastos y prendas";
                      return "en base a datos históricos";
                    };

                    return (
                      <div key={idx} className="grid grid-cols-4 gap-3">
                        {/* Tarjeta 1: Componente (ocupa 2 columnas) */}
                        <div className="col-span-2 p-3 rounded-xl bg-orange-50 flex flex-col justify-center">
                          <div className="font-semibold text-red-900 text-sm mb-1">
                            {comp.nombre}
                          </div>
                          <div className="text-xs text-gray-700">
                            {getDescripcion(comp.nombre)}
                          </div>
                        </div>

                        {/* Tarjeta 2: Costo por Prenda */}
                        <div className="p-3 rounded-xl bg-orange-50 flex flex-col justify-center items-center text-center">
                          <div className="text-xs font-semibold text-red-900 mb-2">
                            Costo por Prenda
                          </div>
                          <div className="font-bold text-lg text-red-900">
                            ${comp.costo_unitario.toFixed(2)}
                          </div>
                        </div>

                        {/* Tarjeta 3: Costo por Kg (si aplica) */}
                        <div className="p-3 rounded-xl bg-orange-50 flex flex-col justify-center items-center text-center">
                          <div className="text-xs font-semibold text-red-900 mb-2">
                            Costo por Kg
                          </div>
                          <div className="font-bold text-lg text-red-900">
                            {kgPrendaPromedio > 0
                              ? `$${(comp.costo_unitario / kgPrendaPromedio).toFixed(2)}`
                              : "N/A"
                            }
                          </div>
                        </div>
                      </div>
                    );
                  })}

                  <div className="border-t-2 pt-3 mt-4 border-orange-400 grid grid-cols-4 gap-3">
                    {/* Tarjeta 1: Total Label (ocupa 2 columnas) */}
                    <div className="col-span-2 p-3 rounded-xl bg-orange-200 flex flex-col justify-center">
                      <div className="font-bold text-red-900 text-sm">
                        Costo Base Total
                      </div>
                    </div>

                    {/* Tarjeta 2: Costo por Prenda */}
                    <div className="p-3 rounded-xl bg-orange-200 flex flex-col justify-center items-center text-center">
                      <div className="text-xs font-semibold text-red-900 mb-2">
                        Total por Prenda
                      </div>
                      <div className="font-bold text-lg text-red-900">
                        ${componentesAgrupados.reduce((sum, comp) => sum + comp.costo_unitario, 0).toFixed(2)}
                      </div>
                    </div>

                    {/* Tarjeta 3: Costo por Kg */}
                    <div className="p-3 rounded-xl bg-orange-200 flex flex-col justify-center items-center text-center">
                      <div className="text-xs font-semibold text-red-900 mb-2">
                        Total por Kg
                      </div>
                      <div className="font-bold text-lg text-red-900">
                        {kgPrendaPromedio > 0
                          ? `$${(componentesAgrupados.reduce((sum, comp) => sum + comp.costo_unitario, 0) / kgPrendaPromedio).toFixed(2)}`
                          : "N/A"
                        }
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Vector de ajuste */}
              <div>
                <h3 className="font-bold mb-4 text-red-500">
                  Vector de Ajuste
                </h3>
                <div className="space-y-3">
                  {/* v2.0: Factor Lote y Factor Estilo eliminados - no se usan en el cálculo */}
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
                    <div className="text-sm text-white/90 mb-2">
                      Precio Final ($ por prenda)
                    </div>
                    <div className="text-2xl font-bold text-white mb-2">
                      ${(cotizacionActual.precio_final || 0).toFixed(2)}/prenda
                    </div>
                    <div className="text-xs text-white/70">
                      ${(componentesAgrupados.reduce((sum, comp) => sum + comp.costo_unitario, 0) || 0).toFixed(2)} × (1 + 15% × {(cotizacionActual.vector_total || 1).toFixed(3)})
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
            onClick={() => {
              setCostosFinalCalculados(false);
              setPestanaActiva("formulario");
            }}
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

  PantallaCostosFinales.displayName = "PantallaCostosFinales";

  // ========================================
  // 🎨 PANTALLA RESULTADOS
  // ========================================

  const PantallaResultados = React.memo(() => {
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
            </div>
          </div>
        </div>

        {/* OPs de referencia */}
        {cotizacionActual && (
          <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
            <div className="p-6 border-b border-gray-100 bg-red-800">
              <h2 className="text-xl font-bold flex items-center gap-3 text-white">
                <FileText className="h-6 w-6" />
                OPs de Referencia
              </h2>
            </div>

            <div className="p-6">
              <OpsSelectionTable
                codigoEstilo={cotizacionActual.inputs.estilo_cliente || cotizacionActual.inputs.codigo_estilo || ""}
                versionCalculo={cotizacionActual.inputs.version_calculo}
                marca={cotizacionActual.inputs.cliente_marca}
                tipoPrenda={cotizacionActual.inputs.tipo_prenda}
                onOpsSelected={handleOpsSelected}
                opsPreseleccionadas={selectedOpsCode} // ✨ Mantener selecciones
                tipoEstilo={cotizacionActual.inputs.estilo_cliente ? "estilo_cliente" : "estilo_propio"} // v2.0: Indicar tipo
              />

              {selectedOpsCode.length > 0 && (
                <div className="mt-8 border-t pt-8">
                  <h3 className="text-lg font-bold text-red-900 mb-4">Análisis de Costos por WIP</h3>
                  {(() => {
                    // ✨ Calcular promedio de kg_prenda de las OPs seleccionadas
                    const kgPrendaPromedio = selectedOpsData.length > 0
                      ? selectedOpsData.reduce((sum, op) => sum + (op.kg_prenda || 0), 0) / selectedOpsData.length
                      : 0;

                    return (
                      <WipDesgloseTable
                        ref={wipDesgloseTableRef}
                        {...({
                          codigoEstilo: formData.codigo_estilo,
                          versionCalculo: formData.version_calculo,
                          codOrdpros: selectedOpsCode,
                          onCostosCalculados: handleCostosWipCalculados,
                          onError: handleOpsSelected,
                          wipsPreseleccionados: selectedWipsRef.current, // ✨ Mantener selecciones visualmente desde ref
                          factoresWip: factoresWip, // ✨ Pasar factores persistentes desde el padre
                          onFactoresChange: setFactoresWip, // ✨ Callback para actualizar factores en el padre
                          kgPrendaPromedio: kgPrendaPromedio, // ✨ Promedio de kg/prenda de OPs seleccionadas
                        } as any)}
                      />
                    );
                  })()}

                  {/* ✨ BOTÓN: Ir a Análisis de Materiales */}
                  <div className="mt-6 flex justify-end gap-4">
                    <button
                      onClick={() => {
                        // Guardar selección de WIPs antes de navegar
                        if (wipDesgloseTableRef.current) {
                          const wipsSeleccionados = wipDesgloseTableRef.current.getSelectedWipsIds();
                          selectedWipsRef.current = wipsSeleccionados;
                        }
                        setPestanaActiva("materiales");
                      }}
                      className="px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center gap-2"
                    >
                      <Layers className="h-5 w-5" />
                      Continuar a Análisis de Materiales
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  });

  PantallaResultados.displayName = "PantallaResultados";

  // ========================================
  // 📊 PANTALLA DE RESULTADOS DE MATERIALES
  // ========================================
  const PantallaMateriales = React.memo(() => {
    return (
      <div className="space-y-8">
        {/* Análisis de Materiales */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
          <h2 className="text-2xl font-bold text-red-800 mb-6">
            Análisis de Materiales
          </h2>

          {/* Desgloses */}
          <div className="space-y-6">
            <div>
              <h3 className="font-bold text-lg text-red-700 mb-4">
                Desglose de Hilos
              </h3>
              <HilosDesgloseTable
                ref={hilosDesgloseTableRef}
                versionCalculo={formData.version_calculo}
                estiloCliente={formData.estilo_cliente}
                codigoEstilo={formData.codigo_estilo}
                clienteMarca={formData.cliente_marca}
                tipoPrenda={formData.tipo_prenda}
                onError={(errorMsg) => console.error("Error en hilos:", errorMsg)}
              />
            </div>

            <div>
              <h3 className="font-bold text-lg text-red-700 mb-4">
                Desglose de Avios
              </h3>
              <AviosDesgloseTable
                ref={aviosDesgloseTableRef}
                versionCalculo={formData.version_calculo}
                estiloCliente={formData.estilo_cliente}
                codigoEstilo={formData.codigo_estilo}
                clienteMarca={formData.cliente_marca}
                tipoPrenda={formData.tipo_prenda}
                onError={(errorMsg) => console.error("Error en avios:", errorMsg)}
              />
            </div>

            <div>
              <h3 className="font-bold text-lg text-purple-700 mb-4">
                Desglose de Telas
              </h3>
              <TelasDesgloseTable
                ref={telasDesgloseTableRef}
                versionCalculo={formData.version_calculo}
                estiloCliente={formData.estilo_cliente}
                codigoEstilo={formData.codigo_estilo}
                clienteMarca={formData.cliente_marca}
                tipoPrenda={formData.tipo_prenda}
                onError={(errorMsg) => console.error("Error en telas:", errorMsg)}
              />
            </div>
          </div>
        </div>

        {/* Botón de Calcular Costos Finales - Aquí después de Materiales */}
        <div className="flex justify-end gap-4">
          <button
            onClick={async () => {
              // ✨ Obtener totales de las tablas de desgloses
              const totalHilos = hilosDesgloseTableRef.current?.getTotalCostoHilos() || 0;
              const totalAvios = aviosDesgloseTableRef.current?.getTotalCostoAvios() || 0;
              const totalTelas = telasDesgloseTableRef.current?.getTotalCostoTelas() || 0;

              // Guardar costos de materiales calculados - SEPARADO hilos y telas
              const costosMateriales = {
                costo_materia_prima: totalHilos + totalTelas, // Hilos + Telas (para compatibilidad)
                costo_avios: totalAvios,
                costo_hilos_materia_prima: totalHilos, // ✨ Materia Prima Hilos
                costo_telas_compradas: totalTelas, // ✨ Materia de Tela Comprada
              };
              setCostosMaterialesFinales(costosMateriales);

              // ✨ Actualizar también cotizacionActual con los nuevos costos separados
              setCotizacionActual((prev) => {
                if (!prev) return prev;

                // Recalcular costo_base_total sumando todos los componentes actualizados
                const nuevosCostos = {
                  costo_textil: prev.costo_textil || 0,
                  costo_manufactura: prev.costo_manufactura || 0,
                  costo_avios: totalAvios, // Actualizado
                  costo_materia_prima: totalHilos + totalTelas, // Actualizado
                  costo_indirecto_fijo: prev.costo_indirecto_fijo || 0,
                  gasto_administracion: prev.gasto_administracion || 0,
                  gasto_ventas: prev.gasto_ventas || 0,
                };
                const costoBaseTotalActualizado = Object.values(nuevosCostos).reduce((a, b) => a + b, 0);

                // Recalcular precio_final con el nuevo costo_base_total
                const vectorTotal = prev.vector_total || 1;
                const margenBase = 0.15; // 15% margen
                const precioFinalActualizado = costoBaseTotalActualizado * (1 + margenBase * vectorTotal);

                return {
                  ...prev,
                  costo_materia_prima: totalHilos + totalTelas,
                  costo_avios: totalAvios,
                  costo_base_total: costoBaseTotalActualizado, // ✨ Recalculado
                  precio_final: precioFinalActualizado, // ✨ Recalculado con nuevo costo base
                  // ✨ Agregar campos separados para visualización en desglose
                  ...(costosMateriales.costo_hilos_materia_prima !== undefined && {
                    costo_hilos_materia_prima: costosMateriales.costo_hilos_materia_prima,
                  }),
                  ...(costosMateriales.costo_telas_compradas !== undefined && {
                    costo_telas_compradas: costosMateriales.costo_telas_compradas,
                  }),
                };
              });

              await procesarCotizacion();
              // Marcar que los costos finales han sido calculados
              setCostosFinalCalculados(true);
              // Navegar a Costos Finales después de procesar
              setTimeout(() => setPestanaActiva("costos"), 500);
            }}
            disabled={cargando || !selectedOpsCode || selectedOpsCode.length === 0}
            className="group relative px-12 py-4 font-bold text-white rounded-2xl shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 bg-gradient-to-r from-red-800 via-red-700 to-red-600"
          >
            {cargando ? (
              <div className="flex items-center gap-3">
                <RefreshCw className="h-6 w-6 animate-spin" />
                <span className="text-lg">Calculando...</span>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <span className="text-2xl">💰</span>
                <span className="text-lg">Calcular Costos Finales</span>
              </div>
            )}
          </button>
        </div>
      </div>
    );
  });

  PantallaMateriales.displayName = "PantallaMateriales";

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
              disabled={!selectedOpsCode || selectedOpsCode.length === 0}
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
              Resultados de Procesos
            </button>

            <button
              onClick={() => setPestanaActiva("materiales")}
              disabled={!selectedOpsCode || selectedOpsCode.length === 0}
              className={`px-8 py-4 font-bold transition-all duration-300 flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed ${
                pestanaActiva === "materiales"
                  ? "text-white shadow-lg"
                  : "hover:shadow-md"
              }`}
              style={{
                backgroundColor:
                  pestanaActiva === "materiales" ? "#821417" : "transparent",
                color: pestanaActiva === "materiales" ? "white" : "#bd4c42",
              }}
            >
              <Layers className="h-5 w-5" />
              Resultados de Materiales
            </button>

            <button
              onClick={() => setPestanaActiva("costos")}
              disabled={!costosFinalCalculados}
              className={`px-8 py-4 font-bold transition-all duration-300 flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed ${
                pestanaActiva === "costos"
                  ? "text-white shadow-lg"
                  : "hover:shadow-md"
              }`}
              style={{
                backgroundColor:
                  pestanaActiva === "costos" ? "#821417" : "transparent",
                color: pestanaActiva === "costos" ? "white" : "#bd4c42",
              }}
            >
              <DollarSign className="h-5 w-5" />
              Costos Finales
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
        {pestanaActiva === "materiales" && <PantallaMateriales />}
        {pestanaActiva === "costos" && <PantallaCostosFinales />}
      </div>
    </div>
  );
};

export default SistemaCotizadorTDV;
