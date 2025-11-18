"use client";

import React, { useState, useCallback, useEffect, forwardRef, useRef, useImperativeHandle } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

// Interfaz para datos de hilos desde la BD
interface Hilo {
  cod_hilado: string;
  descripcion_hilo: string;
  tipo_hilo: string;
  costo_por_prenda_final: number;
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
  costo_ajustado: number;
}

interface HilosDesgloseTableProps {
  versionCalculo: string;
  codOrdpros: string[]; // OPs seleccionadas
  onError?: (error: string) => void;
  hilosPreseleccionados?: string[]; // Hilos preseleccionados por cod_hilado
}

export interface HilosDesgloseTableRef {
  getSelectedHilos: () => HiloConFactor[];
  getTotalCostoHilos: () => number;
}

const HilosDesgloseTableComponent = forwardRef<HilosDesgloseTableRef, HilosDesgloseTableProps>(({
  versionCalculo,
  codOrdpros,
  onError,
  hilosPreseleccionados = [],
}, ref) => {
  const [hilosData, setHilosData] = useState<Hilo[]>([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedHilos, setSelectedHilos] = useState<Set<string>>(new Set(hilosPreseleccionados));
  const [factoresHiloLocal, setFactoresHiloLocal] = useState<Record<string, number>>({}); // (cod_hilado|tipo_hilo) -> factor (valores reales)
  const [factoresInputLocal, setFactoresInputLocal] = useState<Record<string, string>>({}); // (cod_hilado|tipo_hilo) -> factor (para typing)
  const [sortField, setSortField] = useState<"descripcion_hilo" | "tipo_hilo" | "costo_por_prenda_final">("descripcion_hilo");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

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
    if (!versionCalculo || !codOrdpros || codOrdpros.length === 0) return;

    const cargarHilos = async () => {
      setCargando(true);
      setError(null);

      try {
        const params = new URLSearchParams({
          version_calculo: versionCalculo,
          cod_ordpros: codOrdpros.join(","),
        });

        const url = `http://localhost:8000/obtener-hilos-detalladas?${params.toString()}`;
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Error ${response.status}: No se pudieron cargar los hilos`);
        }

        const data: HilosResponse = await response.json();
        setHilosData(data.hilos || []);

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
  }, [versionCalculo, codOrdpros]); // 🔒 NO incluir onError ni hilosPreseleccionados para evitar loops infinitos

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

  // ✨ Hilos con factor y costo ajustado - usar factoresHiloLocal para cálculos
  const hilosConFactor: HiloConFactor[] = hilosData.map((hilo) => {
    const clave = `${hilo.cod_hilado}|${hilo.tipo_hilo}`;
    const factor = factoresHiloLocal[clave] || 1.0;
    return {
      ...hilo,
      factor,
      costo_ajustado: hilo.costo_por_prenda_final * factor,
    };
  });

  // Ordenar hilos
  const hilosOrdenados = [...hilosConFactor].sort((a, b) => {
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

  // Calcular totales
  const totalCostoHilos = hilosData.length > 0
    ? hilosConFactor
        .filter((h) => selectedHilos.has(`${h.cod_hilado}|${h.tipo_hilo}`))
        .reduce((sum, h) => sum + h.costo_ajustado, 0) / codOrdpros.length
    : 0;

  // Exponer métodos al padre via ref
  React.useImperativeHandle(ref, () => ({
    getSelectedHilos: () =>
      hilosConFactor.filter((h) => selectedHilos.has(`${h.cod_hilado}|${h.tipo_hilo}`)),
    getTotalCostoHilos: () => totalCostoHilos,
  }), [hilosConFactor, selectedHilos, codOrdpros.length]);

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

        <div className="mb-4 flex justify-end">
          <button
            onClick={toggleSelectAll}
            className="text-xs px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
          >
            {selectedHilos.size === hilosOrdenados.length ? "Desseleccionar todas" : "Seleccionar todas"}
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
                <th className="px-3 py-2 text-center font-semibold text-gray-700">Costo Prenda</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700">Factor</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700">Costo Ajustado</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700">Frecuencia</th>
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
                      ${hilo.costo_por_prenda_final.toFixed(2)}
                    </td>
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
                    <td className="px-3 py-2 text-center font-semibold text-red-600">
                      ${hilo.costo_ajustado.toFixed(2)}
                    </td>
                    <td className="px-3 py-2 text-center text-xs text-gray-600">
                      {((hilo.frecuencia_ops / codOrdpros.length) * 100).toFixed(0)}%
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
        </div>
      </div>
    </div>
  );
});

HilosDesgloseTableComponent.displayName = "HilosDesgloseTable";

export const HilosDesgloseTable = HilosDesgloseTableComponent;
