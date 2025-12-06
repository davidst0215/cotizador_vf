"use client";

import React, { useState, useCallback, useEffect, forwardRef, useRef, useImperativeHandle } from "react";
import { ChevronDown, ChevronUp, TrendingUp } from "lucide-react";
import HistoricoPreciosModal from "./HistoricoPreciosModal";

// Interfaz para datos de telas desde la BD
interface Tela {
  tela_codigo: string;
  tela_descripcion: string;
  combinacion: string;
  color: string;
  talla: string;
  kg_por_prenda: number; // Kg por prenda
  precio_por_kg_real: number; // Precio sin factor (BD)
  costo_por_prenda: number; // Calculado en backend: precio_por_kg × kg_por_prenda
  frecuencia_ops: number; // En cuántas OPs aparece esta tela
}

// Respuesta del backend
interface TelasResponse {
  codigo_estilo: string;
  version_calculo: string;
  total_ops: number;
  telas_encontradas: number;
  fecha_corrida: string;
  telas: Tela[];
}

// Interfaz para tela con factor (estado local)
interface TelaConFactor extends Tela {
  factor: number;
  precio_por_kg_ajustado: number; // precio_por_kg × factor
  costo_por_prenda_ajustado: number; // precio_por_kg_ajustado × kg_por_prenda
}

interface TelasDesgloseTableProps {
  versionCalculo: string;
  estiloCliente: string; // Estilo del cliente
  codigoEstilo: string; // Código de estilo
  clienteMarca?: string; // Marca del cliente (para búsqueda fallback)
  tipoPrenda?: string; // Tipo de prenda (para búsqueda fallback)
  onError?: (error: string) => void;
  telasPreseleccionadas?: string[]; // Telas preseleccionadas por tela_codigo
  // ✨ Props para estado persistente
  selectedIds?: string[];
  factores?: Record<string, number>;
  onSelectionChange?: (ids: string[]) => void;
  onFactorChange?: (factores: Record<string, number>) => void;
  // ✨ Props para persistencia visual de configuración
  modoInicial?: "detallado" | "monto_fijo" | "automatico";
  costosDetalladosIniciales?: Record<string, number>;
  montoFijoInicial?: number;
}

export interface TelasDesgloseTableRef {
  getSelectedTelas: () => TelaConFactor[];
  getTotalCostoTelas: () => number;
  // ✨ Métodos para obtener configuración visual actual
  getModo: () => "detallado" | "monto_fijo" | "automatico";
  getFactores: () => Record<string, number>;
  getCostosDetallados: () => Record<string, number>;
  getMontoFijo: () => number;
}

const TelasDesgloseTableComponent = forwardRef<TelasDesgloseTableRef, TelasDesgloseTableProps>(({
  versionCalculo,
  estiloCliente,
  codigoEstilo,
  clienteMarca,
  tipoPrenda,
  onError,
  telasPreseleccionadas = [],
  selectedIds = [],
  factores = {},
  onSelectionChange,
  onFactorChange,
  modoInicial = "automatico",
  costosDetalladosIniciales = {},
  montoFijoInicial = 0,
}, ref) => {
  const [telasData, setTelasData] = useState<Tela[]>([]);
  const [totalOps, setTotalOps] = useState<number>(0);
  const [fechaCorrida, setFechaCorrida] = useState<string>("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ✨ Usar props o estado local si no se proveen props (para backward compatibility)
  const [localSelectedTelas, setLocalSelectedTelas] = useState<Set<string>>(new Set(telasPreseleccionadas));
  const [localFactores, setLocalFactores] = useState<Record<string, number>>({});

  const selectedTelasSet = onSelectionChange ? new Set(selectedIds) : localSelectedTelas;
  const currentFactores = onFactorChange ? factores : localFactores;

  const [factoresInputLocal, setFactoresInputLocal] = useState<Record<string, string>>({}); // (tela_codigo) -> factor (para typing)
  const [sortField, setSortField] = useState<"tela_descripcion" | "combinacion" | "precio_por_kg_real" | "frecuencia_ops">("tela_descripcion");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const [busqueda, setBusqueda] = useState<string>("");

  // ✨ 3 Modos de configuración
  const [modo, setModo] = useState<"detallado" | "monto_fijo" | "automatico">(modoInicial);

  // Estado para modal de histórico de precios
  const [modalHistoricoAbierto, setModalHistoricoAbierto] = useState(false);
  const [codigoMaterialSeleccionado, setCodigoMaterialSeleccionado] = useState<string>("");

  // Estado para Modo Detallado (costos directos)
  const [costosDetalladoLocal, setCostosDetalladoLocal] = useState<Record<string, number>>(costosDetalladosIniciales); // (tela_codigo) -> costo directo
  const [costosDetalladoInputLocal, setCostosDetalladoInputLocal] = useState<Record<string, string>>({}); // (tela_codigo) -> costo (para typing)

  // Estado para Modo Monto Fijo
  const [montoFijoGlobal, setMontoFijoGlobal] = useState<number>(montoFijoInicial);
  const [montoFijoInput, setMontoFijoInput] = useState<string>(montoFijoInicial > 0 ? montoFijoInicial.toString() : "");

  // ✨ Ref para almacenar factores sin crear dependencias
  const factoreTelaRef = useRef<Record<string, number>>(currentFactores);

  // ✨ Sincronizar el Ref cuando los factores cambian
  useEffect(() => {
    factoreTelaRef.current = currentFactores;
  }, [currentFactores]);

  // ✨ Sincronizar el estado local de inputs cuando factores cambian
  useEffect(() => {
    const newLocalState: Record<string, string> = {};
    Object.entries(currentFactores).forEach(([telaCodigo, value]) => {
      newLocalState[telaCodigo] = value.toString();
    });
    setFactoresInputLocal(prev => ({ ...prev, ...newLocalState }));
  }, [currentFactores]);

  // Sincronizar selectedTelas cuando telasPreseleccionadas cambia
  useEffect(() => {
    if (telasPreseleccionadas.length > 0 && !onSelectionChange) {
      setLocalSelectedTelas(new Set(telasPreseleccionadas));
    }
  }, [telasPreseleccionadas, onSelectionChange]);

  // Cargar telas desde el backend
  useEffect(() => {
    if (!versionCalculo || (!estiloCliente && !codigoEstilo)) return;

    const cargarTelas = async () => {
      setCargando(true);
      setError(null);

      try {
        const params = new URLSearchParams({
          version_calculo: versionCalculo,
        });

        if (estiloCliente) params.append("estilo_cliente", estiloCliente);
        if (codigoEstilo) params.append("codigo_estilo", codigoEstilo);
        if (clienteMarca) params.append("cliente_marca", clienteMarca);
        if (tipoPrenda) params.append("tipo_prenda", tipoPrenda);

        const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
        const url = `${basePath}/api/proxy/obtener-telas-detalladas?${params.toString()}`;
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Error ${response.status}: No se pudieron cargar las telas`);
        }

        const data: TelasResponse = await response.json();
        setTelasData(data.telas || []);
        setTotalOps(data.total_ops || 0);
        setFechaCorrida(data.fecha_corrida || "");

        // ✨ Deduplicar telas por código
        const telasUnicas = Array.from(
          new Map((data.telas || []).map(t => [t.tela_codigo, t])).values()
        );

        // Inicializar factores en 1.0 para todas las telas únicas
        const factoresIniciales: Record<string, number> = {};
        telasUnicas.forEach((tela) => {
          const clave = tela.tela_codigo;
          factoresIniciales[clave] = 1.0;
        });

        if (onFactorChange) {
          onFactorChange(factoresIniciales);
        } else {
          setLocalFactores(factoresIniciales);
        }

        // Si no hay preseleccionadas, seleccionar todas por defecto
        if (telasPreseleccionadas.length === 0) {
          const allCodes = telasUnicas.map((t) => t.tela_codigo);
          if (onSelectionChange) {
            onSelectionChange(allCodes);
          } else {
            setLocalSelectedTelas(new Set(allCodes));
          }
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : "Error desconocido";
        setError(errorMsg);
        if (onError) onError(errorMsg);
      } finally {
        setCargando(false);
      }
    };

    cargarTelas();
  }, [versionCalculo, estiloCliente, codigoEstilo, clienteMarca, tipoPrenda, onSelectionChange, onFactorChange]); // 🔒 NO incluir onError ni telasPreseleccionadas

  const toggleSelection = useCallback((clave: string) => {
    if (onSelectionChange) {
      const newSet = new Set(selectedIds);
      if (newSet.has(clave)) {
        newSet.delete(clave);
      } else {
        newSet.add(clave);
      }
      onSelectionChange(Array.from(newSet));
    } else {
      setLocalSelectedTelas((prev) => {
        const newSet = new Set(prev);
        if (newSet.has(clave)) {
          newSet.delete(clave);
        } else {
          newSet.add(clave);
        }
        return newSet;
      });
    }
  }, [onSelectionChange, selectedIds]);

  const toggleSelectAll = useCallback(() => {
    // ✨ Usar telasUnicas para contar correctamente
    const uniqueCodesCount = new Set(telasData.map(t => t.tela_codigo)).size;
    if (selectedTelasSet.size === uniqueCodesCount) {
      if (onSelectionChange) {
        onSelectionChange([]);
      } else {
        setLocalSelectedTelas(new Set());
      }
    } else {
      const allCodes = telasData.map((t) => t.tela_codigo);
      if (onSelectionChange) {
        onSelectionChange(allCodes);
      } else {
        setLocalSelectedTelas(new Set(allCodes));
      }
    }
  }, [telasData, selectedTelasSet.size, onSelectionChange]);

  // ✨ Actualizar factor con soporte para typing intermedio
  const handleFactorChange = useCallback((clave: string, value: string) => {
    setFactoresInputLocal((prev) => ({
      ...prev,
      [clave]: value,
    }));

    // Intentar convertir a número y actualizar el valor real
    const numValue = parseFloat(value);
    if (!isNaN(numValue) && numValue >= 0.1 && numValue <= 10) {
      if (onFactorChange) {
        onFactorChange({
          ...currentFactores,
          [clave]: numValue,
        });
      } else {
        setLocalFactores((prev) => ({
          ...prev,
          [clave]: numValue,
        }));
      }
    }
  }, [onFactorChange, currentFactores]);

  // ✨ Actualizar costo detallado
  const handleCostoDetalladoChange = useCallback((clave: string, value: string) => {
    setCostosDetalladoInputLocal((prev) => ({
      ...prev,
      [clave]: value,
    }));

    const numValue = parseFloat(value);
    if (!isNaN(numValue) && numValue >= 0) {
      setCostosDetalladoLocal((prev) => ({
        ...prev,
        [clave]: numValue,
      }));
    }
  }, []);

  // ✨ Actualizar monto fijo global
  const handleMontoFijoChange = useCallback((value: string) => {
    setMontoFijoInput(value);
    const numValue = parseFloat(value);
    if (!isNaN(numValue) && numValue >= 0) {
      setMontoFijoGlobal(numValue);
    }
  }, []);

  // ✨ Deduplicar telas por tela_codigo (mantener solo el primer registro de cada código)
  const telasUnicas: Tela[] = Array.from(
    new Map(telasData.map(t => [t.tela_codigo, t])).values()
  );

  // ✨ Telas con factor y costos ajustados - cálculo en cascada según modo
  const telasConFactor: TelaConFactor[] = telasUnicas.map((tela) => {
    const clave = tela.tela_codigo;

    let factor = 1.0;
    let precio_por_kg_ajustado = tela.precio_por_kg_real;
    let costo_por_prenda_ajustado = tela.costo_por_prenda;

    if (modo === "automatico") {
      factor = currentFactores[clave] || 1.0;
      precio_por_kg_ajustado = tela.precio_por_kg_real * factor;
      costo_por_prenda_ajustado = precio_por_kg_ajustado * tela.kg_por_prenda;
    } else if (modo === "detallado") {
      costo_por_prenda_ajustado = costosDetalladoLocal[clave] ?? tela.costo_por_prenda;
      factor = 1.0;
      precio_por_kg_ajustado = tela.precio_por_kg_real;
    } else if (modo === "monto_fijo") {
      costo_por_prenda_ajustado = montoFijoGlobal;
      factor = 1.0;
      precio_por_kg_ajustado = tela.precio_por_kg_real;
    }

    return {
      ...tela,
      factor,
      precio_por_kg_ajustado,
      costo_por_prenda_ajustado,
    };
  });

  // ✨ Filtrar telas según búsqueda
  const telasFiltradas = telasConFactor.filter((tela) => {
    const term = busqueda.toLowerCase();
    return (
      tela.tela_codigo.toLowerCase().includes(term) ||
      tela.tela_descripcion.toLowerCase().includes(term)
    );
  });

  // ✨ Ordenar telas
  const telasOrdenadas = [...telasFiltradas].sort((a, b) => {
    const aValue = a[sortField] ?? 0;
    const bValue = b[sortField] ?? 0;

    if (typeof aValue === "string") {
      return sortDirection === "asc"
        ? aValue.localeCompare(bValue as string)
        : (bValue as string).localeCompare(aValue);
    }

    return sortDirection === "asc"
      ? (aValue as number) - (bValue as number)
      : (bValue as number) - (aValue as number);
  });

  // ✨ Calcular total según el modo
  let totalCostoTelas = 0;
  if (modo === "automatico") {
    totalCostoTelas = telasData.length > 0
      ? telasConFactor
        .filter((t) => selectedTelasSet.has(t.tela_codigo))
        .reduce((sum, t) => sum + t.costo_por_prenda_ajustado, 0)
      : 0;
  } else if (modo === "detallado") {
    totalCostoTelas = Array.from(selectedTelasSet).reduce((sum, codigo) => {
      return sum + (costosDetalladoLocal[codigo] || 0);
    }, 0);
  } else if (modo === "monto_fijo") {
    totalCostoTelas = montoFijoGlobal; // Monto total, no por prenda
  }

  // ✨ Exponer métodos al componente padre
  useImperativeHandle(
    ref,
    () => ({
      getSelectedTelas: () => {
        return telasConFactor.filter((tela) => selectedTelasSet.has(tela.tela_codigo));
      },
      getTotalCostoTelas: () => {
        return totalCostoTelas;
      },
      // ✨ Métodos para obtener configuración visual actual
      getModo: () => modo,
      getFactores: () => currentFactores,
      getCostosDetallados: () => costosDetalladoLocal,
      getMontoFijo: () => montoFijoGlobal,
    }),
    [telasConFactor, selectedTelasSet, totalCostoTelas, modo, currentFactores, costosDetalladoLocal, montoFijoGlobal]
  );

  const handleSort = (field: typeof sortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  if (cargando) {
    return <div className="text-center py-4 text-gray-600">Cargando telas...</div>;
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        {error}
      </div>
    );
  }

  if (telasData.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-yellow-700">
        ⚠️ No hay telas disponibles para el estilo seleccionado
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-700">
            {telasFiltradas.length} Telas disponibles • {selectedTelasSet.size} seleccionadas
          {fechaCorrida && <span className="ml-4 text-xs text-gray-500">Última fecha: {fechaCorrida}</span>}
        </h3>
      </div>

      {/* ✨ Toggle de Modos */}
      <div className="mb-4 flex items-center gap-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
        <span className="font-semibold text-sm text-gray-700">Modo:</span>
        <div className="flex gap-2">
          <button
            onClick={() => setModo("detallado")}
            className={`px-4 py-2 rounded text-sm font-medium transition-all ${modo === "detallado"
              ? "bg-blue-500 text-white shadow-md"
              : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
          >
            Detallado
          </button>
          <button
            onClick={() => setModo("monto_fijo")}
            className={`px-4 py-2 rounded text-sm font-medium transition-all ${modo === "monto_fijo"
              ? "bg-blue-500 text-white shadow-md"
              : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
          >
            Monto Fijo
          </button>
          <button
            onClick={() => setModo("automatico")}
            className={`px-4 py-2 rounded text-sm font-medium transition-all ${modo === "automatico"
              ? "bg-blue-500 text-white shadow-md"
              : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
          >
            Automático
          </button>
        </div>
      </div>

      {/* ✨ Modo Monto Fijo - Caja de costo global */}
      {modo === "monto_fijo" && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <label className="block text-sm font-semibold text-green-900 mb-2">
            Costo Total de Telas (por prenda)
          </label>
          <input
            type="number"
            value={montoFijoInput}
            onChange={(e) => handleMontoFijoChange(e.target.value)}
            min="0"
            step="0.01"
            className="w-full px-4 py-2 border border-green-300 rounded text-lg font-bold text-green-900 focus:outline-none focus:border-green-500"
            placeholder="Ingresa el monto total"
          />
        </div>
      )}

      {/* Búsqueda */}
      <div className="flex items-center gap-2 mb-4">
        <input
          type="text"
          placeholder="Buscar por código o nombre de tela..."
          className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
        />
        <button
          onClick={toggleSelectAll}
          className="text-xs px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
        >
          {selectedTelasSet.size === telasFiltradas.length && telasFiltradas.length > 0
            ? "Desseleccionar filtradas"
            : "Seleccionar filtradas"}
        </button>
      </div>

      {/* Tabla */}
      <div className="overflow-x-auto overflow-y-auto max-h-96 border border-gray-200 rounded">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-300 bg-gray-100">
              <th className="px-3 py-2 text-center w-8">
                <input
                  type="checkbox"
                  checked={selectedTelasSet.size === telasFiltradas.length && telasFiltradas.length > 0}
                  onChange={toggleSelectAll}
                />
              </th>
              <th
                onClick={() => handleSort("tela_descripcion")}
                className="px-3 py-2 text-center font-semibold text-gray-700 cursor-pointer hover:bg-gray-200"
              >
                <div className="flex items-center justify-center gap-1">
                  Nombre Tela
                  {sortField === "tela_descripcion" && (sortDirection === "asc" ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)}
                </div>
              </th>
              <th className="px-3 py-2 text-center font-semibold text-gray-700">Código Tela</th>
              <th
                onClick={() => handleSort("precio_por_kg_real")}
                className="px-3 py-2 text-center font-semibold text-gray-700 cursor-pointer hover:bg-gray-200"
              >
                <div className="flex items-center justify-center gap-1">
                  kg/prenda
                  {sortField === "precio_por_kg_real" && (sortDirection === "asc" ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)}
                </div>
              </th>
              <th
                onClick={() => handleSort("precio_por_kg_real")}
                className="px-3 py-2 text-center font-semibold text-gray-700 cursor-pointer hover:bg-gray-200"
              >
                <div className="flex items-center justify-center gap-1">
                  Precio/kg
                  {sortField === "precio_por_kg_real" && (sortDirection === "asc" ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)}
                </div>
              </th>
              <th className="px-3 py-2 text-center font-semibold text-gray-700">Histórico</th>
              {modo === "automatico" && (
                <>
                  <th className="px-3 py-2 text-center font-semibold text-gray-700">Factor</th>
                  <th className="px-3 py-2 text-center font-semibold text-gray-700">Precio/kg Ajustado</th>
                </>
              )}
              <th className="px-3 py-2 text-center font-semibold text-gray-700">
                {modo === "detallado" ? "Costo/prenda (directo)" : "Costo/prenda"}
              </th>
              <th
                onClick={() => handleSort("frecuencia_ops")}
                className="px-3 py-2 text-center font-semibold text-gray-700 cursor-pointer hover:bg-gray-200"
              >
                <div className="flex items-center justify-center gap-1">
                  Frecuencia
                  {sortField === "frecuencia_ops" && (sortDirection === "asc" ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)}
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {telasOrdenadas.map((tela) => (
              <tr key={tela.tela_codigo} className="border-b border-gray-200 hover:bg-gray-50">
                <td className="px-3 py-2 text-center">
                  <input
                    type="checkbox"
                    checked={selectedTelasSet.has(tela.tela_codigo)}
                    onChange={() => toggleSelection(tela.tela_codigo)}
                  />
                </td>
                <td className="px-3 py-2 text-center font-semibold text-gray-900">
                  {tela.tela_descripcion}
                </td>
                <td className="px-3 py-2 text-center text-gray-700">
                  {tela.tela_codigo}
                </td>
                <td className="px-3 py-2 text-center text-gray-700">
                  {tela.kg_por_prenda.toFixed(4)}
                </td>
                <td className="px-3 py-2 text-center text-gray-700">
                  ${tela.precio_por_kg_real.toFixed(4)}
                </td>
                <td className="px-3 py-2 text-center">
                  <button
                    onClick={() => {
                      setCodigoMaterialSeleccionado(tela.tela_codigo);
                      setModalHistoricoAbierto(true);
                    }}
                    className="p-1 hover:bg-gray-200 rounded transition-colors inline-block"
                    title="Ver histórico de precios"
                  >
                    <TrendingUp className="h-4 w-4 text-red-600 hover:text-red-800" />
                  </button>
                </td>
                {modo === "automatico" && (
                  <>
                    <td className="px-3 py-2 text-center">
                      <input
                        type="number"
                        autoComplete="off"
                        min="0.1"
                        max="10"
                        step="0.01"
                        value={factoresInputLocal[tela.tela_codigo] || tela.factor.toFixed(2)}
                        onChange={(e) => handleFactorChange(tela.tela_codigo, e.target.value)}
                        className="w-16 px-2 py-1 border border-gray-300 rounded text-center text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </td>
                    <td className="px-3 py-2 text-center text-gray-700">
                      ${tela.precio_por_kg_ajustado.toFixed(4)}
                    </td>
                  </>
                )}
                {modo === "detallado" && (
                  <td className="px-3 py-2 text-center">
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={costosDetalladoInputLocal[tela.tela_codigo] || ""}
                      onChange={(e) => handleCostoDetalladoChange(tela.tela_codigo, e.target.value)}
                      className="w-20 px-2 py-1 border border-gray-300 rounded text-center text-sm"
                      placeholder="0.00"
                    />
                  </td>
                )}
                {modo === "monto_fijo" && (
                  <td className="px-3 py-2 text-center text-gray-700 font-medium">
                    ${montoFijoGlobal.toFixed(4)}
                  </td>
                )}
                {modo === "automatico" && (
                  <td className="px-3 py-2 text-center font-semibold text-red-600">
                    ${tela.costo_por_prenda_ajustado.toFixed(4)}
                  </td>
                )}
                {(modo === "detallado" || modo === "monto_fijo") && (
                  <td className="px-3 py-2 text-center font-semibold text-red-600">
                    ${tela.costo_por_prenda_ajustado.toFixed(4)}
                  </td>
                )}
                <td className="px-3 py-2 text-center text-gray-700">
                  {totalOps > 0 ? ((tela.frecuencia_ops / totalOps) * 100).toFixed(1) : 0}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Resumen de Total */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex justify-between items-center">
          <span className="font-semibold text-blue-900">Total Costo Telas (por prenda):</span>
          <span className="text-2xl font-bold text-blue-700">
            ${totalCostoTelas.toFixed(2)}
          </span>
        </div>
        {modo === "monto_fijo" && (
          <p className="text-xs text-blue-600 mt-2">
            * Modo Monto Fijo: El costo total es el valor ingresado directamente
          </p>
        )}
        {modo === "detallado" && (
          <p className="text-xs text-blue-600 mt-2">
            * Modo Detallado: El costo total es la suma de los costos ingresados por prenda
          </p>
        )}
        {modo === "automatico" && (
          <p className="text-xs text-blue-600 mt-2">
            * Modo Automático: El costo total es calculado como (costo/kg × factor × kg/prenda) de los seleccionados
          </p>
        )}
      </div>

      {/* Modal de Histórico de Precios */}
      <HistoricoPreciosModal
        isOpen={modalHistoricoAbierto}
        onClose={() => setModalHistoricoAbierto(false)}
        basePath={process.env.NEXT_PUBLIC_BASE_PATH || ''}
        codigoMaterialInicial={codigoMaterialSeleccionado}
      />
    </div>
  </div>
);
});

TelasDesgloseTableComponent.displayName = "TelasDesgloseTable";

export const TelasDesgloseTable = TelasDesgloseTableComponent;
