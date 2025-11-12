"use client";

import React, { useState, useCallback, useMemo, forwardRef } from "react";
import { useImperativeHandle } from "react";
import { ChevronDown, ChevronUp, CheckSquare, Square } from "lucide-react";

// Interface para una OP individual
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
}

// Interface para la respuesta de OPs
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
  onOpsSelected: (opsSeleccionadas: OP[]) => Promise<void>;
  onError?: (error: string) => void;
  opsSeleccionadasPrevia?: string[]; // Mantener selección anterior
  marca?: string; // Para búsqueda alternativa por marca + tipo_prenda
  tipoPrenda?: string; // Para búsqueda alternativa por marca + tipo_prenda
}

export interface OpsSelectionTableRef {
  iniciarBusqueda: () => void;
  iniciarBusquedaPorMarca: (marca: string, tipoPrenda: string) => void;
}

type SortField = "cod_ordpro" | "textil_unitario" | "manufactura_unitario" | "prendas_requeridas" | "fecha_facturacion";
type SortDirection = "asc" | "desc";

export const OpsSelectionTable = forwardRef<OpsSelectionTableRef, OpsSelectionTableProps>(
  ({ codigoEstilo, versionCalculo, onOpsSelected, onError, opsSeleccionadasPrevia, marca, tipoPrenda }, ref) => {
    const [opsData, setOpsData] = useState<OP[]>([]);
    const [cargando, setCargando] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [sortField, setSortField] = useState<SortField>("fecha_facturacion");
    const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
    const [selectedOps, setSelectedOps] = useState<Set<string>>(new Set());
    const [debeCargar, setDebeCargar] = useState(false); // Control para evitar búsqueda automática
    const [busquedaPorMarca, setBusquedaPorMarca] = useState<{ marca: string; tipoPrenda: string } | null>(null); // Para búsqueda alternativa
    const [filtrosCategoriaLote, setFiltrosCategoriaLote] = useState<Set<string>>(new Set()); // Filtros post-búsqueda

    // Exponer métodos imperativos al componente padre
    useImperativeHandle(ref, () => ({
      iniciarBusqueda: () => setDebeCargar(true),
      iniciarBusquedaPorMarca: (m: string, t: string) => {
        setBusquedaPorMarca({ marca: m, tipoPrenda: t });
        setDebeCargar(true);
      },
    }), []);

    // Cargar OPs detalladas - soporta búsqueda por código_estilo o por marca+tipo_prenda
    const cargarOpsDetalladas = useCallback(async () => {
      setCargando(true);
      setError(null);

      try {
        let url: string;

        // Determinar URL según tipo de búsqueda
        if (busquedaPorMarca && busquedaPorMarca.marca && busquedaPorMarca.tipoPrenda) {
          // Búsqueda alternativa por marca + tipo_prenda
          url = `http://localhost:8000/obtener-ops-por-marca/${encodeURIComponent(busquedaPorMarca.marca)}/${encodeURIComponent(busquedaPorMarca.tipoPrenda)}?version_calculo=${versionCalculo}`;
        } else {
          // Búsqueda por código_estilo (default)
          url = `http://localhost:8000/obtener-ops-detalladas/${codigoEstilo}?version_calculo=${versionCalculo}`;
        }

        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Error ${response.status}: No se pudieron cargar las OPs`);
        }

        const data: OpsResponse = await response.json();

        if (data.ops.length === 0) {
          const tipoError = busquedaPorMarca
            ? `No hay OPs disponibles para ${busquedaPorMarca.marca} - ${busquedaPorMarca.tipoPrenda}`
            : "No hay OPs disponibles para este estilo (estilo nuevo)";
          setError(tipoError);
          setOpsData([]);
          setSelectedOps(new Set());
        } else {
          // Inicializar OPs - seleccionar todas por defecto
          setOpsData(data.ops);
          setSelectedOps(new Set(data.ops.map((op) => op.cod_ordpro)));
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : "Error desconocido";
        setError(errorMsg);
        if (onError) onError(errorMsg);
      } finally {
        setCargando(false);
      }
    }, [codigoEstilo, versionCalculo, onError, busquedaPorMarca]);

    // Cargar OPs solo cuando se solicita explícitamente (NO automáticamente)
    // ✨ CORREGIDO: useEffect solo se ejecuta cuando debeCargar es true
    React.useEffect(() => {
      if (debeCargar) {
        cargarOpsDetalladas();
        setDebeCargar(false); // Resetear para próxima búsqueda
      }
    }, [debeCargar]);

    // Restaurar selección anterior cuando opsSeleccionadasPrevia cambia
    React.useEffect(() => {
      if (opsSeleccionadasPrevia && opsSeleccionadasPrevia.length > 0 && opsData.length > 0) {
        // Solo actualizar si las OPs cargadas contienen las OPs de la selección previa
        const opsValidas = opsSeleccionadasPrevia.filter(opCode =>
          opsData.some(op => op.cod_ordpro === opCode)
        );
        if (opsValidas.length > 0) {
          setSelectedOps(new Set(opsValidas));
          console.log("✅ Restaurada selección anterior de OPs:", opsValidas);
        }
      }
    }, [opsSeleccionadasPrevia, opsData]);

    // Ordenar OPs
    const sortedOps = useMemo(() => {
      const sorted = [...opsData].sort((a, b) => {
        let aVal: any = a[sortField];
        let bVal: any = b[sortField];

        // Manejar valores numéricos vs. strings
        if (typeof aVal === "number" && typeof bVal === "number") {
          return sortDirection === "asc" ? aVal - bVal : bVal - aVal;
        } else {
          aVal = String(aVal);
          bVal = String(bVal);
          return sortDirection === "asc" ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        }
      });
      return sorted;
    }, [opsData, sortField, sortDirection]);

    // Obtener categorías únicas para filtros
    const categoriasUnicas = useMemo(() => {
      return Array.from(new Set(opsData.map(op => op.categoria_lote))).sort();
    }, [opsData]);

    // Aplicar filtro de categoría lote (post-búsqueda)
    const opsFiltradasPorCategoria = useMemo(() => {
      if (filtrosCategoriaLote.size === 0) return sortedOps; // Sin filtros, mostrar todas
      return sortedOps.filter(op => filtrosCategoriaLote.has(op.categoria_lote));
    }, [sortedOps, filtrosCategoriaLote]);

    // Toggle selección de una OP
    const toggleOp = useCallback((codOrdpro: string) => {
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

    // Toggle seleccionar todas (sobre el universo de OPs filtradas)
    const toggleSelectAll = useCallback(() => {
      const opsATratar = filtrosCategoriaLote.size === 0 ? opsData : opsFiltradasPorCategoria;
      if (selectedOps.size === opsATratar.length) {
        setSelectedOps(new Set());
      } else {
        setSelectedOps(new Set(opsATratar.map((op) => op.cod_ordpro)));
      }
    }, [opsData, opsFiltradasPorCategoria, selectedOps.size, filtrosCategoriaLote.size]);

    // Manejar cambio de sorting
    const handleSort = (field: SortField) => {
      if (sortField === field) {
        setSortDirection(sortDirection === "asc" ? "desc" : "asc");
      } else {
        setSortField(field);
        setSortDirection("asc");
      }
    };

    // Obtener OPs seleccionadas
    const opsSeleccionadas = useMemo(
      () => opsData.filter((op) => selectedOps.has(op.cod_ordpro)),
      [opsData, selectedOps]
    );

    // Manejar recálculo de promedios
    const handleRecalcular = useCallback(async () => {
      if (opsSeleccionadas.length === 0) {
        setError("Debes seleccionar al menos una OP");
        return;
      }

      try {
        await onOpsSelected(opsSeleccionadas);
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : "Error recalculando promedios";
        setError(errorMsg);
        if (onError) onError(errorMsg);
      }
    }, [opsSeleccionadas, onOpsSelected, onError]);

    // Renderizar encabezado de columna con sort
    const SortHeader = ({ field, label }: { field: SortField; label: string }) => (
      <th
        onClick={() => handleSort(field)}
        className="px-4 py-3 text-left text-sm font-semibold text-gray-700 cursor-pointer hover:bg-gray-200 transition-colors"
      >
        <div className="flex items-center gap-2">
          {label}
          {sortField === field && (
            sortDirection === "asc" ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />
          )}
        </div>
      </th>
    );

    if (cargando) {
      return (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-500 mr-3"></div>
          <span className="text-lg text-gray-600">Cargando OPs detalladas...</span>
        </div>
      );
    }

    if (error) {
      return (
        <div className="p-6 bg-red-50 border-2 border-red-200 rounded-xl">
          <p className="text-red-800 font-semibold mb-3">⚠️ {error}</p>
          <button
            onClick={cargarOpsDetalladas}
            className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
          >
            Reintentar
          </button>
        </div>
      );
    }

    if (opsData.length === 0) {
      return (
        <div className="p-6 bg-yellow-50 border-2 border-yellow-200 rounded-xl text-center">
          <p className="text-yellow-800 font-semibold">
            No hay OPs disponibles para este estilo. Será tratado como un estilo nuevo.
          </p>
        </div>
      );
    }

    return (
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
        {/* Encabezado */}
        <div className="p-6 border-b border-gray-100 bg-red-800">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-xl font-bold text-white">OPs de Referencia - Tabla Interactiva</h3>
            <span className="text-white/80 text-sm">
              {selectedOps.size} de {opsFiltradasPorCategoria.length} seleccionadas
            </span>
          </div>
          <p className="text-white/80 text-sm">
            Selecciona las OPs que deseas usar para calcular los promedios de costos
          </p>
        </div>

        {/* Filtros de Categoría Lote */}
        {categoriasUnicas.length > 0 && (
          <div className="p-4 border-b border-gray-200 bg-gray-50">
            <h4 className="font-semibold text-sm text-gray-700 mb-3">Filtrar por Categoría de Lote:</h4>
            <div className="flex flex-wrap gap-3">
              {categoriasUnicas.map((categoria) => (
                <label key={categoria} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filtrosCategoriaLote.size === 0 || filtrosCategoriaLote.has(categoria)}
                    onChange={(e) => {
                      setFiltrosCategoriaLote((prev) => {
                        const newSet = new Set(prev);
                        if (e.target.checked) {
                          newSet.add(categoria);
                        } else {
                          newSet.delete(categoria);
                        }
                        return newSet;
                      });
                    }}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">{categoria}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Tabla */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-100 border-b border-gray-200">
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 w-12">
                  <button
                    onClick={toggleSelectAll}
                    className="flex items-center justify-center w-6 h-6 rounded hover:bg-gray-300 transition-colors"
                    title={selectedOps.size === opsData.length ? "Desseleccionar todas" : "Seleccionar todas"}
                  >
                    {selectedOps.size === opsData.length ? (
                      <CheckSquare className="h-5 w-5 text-red-600" />
                    ) : (
                      <Square className="h-5 w-5 text-gray-400" />
                    )}
                  </button>
                </th>
                <SortHeader field="cod_ordpro" label="Código OP" />
                <SortHeader field="textil_unitario" label="Costo Textil ($/prenda)" />
                <SortHeader field="manufactura_unitario" label="Manufactura ($/prenda)" />
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Materia Prima ($/prenda)</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Avios ($/prenda)</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Indirecto Fijo ($/prenda)</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Administración ($/prenda)</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Ventas ($/prenda)</th>
                <SortHeader field="prendas_requeridas" label="Prendas" />
                <SortHeader field="fecha_facturacion" label="Fecha" />
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Categoría</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Esfuerzo</th>
              </tr>
            </thead>
            <tbody>
              {opsFiltradasPorCategoria.map((op) => {
                const isSelected = selectedOps.has(op.cod_ordpro);
                return (
                  <tr
                    key={op.cod_ordpro}
                    className={`border-b border-gray-200 hover:bg-gray-50 transition-colors ${
                      isSelected ? "bg-blue-50" : ""
                    }`}
                  >
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => toggleOp(op.cod_ordpro)}
                        className="flex items-center justify-center w-6 h-6 rounded hover:bg-gray-200 transition-colors"
                      >
                        {isSelected ? (
                          <CheckSquare className="h-5 w-5 text-red-600" />
                        ) : (
                          <Square className="h-5 w-5 text-gray-400" />
                        )}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-sm font-mono text-red-900">{op.cod_ordpro}</td>
                    <td className="px-4 py-3 text-sm text-right text-gray-700">
                      ${op.textil_unitario.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-700">
                      ${op.manufactura_unitario.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-700">
                      ${op.materia_prima_unitario.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-700">
                      ${op.avios_unitario.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-700">
                      ${op.indirecto_fijo_unitario.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-700">
                      ${op.administracion_unitario.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-700">
                      ${op.ventas_unitario.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-700">
                      {op.prendas_requeridas.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      {new Date(op.fecha_facturacion).toLocaleDateString("es-ES")}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">{op.categoria_lote}</td>
                    <td className="px-4 py-3 text-sm text-center">
                      <span className="inline-block px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-semibold">
                        {op.esfuerzo_total}/10
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pie de tabla con resumen y botón */}
        <div className="p-6 border-t border-gray-200 bg-gray-50 flex justify-between items-center">
          <div>
            <p className="text-sm text-gray-600">
              <strong>{selectedOps.size}</strong> OPs seleccionadas de <strong>{opsData.length}</strong>
            </p>
            {selectedOps.size > 0 && (
              <p className="text-xs text-gray-500 mt-1">
                Promedio textil: $
                {(
                  opsSeleccionadas.reduce((sum, op) => sum + op.textil_unitario * op.prendas_requeridas, 0) /
                  opsSeleccionadas.reduce((sum, op) => sum + op.prendas_requeridas, 0)
                ).toFixed(2)}{" "}
                | Promedio manufactura: $
                {(
                  opsSeleccionadas.reduce((sum, op) => sum + op.manufactura_unitario * op.prendas_requeridas, 0) /
                  opsSeleccionadas.reduce((sum, op) => sum + op.prendas_requeridas, 0)
                ).toFixed(2)}
              </p>
            )}
          </div>
          <button
            onClick={handleRecalcular}
            disabled={selectedOps.size === 0}
            className="px-6 py-3 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            Generar Cotización
          </button>
        </div>
      </div>
    );
  },
);

OpsSelectionTable.displayName = "OpsSelectionTable";
