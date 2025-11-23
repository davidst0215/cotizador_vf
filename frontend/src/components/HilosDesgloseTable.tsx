"use client";

import React, { useState, useCallback, useEffect, forwardRef, useRef } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

// Interfaz para datos de hilos desde la BD
interface Hilo {
  cod_hilado: string;
  descripcion_hilo: string;
  tipo_hilo: string;
  kg_por_prenda: number;
  costo_por_kg: number; // Costo sin factor (BD)
  costo_por_prenda_final: number; // Calculado en backend: costo_por_kg × kg_por_prenda
  frecuencia_ops: number; // En cuántas OPs aparece este hilo
}

// Respuesta del backend
interface HilosResponse {
  codigo_estilo: string;
  version_calculo: string;
  total_ops: number;
  hilos_encontrados: number;
  hilos: Hilo[];
}

// Interfaz para hilo con factor (estado local)
interface HiloConFactor extends Hilo {
  factor: number;
  costo_por_kg_ajustado: number; // costo_por_kg × factor
  costo_por_prenda_ajustado: number; // costo_por_kg_ajustado × kg_por_prenda
}

interface HilosDesgloseTableProps {
  versionCalculo: string;
  estiloCliente: string; // Estilo del cliente
  codigoEstilo: string; // Código de estilo
  clienteMarca?: string; // Marca del cliente (para búsqueda fallback)
  tipoPrenda?: string; // Tipo de prenda (para búsqueda fallback)
  onError?: (error: string) => void;
  hilosPreseleccionados?: string[]; // Hilos preseleccionados por cod_hilado
}

export interface HilosDesgloseTableRef {
  getSelectedHilos: () => HiloConFactor[];
  getTotalCostoHilos: () => number;
}

const HilosDesgloseTableComponent = forwardRef<HilosDesgloseTableRef, HilosDesgloseTableProps>(({
  versionCalculo,
  estiloCliente,
  codigoEstilo,
  clienteMarca,
  tipoPrenda,
  onError,
  hilosPreseleccionados = [],
}, ref) => {
  const [hilosData, setHilosData] = useState<Hilo[]>([]);
  const [totalOps, setTotalOps] = useState<number>(0);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedHilos, setSelectedHilos] = useState<Set<string>>(new Set(hilosPreseleccionados));
  const [factoresHiloLocal, setFactoresHiloLocal] = useState<Record<string, number>>({}); // (cod_hilado|tipo_hilo) -> factor (valores reales)
  const [factoresInputLocal, setFactoresInputLocal] = useState<Record<string, string>>({}); // (cod_hilado|tipo_hilo) -> factor (para typing)
  const [sortField, setSortField] = useState<"descripcion_hilo" | "tipo_hilo" | "costo_por_kg" | "frecuencia_ops">("descripcion_hilo");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const [busqueda, setBusqueda] = useState<string>("");

  // ✨ 3 Modos de configuración
  const [modo, setModo] = useState<"detallado" | "monto_fijo" | "automatico">("automatico");

  // Estado para Modo Detallado (costos directos)
  const [costosDetalladoLocal, setCostosDetalladoLocal] = useState<Record<string, number>>({}); // (cod_hilado) -> costo directo
  const [costosDetalladoInputLocal, setCostosDetalladoInputLocal] = useState<Record<string, string>>({}); // (cod_hilado) -> costo (para typing)

  // Estado para Modo Monto Fijo
  const [montoFijoGlobal, setMontoFijoGlobal] = useState<number>(0);
  const [montoFijoInput, setMontoFijoInput] = useState<string>("");

  // ✨ Ref para almacenar factoresHiloLocal sin crear dependencias
  const factoresHiloRef = useRef<Record<string, number>>(factoresHiloLocal);

  // ✨ Sincronizar el Ref cuando los factores locales cambian
  useEffect(() => {
    factoresHiloRef.current = factoresHiloLocal;
  }, [factoresHiloLocal]);

  // ✨ Sincronizar el estado local de inputs cuando factoresHiloLocal cambia
  useEffect(() => {
    const newLocalState: Record<string, string> = {};
    Object.entries(factoresHiloLocal).forEach(([codHilado, value]) => {
      newLocalState[codHilado] = value.toString();
    });
    setFactoresInputLocal(newLocalState);
  }, [factoresHiloLocal]);

  // Sincronizar selectedHilos cuando hilosPreseleccionados cambia
  useEffect(() => {
    if (hilosPreseleccionados.length > 0) {
      setSelectedHilos(new Set(hilosPreseleccionados));
    }
  }, [hilosPreseleccionados]);

  // Cargar hilos desde el backend
  useEffect(() => {
    if (!versionCalculo || (!estiloCliente && !codigoEstilo)) return;

    const cargarHilos = async () => {
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

        const url = `/api/proxy/obtener-hilos-detalladas?${params.toString()}`;
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Error ${response.status}: No se pudieron cargar los hilos`);
        }

        const data: HilosResponse = await response.json();
        setHilosData(data.hilos || []);
        setTotalOps(data.total_ops || 0);

        // Inicializar factores en 1.0 para todos los hilos usando clave compuesta (cod_hilado|tipo_hilo)
        const factoresIniciales: Record<string, number> = {};
        (data.hilos || []).forEach((hilo) => {
          const clave = `${hilo.cod_hilado}|${hilo.tipo_hilo}`;
          factoresIniciales[clave] = 1.0;
        });
        setFactoresHiloLocal(factoresIniciales);

        // Si no hay preseleccionados, seleccionar todos por defecto usando clave compuesta
        if (hilosPreseleccionados.length === 0) {
          setSelectedHilos(new Set(data.hilos.map((h) => `${h.cod_hilado}|${h.tipo_hilo}`)));
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : "Error desconocido";
        setError(errorMsg);
        if (onError) onError(errorMsg);
      } finally {
        setCargando(false);
      }
    };

    cargarHilos();
  }, [versionCalculo, estiloCliente, codigoEstilo, clienteMarca, tipoPrenda]); // 🔒 NO incluir onError ni hilosPreseleccionados para evitar loops infinitos

  const toggleSelection = useCallback((clave: string) => {
    setSelectedHilos((prev) => {
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
    if (selectedHilos.size === hilosData.length) {
      setSelectedHilos(new Set());
    } else {
      setSelectedHilos(new Set(hilosData.map((h) => `${h.cod_hilado}|${h.tipo_hilo}`)));
    }
  }, [hilosData, selectedHilos.size]);

  // ✨ Actualizar factor con soporte para typing intermedio
  const handleFactorChange = useCallback((clave: string, value: string) => {
    setFactoresInputLocal((prev) => ({
      ...prev,
      [clave]: value,
    }));

    // Intentar convertir a número y actualizar el valor real
    const numValue = parseFloat(value);
    if (!isNaN(numValue) && numValue >= 0.1 && numValue <= 10) {
      setFactoresHiloLocal((prev) => ({
        ...prev,
        [clave]: numValue,
      }));
    }
  }, []);

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

  // ✨ Hilos con factor y costos ajustados - cálculo en cascada según modo
  const hilosConFactor: HiloConFactor[] = hilosData.map((hilo) => {
    const clave = `${hilo.cod_hilado}|${hilo.tipo_hilo}`;

    let factor = 1.0;
    let costo_por_kg_ajustado = hilo.costo_por_kg;
    let costo_por_prenda_ajustado = hilo.costo_por_prenda_final;

    if (modo === "automatico") {
      factor = factoresHiloLocal[clave] || 1.0;
      costo_por_kg_ajustado = hilo.costo_por_kg * factor;
      costo_por_prenda_ajustado = costo_por_kg_ajustado * hilo.kg_por_prenda;
    } else if (modo === "detallado") {
      costo_por_prenda_ajustado = costosDetalladoLocal[clave] ?? hilo.costo_por_prenda_final;
      factor = 1.0;
      costo_por_kg_ajustado = hilo.costo_por_kg;
    } else if (modo === "monto_fijo") {
      costo_por_prenda_ajustado = montoFijoGlobal;
      factor = 1.0;
      costo_por_kg_ajustado = hilo.costo_por_kg;
    }

    return {
      ...hilo,
      factor,
      costo_por_kg_ajustado,
      costo_por_prenda_ajustado,
    };
  });

  // ✨ Filtrar hilos según búsqueda
  const hilosFiltrados = hilosConFactor.filter((hilo) => {
    const term = busqueda.toLowerCase();
    return (
      hilo.cod_hilado.toLowerCase().includes(term) ||
      hilo.descripcion_hilo.toLowerCase().includes(term) ||
      hilo.tipo_hilo.toLowerCase().includes(term)
    );
  });

  // Ordenar hilos
  const hilosOrdenados = [...hilosFiltrados].sort((a, b) => {
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
  let totalCostoHilos = 0;
  if (modo === "automatico") {
    totalCostoHilos = hilosData.length > 0
      ? hilosConFactor
          .filter((h) => selectedHilos.has(`${h.cod_hilado}|${h.tipo_hilo}`))
          .reduce((sum, h) => sum + h.costo_por_prenda_ajustado, 0)
      : 0;
  } else if (modo === "detallado") {
    totalCostoHilos = Array.from(selectedHilos).reduce((sum, clave) => {
      return sum + (costosDetalladoLocal[clave] || 0);
    }, 0);
  } else if (modo === "monto_fijo") {
    totalCostoHilos = montoFijoGlobal; // Monto total, no por prenda
  }

  // Exponer métodos al padre via ref
  React.useImperativeHandle(ref, () => ({
    getSelectedHilos: () =>
      hilosConFactor.filter((h) => selectedHilos.has(`${h.cod_hilado}|${h.tipo_hilo}`)),
    getTotalCostoHilos: () => totalCostoHilos,
  }), [hilosConFactor, selectedHilos, totalCostoHilos, totalOps, modo]);

  if (cargando) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mr-2"></div>
        <span className="text-sm text-gray-600">Cargando hilos...</span>
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

  if (hilosData.length === 0) {
    return <div className="p-4 text-gray-500">No hay hilos disponibles para las OPs seleccionadas</div>;
  }

  return (
    <div className="space-y-4">
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-700">
            {hilosOrdenados.length} Hilos disponibles • {selectedHilos.size} seleccionados
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
              Costo Total de Hilos (por prenda)
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

        {/* ✨ Buscador */}
        <div className="mb-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <input
            type="text"
            placeholder="Buscar por código, nombre o tipo de hilo..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="mb-4 flex justify-between items-center">
          <p className="text-xs text-gray-600">
            Mostrando {hilosOrdenados.length} de {hilosConFactor.length} hilos
          </p>
          <button
            onClick={toggleSelectAll}
            className="text-xs px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
          >
            {selectedHilos.size === hilosOrdenados.length && hilosOrdenados.length > 0
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
                    checked={selectedHilos.size === hilosOrdenados.length && hilosOrdenados.length > 0}
                    onChange={toggleSelectAll}
                  />
                </th>
                <th
                  onClick={() => {
                    setSortField("descripcion_hilo");
                    setSortDirection(sortDirection === "asc" ? "desc" : "asc");
                  }}
                  className="px-3 py-2 text-center font-semibold text-gray-700 cursor-pointer hover:bg-gray-200"
                >
                  <div className="flex items-center justify-center gap-1">
                    Nombre Hilo
                    {sortField === "descripcion_hilo" && (sortDirection === "asc" ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)}
                  </div>
                </th>
                <th
                  onClick={() => {
                    setSortField("tipo_hilo");
                    setSortDirection(sortDirection === "asc" ? "desc" : "asc");
                  }}
                  className="px-3 py-2 text-center font-semibold text-gray-700 cursor-pointer hover:bg-gray-200"
                >
                  <div className="flex items-center justify-center gap-1">
                    Tipo Hilo
                    {sortField === "tipo_hilo" && (sortDirection === "asc" ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)}
                  </div>
                </th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700">Código Hilo</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700">kg/prenda</th>
                <th
                  onClick={() => {
                    setSortField("costo_por_kg");
                    setSortDirection(sortDirection === "asc" ? "desc" : "asc");
                  }}
                  className="px-3 py-2 text-center font-semibold text-gray-700 cursor-pointer hover:bg-gray-200"
                >
                  <div className="flex items-center justify-center gap-1">
                    Costo/kg
                    {sortField === "costo_por_kg" && (sortDirection === "asc" ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)}
                  </div>
                </th>
                {modo === "automatico" && (
                  <>
                    <th className="px-3 py-2 text-center font-semibold text-gray-700">Factor</th>
                    <th className="px-3 py-2 text-center font-semibold text-gray-700">Costo/kg Ajustado</th>
                  </>
                )}
                <th className="px-3 py-2 text-center font-semibold text-gray-700">
                  {modo === "detallado" ? "Costo/prenda (directo)" : "Costo/prenda"}
                </th>
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
              {hilosOrdenados.map((hilo) => {
                const clave = `${hilo.cod_hilado}|${hilo.tipo_hilo}`;
                return (
                  <tr key={clave} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="px-3 py-2 text-center">
                      <input
                        type="checkbox"
                        checked={selectedHilos.has(clave)}
                        onChange={() => toggleSelection(clave)}
                      />
                    </td>
                    <td className="px-3 py-2 text-center font-semibold text-gray-900">
                      {hilo.descripcion_hilo}
                    </td>
                    <td className="px-3 py-2 text-center text-gray-700">
                      {hilo.tipo_hilo}
                    </td>
                    <td className="px-3 py-2 text-center text-gray-700">
                      {hilo.cod_hilado}
                    </td>
                    <td className="px-3 py-2 text-center text-gray-700">
                      {hilo.kg_por_prenda.toFixed(4)}
                    </td>
                    <td className="px-3 py-2 text-center text-gray-700">
                      ${hilo.costo_por_kg.toFixed(4)}
                    </td>
                    {modo === "automatico" && (
                      <>
                        <td className="px-3 py-2 text-center">
                          <input
                            type="number"
                            value={factoresInputLocal[clave] || hilo.factor.toFixed(2)}
                            onChange={(e) => handleFactorChange(clave, e.target.value)}
                            step="0.01"
                            min="0.1"
                            max="10"
                            className="w-16 px-2 py-1 border border-gray-300 rounded text-center text-sm"
                          />
                        </td>
                        <td className="px-3 py-2 text-center text-gray-700">
                          ${hilo.costo_por_kg_ajustado.toFixed(4)}
                        </td>
                      </>
                    )}
                    {modo === "detallado" && (
                      <td className="px-3 py-2 text-center">
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={costosDetalladoInputLocal[clave] || ""}
                          onChange={(e) => handleCostoDetalladoChange(clave, e.target.value)}
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
                        ${hilo.costo_por_prenda_ajustado.toFixed(4)}
                      </td>
                    )}
                    {(modo === "detallado" || modo === "monto_fijo") && (
                      <td className="px-3 py-2 text-center font-semibold text-red-600">
                        ${hilo.costo_por_prenda_ajustado.toFixed(4)}
                      </td>
                    )}
                    <td className="px-3 py-2 text-center text-xs text-gray-600">
                      {totalOps > 0 ? ((hilo.frecuencia_ops / totalOps) * 100).toFixed(0) : "0"}%
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
            <span className="font-semibold text-blue-900">Total Costo Hilos (por prenda):</span>
            <span className="text-2xl font-bold text-blue-700">
              ${totalCostoHilos.toFixed(2)}
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
      </div>
    </div>
  );
});

HilosDesgloseTableComponent.displayName = "HilosDesgloseTable";

export const HilosDesgloseTable = HilosDesgloseTableComponent;
