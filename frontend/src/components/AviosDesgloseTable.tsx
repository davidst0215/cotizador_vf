"use client";

import React, { useState, useCallback, useEffect, forwardRef, useRef } from "react";
import { ChevronDown, ChevronUp, TrendingUp } from "lucide-react";
import HistoricoPreciosModal from "./HistoricoPreciosModal";

// Interfaz para datos de avios desde la BD
interface Avio {
  avio_codigo: string;
  avio_descripcion: string;
  can_consuni: number; // Unidades por prenda
  costo_por_unidad: number; // Costo sin factor (BD): imp_valorizado_neto_usd / can_movimiento_neto
  costo_por_prenda_final: number; // Calculado en backend: costo_por_unidad × can_consuni
  frecuencia_ops: number; // En cuántas OPs aparece este avio
}

// Respuesta del backend
interface AviosResponse {
  codigo_estilo: string;
  version_calculo: string;
  total_ops: number;
  avios_encontrados: number;
  fecha_corrida: string; // Última fecha_corrida
  avios: Avio[];
}

// Interfaz para avio con factor (solo para Modo Automático)
interface AvioConFactor extends Avio {
  factor: number;
  costo_por_unidad_ajustado: number; // costo_por_unidad × factor
  costo_por_prenda_ajustado: number; // costo_por_unidad_ajustado × can_consuni
}

type ModoAvios = "detallado" | "monto_fijo" | "automatico";

interface AviosDesgloseTableProps {
  versionCalculo: string;
  estiloCliente: string; // Estilo del cliente
  codigoEstilo: string; // Código de estilo
  clienteMarca?: string; // Marca del cliente (para búsqueda fallback)
  tipoPrenda?: string; // Tipo de prenda (para búsqueda fallback)
  onError?: (error: string) => void;
  aviosPreseleccionados?: string[]; // Avios preseleccionados por avio_codigo
}

export interface AviosDesgloseTableRef {
  getSelectedAvios: () => AvioConFactor[] | Avio[];
  getTotalCostoAvios: () => number;
}

const AviosDesgloseTableComponent = forwardRef<AviosDesgloseTableRef, AviosDesgloseTableProps>((
  {
    versionCalculo,
    estiloCliente,
    codigoEstilo,
    clienteMarca,
    tipoPrenda,
    onError,
    aviosPreseleccionados = [],
  },
  ref
) => {
  const [aviosData, setAviosData] = useState<Avio[]>([]);
  const [totalOps, setTotalOps] = useState<number>(0);
  const [fechaCorrida, setFechaCorrida] = useState<string>("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedAvios, setSelectedAvios] = useState<Set<string>>(new Set(aviosPreseleccionados));

  // ✨ 3 Modos de configuración
  const [modo, setModo] = useState<ModoAvios>("automatico");

  // Estado para modal de histórico de precios
  const [modalHistoricoAbierto, setModalHistoricoAbierto] = useState(false);
  const [codigoMaterialSeleccionado, setCodigoMaterialSeleccionado] = useState<string>("");

  // Estado para Modo Automático (factores)
  const [factoresAvioLocal, setFactoresAvioLocal] = useState<Record<string, number>>({}); // (avio_codigo) -> factor
  const [factoresInputLocal, setFactoresInputLocal] = useState<Record<string, string>>({}); // (avio_codigo) -> factor (para typing)

  // Estado para Modo Detallado (costos directos)
  const [costosDetalladoLocal, setCostosDetalladoLocal] = useState<Record<string, number>>({}); // (avio_codigo) -> costo directo
  const [costosDetalladoInputLocal, setCostosDetalladoInputLocal] = useState<Record<string, string>>({}); // (avio_codigo) -> costo (para typing)

  // Estado para Modo Monto Fijo
  const [montoFijoGlobal, setMontoFijoGlobal] = useState<number>(0);
  const [montoFijoInput, setMontoFijoInput] = useState<string>("");

  const [sortField, setSortField] = useState<"avio_descripcion" | "can_consuni" | "costo_por_unidad" | "frecuencia_ops">("avio_descripcion");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const [busqueda, setBusqueda] = useState<string>("");

  // ✨ Ref para almacenar factoresAvioLocal sin crear dependencias
  const factoresAvioRef = useRef<Record<string, number>>(factoresAvioLocal);

  // ✨ Sincronizar el Ref cuando los factores locales cambian
  useEffect(() => {
    factoresAvioRef.current = factoresAvioLocal;
  }, [factoresAvioLocal]);

  // ✨ Sincronizar el estado local de inputs cuando factoresAvioLocal cambia
  useEffect(() => {
    const newLocalState: Record<string, string> = {};
    Object.entries(factoresAvioLocal).forEach(([avioCode, value]) => {
      newLocalState[avioCode] = value.toString();
    });
    setFactoresInputLocal(newLocalState);
  }, [factoresAvioLocal]);

  // Sincronizar selectedAvios cuando aviosPreseleccionados cambia
  useEffect(() => {
    if (aviosPreseleccionados.length > 0) {
      setSelectedAvios(new Set(aviosPreseleccionados));
    }
  }, [aviosPreseleccionados]);

  // Cargar avios desde el backend
  useEffect(() => {
    if (!versionCalculo || (!estiloCliente && !codigoEstilo)) return;

    const cargarAvios = async () => {
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
        const url = `${basePath}/api/proxy/obtener-avios-detalladas?${params.toString()}`;
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Error ${response.status}: No se pudieron cargar los avios`);
        }

        const data: AviosResponse = await response.json();
        setAviosData(data.avios || []);
        setTotalOps(data.total_ops || 0);
        setFechaCorrida(data.fecha_corrida || "");

        // Inicializar factores en 1.0 para todos los avios (Modo Automático)
        const factoresIniciales: Record<string, number> = {};
        (data.avios || []).forEach((avio) => {
          const clave = avio.avio_codigo;
          factoresIniciales[clave] = 1.0;
        });
        setFactoresAvioLocal(factoresIniciales);

        // Inicializar costos directos (Modo Detallado)
        const costosIniciales: Record<string, number> = {};
        (data.avios || []).forEach((avio) => {
          costosIniciales[avio.avio_codigo] = avio.costo_por_prenda_final;
        });
        setCostosDetalladoLocal(costosIniciales);

        // Si no hay preseleccionados, seleccionar todos por defecto
        if (aviosPreseleccionados.length === 0) {
          setSelectedAvios(new Set(data.avios.map((a) => a.avio_codigo)));
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : "Error desconocido";
        setError(errorMsg);
        if (onError) onError(errorMsg);
      } finally {
        setCargando(false);
      }
    };

    cargarAvios();
  }, [versionCalculo, estiloCliente, codigoEstilo, clienteMarca, tipoPrenda]);

  const toggleSelection = useCallback((clave: string) => {
    setSelectedAvios((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(clave)) {
        newSet.delete(clave);
      } else {
        newSet.add(clave);
      }
      return newSet;
    });
  }, []);

  const toggleSelectAll = useCallback(() => {
    if (selectedAvios.size === aviosData.length) {
      setSelectedAvios(new Set());
    } else {
      setSelectedAvios(new Set(aviosData.map((a) => a.avio_codigo)));
    }
  }, [aviosData, selectedAvios.size]);

  // ✨ Actualizar factor (Modo Automático)
  const handleFactorChange = useCallback((clave: string, value: string) => {
    setFactoresInputLocal((prev) => ({
      ...prev,
      [clave]: value,
    }));

    const numValue = parseFloat(value);
    if (!isNaN(numValue) && numValue >= 0.1 && numValue <= 10) {
      setFactoresAvioLocal((prev) => ({
        ...prev,
        [clave]: numValue,
      }));
    }
  }, []);

  // ✨ Actualizar costo directo (Modo Detallado)
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

  // ✨ Actualizar costo global (Modo Monto Fijo)
  const handleMontoFijoChange = useCallback((value: string) => {
    setMontoFijoInput(value);
    const numValue = parseFloat(value);
    if (!isNaN(numValue) && numValue >= 0) {
      setMontoFijoGlobal(numValue);
    }
  }, []);

  // ✨ Avios con factor (solo para Modo Automático)
  const aviosConFactor: AvioConFactor[] = aviosData.map((avio) => {
    const clave = avio.avio_codigo;
    const factor = factoresAvioLocal[clave] || 1.0;

    const costo_por_unidad_ajustado = avio.costo_por_unidad * factor;
    const costo_por_prenda_ajustado = costo_por_unidad_ajustado * avio.can_consuni;

    return {
      ...avio,
      factor,
      costo_por_unidad_ajustado,
      costo_por_prenda_ajustado,
    };
  });

  // ✨ Filtrar avios según búsqueda
  const aviosFiltrados = aviosConFactor.filter((avio) => {
    const term = busqueda.toLowerCase();
    return (
      avio.avio_codigo.toLowerCase().includes(term) ||
      avio.avio_descripcion.toLowerCase().includes(term)
    );
  });

  // Ordenar avios
  const aviosOrdenados = [...aviosFiltrados].sort((a, b) => {
    const aVal = a[sortField];
    const bVal = b[sortField];

    if (typeof aVal === "string") {
      return sortDirection === "asc"
        ? aVal.localeCompare(bVal as string)
        : (bVal as string).localeCompare(aVal);
    }

    const diff = (aVal as number) - (bVal as number);
    return sortDirection === "asc" ? diff : -diff;
  });

  // ✨ Calcular total según el modo
  let totalCostoAvios = 0;
  if (modo === "automatico") {
    totalCostoAvios = aviosData.length > 0
      ? aviosConFactor
          .filter((a) => selectedAvios.has(a.avio_codigo))
          .reduce((sum, a) => sum + a.costo_por_prenda_ajustado, 0)
      : 0;
  } else if (modo === "detallado") {
    totalCostoAvios = Array.from(selectedAvios).reduce((sum, codigo) => {
      return sum + (costosDetalladoLocal[codigo] || 0);
    }, 0);
  } else if (modo === "monto_fijo") {
    totalCostoAvios = montoFijoGlobal;
  }

  // Exponer métodos al padre via ref
  React.useImperativeHandle(ref, () => ({
    getSelectedAvios: () =>
      modo === "automatico"
        ? aviosConFactor.filter((a) => selectedAvios.has(a.avio_codigo))
        : aviosData.filter((a) => selectedAvios.has(a.avio_codigo)),
    getTotalCostoAvios: () => totalCostoAvios,
  }), [aviosConFactor, aviosData, selectedAvios, costosDetalladoLocal, montoFijoGlobal, modo]);

  if (cargando) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mr-2"></div>
        <span className="text-sm text-gray-600">Cargando avios...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-sm text-red-700">{error}</p>
      </div>
    );
  }

  if (aviosData.length === 0) {
    return <div className="p-4 text-gray-500">No hay avios disponibles para las OPs seleccionadas</div>;
  }

  return (
    <div className="space-y-4">
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-700">
            {aviosOrdenados.length} Avios disponibles • {selectedAvios.size} seleccionados
            {fechaCorrida && <span className="ml-4 text-xs text-gray-500">Última fecha: {fechaCorrida}</span>}
          </h3>
        </div>

        {/* ✨ Toggle de Modos */}
        <div className="mb-4 flex items-center gap-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <span className="font-semibold text-sm text-gray-700">Modo:</span>
          <div className="flex gap-2">
            <button
              onClick={() => setModo("detallado")}
              className={`px-4 py-2 rounded text-sm font-medium transition-all ${
                modo === "detallado"
                  ? "bg-blue-500 text-white shadow-md"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
            >
              Detallado
            </button>
            <button
              onClick={() => setModo("monto_fijo")}
              className={`px-4 py-2 rounded text-sm font-medium transition-all ${
                modo === "monto_fijo"
                  ? "bg-blue-500 text-white shadow-md"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
            >
              Monto Fijo
            </button>
            <button
              onClick={() => setModo("automatico")}
              className={`px-4 py-2 rounded text-sm font-medium transition-all ${
                modo === "automatico"
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
              Costo Total de Avios (por prenda)
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

        {/* Buscador */}
        <div className="mb-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <input
            type="text"
            placeholder="Buscar por código o nombre de avio..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="mb-4 flex justify-between items-center">
          <p className="text-xs text-gray-600">
            Mostrando {aviosOrdenados.length} de {aviosConFactor.length} avios
          </p>
          <button
            onClick={toggleSelectAll}
            className="text-xs px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
          >
            {selectedAvios.size === aviosOrdenados.length && aviosOrdenados.length > 0
              ? "Desseleccionar filtrados"
              : "Seleccionar filtrados"}
          </button>
        </div>

        <div className="overflow-x-auto overflow-y-auto max-h-96 border border-gray-200 rounded">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-300 bg-gray-100">
                <th className="px-3 py-2 text-center w-8">
                  <input
                    type="checkbox"
                    checked={selectedAvios.size === aviosOrdenados.length && aviosOrdenados.length > 0}
                    onChange={toggleSelectAll}
                  />
                </th>
                <th
                  onClick={() => {
                    setSortField("avio_descripcion");
                    setSortDirection(sortDirection === "asc" ? "desc" : "asc");
                  }}
                  className="px-3 py-2 text-center font-semibold text-gray-700 cursor-pointer hover:bg-gray-200"
                >
                  <div className="flex items-center justify-center gap-1">
                    Nombre Avio
                    {sortField === "avio_descripcion" && (sortDirection === "asc" ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)}
                  </div>
                </th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700">Código Avio</th>
                <th
                  onClick={() => {
                    setSortField("can_consuni");
                    setSortDirection(sortDirection === "asc" ? "desc" : "asc");
                  }}
                  className="px-3 py-2 text-center font-semibold text-gray-700 cursor-pointer hover:bg-gray-200"
                >
                  <div className="flex items-center justify-center gap-1">
                    Unidades/prenda
                    {sortField === "can_consuni" && (sortDirection === "asc" ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)}
                  </div>
                </th>
                {/* Columnas según modo */}
                {modo === "automatico" && (
                  <>
                    <th
                      onClick={() => {
                        setSortField("costo_por_unidad");
                        setSortDirection(sortDirection === "asc" ? "desc" : "asc");
                      }}
                      className="px-3 py-2 text-center font-semibold text-gray-700 cursor-pointer hover:bg-gray-200"
                    >
                      <div className="flex items-center justify-center gap-1">
                        Costo/unidad
                        {sortField === "costo_por_unidad" && (sortDirection === "asc" ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)}
                      </div>
                    </th>
                    <th className="px-3 py-2 text-center font-semibold text-gray-700">Histórico</th>
                    <th className="px-3 py-2 text-center font-semibold text-gray-700">Factor</th>
                    <th className="px-3 py-2 text-center font-semibold text-gray-700">Costo/unidad Ajustado</th>
                    <th className="px-3 py-2 text-center font-semibold text-gray-700">Costo/prenda</th>
                  </>
                )}

                {(modo === "detallado" || modo === "monto_fijo") && (
                  <>
                    <th className="px-3 py-2 text-center font-semibold text-gray-700">
                      {modo === "detallado" ? "Costo/prenda" : "Costo/prenda (ref)"}
                    </th>
                    <th className="px-3 py-2 text-center font-semibold text-gray-700">Histórico</th>
                  </>
                )}

                <th
                  onClick={() => {
                    setSortField("frecuencia_ops");
                    setSortDirection(sortDirection === "asc" ? "desc" : "asc");
                  }}
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
              {aviosOrdenados.map((avio) => {
                const clave = avio.avio_codigo;
                return (
                  <tr key={clave} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="px-3 py-2 text-center">
                      <input
                        type="checkbox"
                        checked={selectedAvios.has(clave)}
                        onChange={() => toggleSelection(clave)}
                      />
                    </td>
                    <td className="px-3 py-2 text-center font-semibold text-gray-900">
                      {avio.avio_descripcion}
                    </td>
                    <td className="px-3 py-2 text-center text-gray-700">
                      {avio.avio_codigo}
                    </td>
                    <td className="px-3 py-2 text-center text-gray-700">
                      {avio.can_consuni.toFixed(4)}
                    </td>

                    {/* Contenido según modo */}
                    {modo === "automatico" && (
                      <>
                        <td className="px-3 py-2 text-center text-gray-700">
                          ${avio.costo_por_unidad.toFixed(4)}
                        </td>
                        <td className="px-3 py-2 text-center">
                          <button
                            onClick={() => {
                              setCodigoMaterialSeleccionado(avio.avio_codigo);
                              setModalHistoricoAbierto(true);
                            }}
                            className="p-1 hover:bg-gray-200 rounded transition-colors inline-block"
                            title="Ver histórico de precios"
                          >
                            <TrendingUp className="h-4 w-4 text-red-600 hover:text-red-800" />
                          </button>
                        </td>
                        <td className="px-3 py-2 text-center">
                          <input
                            type="number"
                            value={factoresInputLocal[clave] || avio.factor.toFixed(2)}
                            onChange={(e) => handleFactorChange(clave, e.target.value)}
                            step="0.01"
                            min="0.1"
                            max="10"
                            className="w-16 px-2 py-1 border border-gray-300 rounded text-center text-sm"
                          />
                        </td>
                        <td className="px-3 py-2 text-center text-gray-700">
                          ${avio.costo_por_unidad_ajustado.toFixed(4)}
                        </td>
                        <td className="px-3 py-2 text-center font-semibold text-red-600">
                          ${avio.costo_por_prenda_ajustado.toFixed(4)}
                        </td>
                      </>
                    )}

                    {modo === "detallado" && (
                      <>
                        <td className="px-3 py-2 text-center">
                          <input
                            type="number"
                            value={costosDetalladoInputLocal[clave] || costosDetalladoLocal[clave]?.toFixed(4) || avio.costo_por_prenda_final.toFixed(4)}
                            onChange={(e) => handleCostoDetalladoChange(clave, e.target.value)}
                            step="0.01"
                            min="0"
                            className="w-24 px-2 py-1 border border-gray-300 rounded text-center text-sm font-semibold text-blue-600"
                          />
                        </td>
                        <td className="px-3 py-2 text-center">
                          <button
                            onClick={() => {
                              setCodigoMaterialSeleccionado(avio.avio_codigo);
                              setModalHistoricoAbierto(true);
                            }}
                            className="p-1 hover:bg-gray-200 rounded transition-colors inline-block"
                            title="Ver histórico de precios"
                          >
                            <TrendingUp className="h-4 w-4 text-red-600 hover:text-red-800" />
                          </button>
                        </td>
                      </>
                    )}

                    {modo === "monto_fijo" && (
                      <>
                        <td className="px-3 py-2 text-center text-gray-700">
                          ${avio.costo_por_prenda_final.toFixed(4)}
                        </td>
                        <td className="px-3 py-2 text-center">
                          <button
                            onClick={() => {
                              setCodigoMaterialSeleccionado(avio.avio_codigo);
                              setModalHistoricoAbierto(true);
                            }}
                            className="p-1 hover:bg-gray-200 rounded transition-colors inline-block"
                            title="Ver histórico de precios"
                          >
                            <TrendingUp className="h-4 w-4 text-red-600 hover:text-red-800" />
                          </button>
                        </td>
                      </>
                    )}

                    <td className="px-3 py-2 text-center text-xs text-gray-600">
                      {totalOps > 0 ? ((avio.frecuencia_ops / totalOps) * 100).toFixed(0) : "0"}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Resumen de Total */}
        <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex justify-between items-center">
            <span className="font-semibold text-blue-900">Total Costo Avios (por prenda):</span>
            <span className="text-2xl font-bold text-blue-700">
              ${totalCostoAvios.toFixed(2)}
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
              * Modo Automático: El costo total es calculado como (costo/unidad × factor × unidades/prenda) de los seleccionados
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

AviosDesgloseTableComponent.displayName = "AviosDesgloseTable";

export const AviosDesgloseTable = AviosDesgloseTableComponent;
