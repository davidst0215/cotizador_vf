"use client";

import React, { useState, useCallback, useEffect } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

// Rangos de categorías de lote
const CATEGORIAS_LOTE_RANGOS: Record<string, string> = {
  "Micro Lote": "1-50",
  "Lote Pequeo": "51-500",
  "Lote Mediano": "501-1000",
  "Lote Grande": "1001-4000",
  "Lote Masivo": "4001+",
};

// Mapeo para mostrar nombres correctos (BD puede tener valores sin ñ)
const CATEGORIAS_LOTE_NOMBRES: Record<string, string> = {
  "Lote Pequeo": "Lote Pequeño",
};

interface OP {
  cod_ordpro: string;
  textil_unitario: number;
  manufactura_unitario: number;
  materia_prima_unitario: number;
  avios_unitario: number;
  indirecto_fijo_unitario: number;
  administracion_unitario: number;
  ventas_unitario: number;
  prendas_requeridas: number;
  fecha_facturacion: string;
  esfuerzo_total: number;
  cliente: string;
  categoria_lote: string;
  seleccionado: boolean;
  kg_prenda?: number; // ✨ Peso en kg por prenda (para cálculo de costos por kg)
}

interface OpsResponse {
  codigo_estilo: string;
  version_calculo: string;
  es_estilo_nuevo: boolean;
  ops_encontradas: number;
  ops: OP[];
}

interface OpsSelectionTableProps {
  codigoEstilo: string;
  versionCalculo: string;
  marca: string;
  tipoPrenda: string;
  onOpsSelected: (ops: OP[]) => void; // Solo pasa OPs seleccionadas, sin calcular
  onError?: (error: string) => void;
  opsPreseleccionadas?: string[]; // ✨ OPs que ya fueron seleccionadas
  tipoEstilo?: "estilo_propio" | "estilo_cliente"; // v2.0: Tipo de búsqueda
}

type SortField = "cod_ordpro" | "prendas_requeridas" | "fecha_facturacion";
type SortDirection = "asc" | "desc";

export const OpsSelectionTable: React.FC<OpsSelectionTableProps> = ({
  codigoEstilo,
  versionCalculo,
  marca,
  tipoPrenda,
  onOpsSelected,
  onError,
  opsPreseleccionadas = [],
  tipoEstilo = "estilo_propio", // v2.0: Default a estilo_propio
}) => {
  const [opsData, setOpsData] = useState<OP[]>([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedOps, setSelectedOps] = useState<Set<string>>(new Set(opsPreseleccionadas)); // ✨ Usar preseleccionadas
  const [sortField, setSortField] = useState<SortField>("fecha_facturacion");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [filtroLoteSeleccionado, setFiltroLoteSeleccionado] = useState<Set<string>>(new Set()); // ✨ Filtro por checkboxes

  // Sincronizar selectedOps cuando opsPreseleccionadas cambia
  useEffect(() => {
    if (opsPreseleccionadas.length > 0) {
      setSelectedOps(new Set(opsPreseleccionadas));
    }
  }, [opsPreseleccionadas]);

  // Cargar OPs una sola vez cuando el componente se monta
  useEffect(() => {
    if (!codigoEstilo || !versionCalculo) return;

    const cargarOps = async () => {
      setCargando(true);
      setError(null);

      try {
        // Normalizar version_calculo: FLUIDO -> FLUIDA
        const versionNormalizada = versionCalculo
          .toUpperCase()
          .replace(/FLUIDO(?!A)/, "FLUIDA")
          .replace(/FLU(?!IDA|IDO)/, "FLUIDA") || "FLUIDA";

        const params = new URLSearchParams({
          version_calculo: versionNormalizada,
          marca,
          tipo_prenda: tipoPrenda,
          tipo_estilo: tipoEstilo, // v2.0: Indicar si es estilo_propio o estilo_cliente
        });

        const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
        const url = `${basePath}/api/proxy/obtener-ops-detalladas/${codigoEstilo}?${params.toString()}`;
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Error ${response.status}: No se pudieron cargar las OPs`);
        }

        const data: OpsResponse = await response.json();
        setOpsData(data.ops || []);
        // Si no hay preseleccionadas, seleccionar todas por defecto
        if (opsPreseleccionadas.length === 0) {
          setSelectedOps(new Set(data.ops.map((op) => op.cod_ordpro)));
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : "Error desconocido";
        setError(errorMsg);
        if (onError) onError(errorMsg);
      } finally {
        setCargando(false);
      }
    };

    cargarOps();
  }, [codigoEstilo, versionCalculo, marca, tipoPrenda, onError, opsPreseleccionadas]);

  const toggleSelection = useCallback((codOrdpro: string) => {
    setSelectedOps((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(codOrdpro)) {
        newSet.delete(codOrdpro);
      } else {
        newSet.add(codOrdpro);
      }
      return newSet;
    });
  }, []);

  // ✨ Filtrar OPs según las categorías de lote seleccionadas
  const opsFiltradasPorLote = filtroLoteSeleccionado.size === 0
    ? opsData
    : opsData.filter((op) => filtroLoteSeleccionado.has(op.categoria_lote));

  // ✨ Obtener categorías únicas para el filtro
  const categoriasLoteUnicas = Array.from(new Set(opsData.map((op) => op.categoria_lote))).sort();

  // ✨ Toggle checkbox de categoría de lote
  const toggleFiltroLote = useCallback((categoria: string) => {
    setFiltroLoteSeleccionado((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(categoria)) {
        newSet.delete(categoria);
      } else {
        newSet.add(categoria);
      }
      return newSet;
    });
  }, []);

  const toggleSelectAll = useCallback(() => {
    if (selectedOps.size === opsFiltradasPorLote.length) {
      setSelectedOps(new Set());
    } else {
      setSelectedOps(new Set(opsFiltradasPorLote.map((op) => op.cod_ordpro)));
    }
  }, [opsFiltradasPorLote, selectedOps.size]);

  const sortedOps = [...opsFiltradasPorLote].sort((a, b) => {
    const aVal = a[sortField];
    const bVal = b[sortField];

    if (typeof aVal === "string") {
      return sortDirection === "asc" ? aVal.localeCompare(bVal as string) : (bVal as string).localeCompare(aVal);
    }

    const diff = (aVal as number) - (bVal as number);
    return sortDirection === "asc" ? diff : -diff;
  });

  // Botón: Setear OPs Seleccionadas (SIN CALCULAR)
  const handleSetearOps = useCallback(() => {
    const selected = opsData.filter((op) => selectedOps.has(op.cod_ordpro));
    onOpsSelected(selected);
  }, [opsData, selectedOps, onOpsSelected]);

  if (cargando) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-red-500 mr-2"></div>
        <span className="text-sm text-gray-600">Cargando OPs...</span>
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

  if (opsData.length === 0) {
    return <div className="p-4 text-gray-500">No hay OPs disponibles</div>;
  }

  return (
    <div className="space-y-4">
      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-700">
            {opsFiltradasPorLote.length} OPs disponibles • {selectedOps.size} seleccionadas
          </h3>
        </div>

        {/* ✨ FILTRO POR CATEGORÍA DE LOTE CON CHECKBOXES */}
        <div className="mb-4 space-y-2">
          <label className="text-sm font-semibold text-gray-600">Filtrar por Tamaño de Lote:</label>
          <div className="flex flex-wrap gap-3">
            {categoriasLoteUnicas.map((categoria) => (
              <label key={categoria} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filtroLoteSeleccionado.has(categoria)}
                  onChange={() => toggleFiltroLote(categoria)}
                  className="w-4 h-4 text-blue-600 rounded cursor-pointer"
                />
                <span className="text-sm text-gray-700">
                  {CATEGORIAS_LOTE_NOMBRES[categoria] || categoria} ({CATEGORIAS_LOTE_RANGOS[categoria] || "N/A"})
                </span>
              </label>
            ))}
          </div>
        </div>

        <div className="mb-4 flex justify-end">
          <button
            onClick={toggleSelectAll}
            className="text-xs px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
          >
            {selectedOps.size === opsFiltradasPorLote.length ? "Desseleccionar todas" : "Seleccionar todas"}
          </button>
        </div>

        <div className="overflow-x-auto overflow-y-auto max-h-96 border border-gray-200 rounded">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-300 bg-gray-100">
                <th className="px-3 py-2 text-center w-8">
                  <input type="checkbox" checked={selectedOps.size === opsFiltradasPorLote.length && opsFiltradasPorLote.length > 0} onChange={toggleSelectAll} />
                </th>
                {(["cod_ordpro", "fecha_facturacion", "prendas_requeridas"] as const).map((field) => (
                  <th
                    key={field}
                    onClick={() => {
                      setSortField(field);
                      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
                    }}
                    className="px-3 py-2 text-center font-semibold text-gray-700 cursor-pointer hover:bg-gray-200"
                  >
                    <div className="flex items-center justify-center gap-1">
                      {field === "cod_ordpro"
                        ? "OP"
                        : field === "fecha_facturacion"
                          ? "Fecha de Facturación"
                          : "Prendas Facturadas"}
                      {sortField === field && (sortDirection === "asc" ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)}
                    </div>
                  </th>
                ))}
                <th className="px-3 py-2 text-center font-semibold text-gray-700">Categoría</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700">Esfuerzo</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700">Kg/Prenda</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700">Costo Textil</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700">Costo Manufactura</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700 hidden">Costo Mat. Prima</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700 hidden">Costo Avíos</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700 hidden">Costo Ind. Fijo</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700 hidden">Costo Admin</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700 hidden">Costo Ventas</th>
              </tr>
            </thead>
            <tbody>
              {sortedOps.map((op) => (
                <tr key={op.cod_ordpro} className="border-b border-gray-200 hover:bg-gray-50">
                  <td className="px-3 py-2 text-center">
                    <input type="checkbox" checked={selectedOps.has(op.cod_ordpro)} onChange={() => toggleSelection(op.cod_ordpro)} />
                  </td>
                  <td className="px-3 py-2 text-center font-semibold text-gray-900">{op.cod_ordpro}</td>
                  <td className="px-3 py-2 text-center text-gray-700">{new Date(op.fecha_facturacion).toLocaleDateString("es-ES")}</td>
                  <td className="px-3 py-2 text-center text-gray-700">{op.prendas_requeridas.toLocaleString()}</td>
                  <td className="px-3 py-2 text-center text-gray-700 text-xs">{CATEGORIAS_LOTE_NOMBRES[op.categoria_lote] || op.categoria_lote}</td>
                  <td className="px-3 py-2 text-center font-semibold text-red-600">{op.esfuerzo_total}/10</td>
                  <td className="px-3 py-2 text-center text-gray-700">{op.kg_prenda ? op.kg_prenda.toFixed(3) : "N/A"}</td>
                  <td className="px-3 py-2 text-center text-gray-700">${op.textil_unitario.toFixed(2)}</td>
                  <td className="px-3 py-2 text-center text-gray-700">${op.manufactura_unitario.toFixed(2)}</td>
                  <td className="px-3 py-2 text-center text-gray-700 text-xs hidden">${op.materia_prima_unitario.toFixed(2)}</td>
                  <td className="px-3 py-2 text-center text-gray-700 text-xs hidden">${op.avios_unitario.toFixed(2)}</td>
                  <td className="px-3 py-2 text-center text-gray-700 text-xs hidden">${op.indirecto_fijo_unitario.toFixed(2)}</td>
                  <td className="px-3 py-2 text-center text-gray-700 text-xs hidden">${op.administracion_unitario.toFixed(2)}</td>
                  <td className="px-3 py-2 text-center text-gray-700 text-xs hidden">${op.ventas_unitario.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 flex justify-end">
          <button
            onClick={handleSetearOps}
            disabled={selectedOps.size === 0}
            className="px-6 py-2 bg-red-700 text-white rounded-lg font-semibold hover:bg-red-800 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            Setear OPs Seleccionadas ({selectedOps.size})
          </button>
        </div>
      </div>
    </div>
  );
};
