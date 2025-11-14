"use client";

import React, { useState, useEffect, useMemo, useCallback, forwardRef, useImperativeHandle } from "react";
import { TrendingUp } from "lucide-react";

// Mapping de WIP IDs a nombres
const NOMBRES_WIPS: Record<string, string> = {
  "10": "Abastecimiento de Hilado",
  "14": "Teñido de Hilado",
  "16": "Tejido de Tela y Rectilíneos",
  "19a": "Teñido de Tela",
  "19c": "Despacho",
  "24": "Estampado Tela",
  "34": "Corte",
  "36": "Estampado Pieza",
  "37": "Bordado Pieza",
  "40": "Costura",
  "43": "Bordado Prendas",
  "44": "Estampado Prendas",
  "45": "Lavado en Prenda (Después de estampar)",
  "49": "Acabado",
};

interface DesgloseWip {
  wip_id: string;
  grupo_wip: "textil" | "manufactura" | "otro";
  total_prendas: number;
  total_textil: number;
  total_manufactura: number;
  textil_por_prenda: number;
  manufactura_por_prenda: number;
}

interface WipDesgloseResponse {
  ops_analizadas: number;
  desgloses_textil: DesgloseWip[];
  desgloses_manufactura: DesgloseWip[];
  desgloses_total: DesgloseWip[];
  fecha_corrida?: string;
}

export interface WipDesgloseTableProps {
  codigoEstilo: string;
  versionCalculo: string;
  codOrdpros: string[]; // OPs seleccionadas
  onError?: (error: string) => void;
  onWipsSelected?: (wips: DesgloseWip[]) => void; // Callback cuando se seleccionan WIPs
  wipsPreseleccionados?: string[]; // ✨ WIPs que ya fueron seleccionados
}

export interface WipDesgloseTableRef {
  getSelectedWips: () => DesgloseWip[];
  getSelectedWipsIds: () => string[];
  getTotalTextil: () => number;
  getTotalManufactura: () => number;
}

const WipDesgloseTableComponent = forwardRef<WipDesgloseTableRef, WipDesgloseTableProps>(({
  codigoEstilo: _codigoEstilo,
  versionCalculo,
  codOrdpros,
  onError,
  onWipsSelected,
  wipsPreseleccionados = [],
}, ref) => {
  const [desgloseData, setDesgloseData] = useState<WipDesgloseResponse | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedWips, setSelectedWips] = useState<Set<string>>(new Set(wipsPreseleccionados)); // ✨ Inicializar con preseleccionados
  const [factoresWip, setFactoresWip] = useState<Record<string, number>>({}); // ✨ Factores multiplicadores por WIP

  // Sincronizar selectedWips cuando wipsPreseleccionados cambia
  useEffect(() => {
    if (wipsPreseleccionados.length > 0) {
      setSelectedWips(new Set(wipsPreseleccionados));
    }
  }, [wipsPreseleccionados]);

  // Cargar desglose WIP cuando cambian las OPs
  useEffect(() => {
    if (!codOrdpros || codOrdpros.length === 0) {
      setDesgloseData(null);
      setSelectedWips(new Set());
      return;
    }

    const cargarDesglose = async () => {
      setCargando(true);
      setError(null);

      try {
        const payload = {
          cod_ordpros: codOrdpros,
          version_calculo: versionCalculo,
        };

        const response = await fetch("http://localhost:8000/desglose-wip-ops", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          throw new Error(`Error ${response.status}: No se pudo obtener el desglose WIP`);
        }

        const data: WipDesgloseResponse = await response.json();
        setDesgloseData(data);
        // ✨ Solo seleccionar todos por defecto si no hay preseleccionados (Y SOLO LOS CON COSTO)
        if (wipsPreseleccionados.length === 0) {
          const wipsConCosto = data.desgloses_total.filter((d) => d.textil_por_prenda > 0 || d.manufactura_por_prenda > 0);
          setSelectedWips(new Set(wipsConCosto.map((w) => w.wip_id)));
        }

        if (!data.desgloses_total || data.desgloses_total.length === 0) {
          setError("No hay datos WIP disponibles");
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : "Error desconocido";
        setError(errorMsg);
        if (onError) onError(errorMsg);
      } finally {
        setCargando(false);
      }
    };

    cargarDesglose();
  }, [codOrdpros, versionCalculo]); // 🔒 NO incluir onError para evitar loops infinitos

  // Calcular totales por grupo - SOLO para los WIPs seleccionados - CON FACTORES APLICADOS
  const totalesPorGrupo = useMemo(() => {
    if (!desgloseData) return { textil: 0, manufactura: 0, conteoTextil: 0, conteoManufactura: 0 };

    // Filtrar solo los WIPs seleccionados
    const textilSeleccionados = desgloseData.desgloses_textil.filter((d) => selectedWips.has(d.wip_id));
    const manufacturaSeleccionados = desgloseData.desgloses_manufactura.filter((d) => selectedWips.has(d.wip_id));

    // ✨ Aplicar factores al cálculo
    const totalTextil = textilSeleccionados.reduce((sum, d) => {
      const factor = factoresWip[d.wip_id] || 1;
      return sum + (d.textil_por_prenda * factor);
    }, 0);

    const totalManufactura = manufacturaSeleccionados.reduce((sum, d) => {
      const factor = factoresWip[d.wip_id] || 1;
      return sum + (d.manufactura_por_prenda * factor);
    }, 0);

    return {
      textil: totalTextil,
      manufactura: totalManufactura,
      conteoTextil: textilSeleccionados.length,
      conteoManufactura: manufacturaSeleccionados.length,
    };
  }, [desgloseData, selectedWips, factoresWip]);

  // Exponer métodos al padre para acceder a WIPs seleccionados sin callbacks
  useImperativeHandle(ref, () => ({
    getSelectedWips: () => {
      if (!desgloseData) return [];
      return desgloseData.desgloses_total.filter((wip) => selectedWips.has(wip.wip_id));
    },
    getSelectedWipsIds: () => {
      return Array.from(selectedWips);
    },
    getTotalTextil: () => {
      return totalesPorGrupo.textil;
    },
    getTotalManufactura: () => {
      return totalesPorGrupo.manufactura;
    },
  }), [desgloseData, selectedWips, totalesPorGrupo]);

  // Toggle selección de un WIP
  const toggleWipSelection = useCallback((wipId: string) => {
    setSelectedWips((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(wipId)) {
        newSet.delete(wipId);
      } else {
        newSet.add(wipId);
      }
      return newSet;
    });
  }, []);

  // Toggle seleccionar todos los WIPs
  // ✨ Toggle seleccionar todos los WIPs (SOLO LOS QUE TIENEN COSTO)
  const toggleSelectAllWips = useCallback(() => {
    if (!desgloseData) return;
    // Filtrar solo WIPs con costo
    const wipsConCosto = desgloseData.desgloses_total.filter((d) => d.textil_por_prenda > 0 || d.manufactura_por_prenda > 0);
    if (selectedWips.size === wipsConCosto.length) {
      setSelectedWips(new Set());
    } else {
      setSelectedWips(new Set(wipsConCosto.map((w) => w.wip_id)));
    }
  }, [desgloseData, selectedWips.size]);

  // ✨ Manejar cambio de factor para un WIP
  const handleFactorChange = useCallback((wipId: string, factor: number) => {
    setFactoresWip((prev) => ({
      ...prev,
      [wipId]: factor,
    }));
  }, []);

  if (cargando) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mr-2"></div>
        <span className="text-sm text-gray-600">Cargando desglose WIP...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="text-sm text-yellow-800">{error}</p>
      </div>
    );
  }

  if (!desgloseData || desgloseData.desgloses_total.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* Resumen de costos por grupo - DINÁMICO según WIPs seleccionados */}
      <div className="grid grid-cols-2 gap-4">
        {desgloseData.desgloses_textil.length > 0 && (
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-4 w-4 text-blue-600" />
              <h4 className="text-sm font-semibold text-blue-900">Textil Por Prenda</h4>
            </div>
            <p className="text-2xl font-bold text-blue-900">${totalesPorGrupo.textil.toFixed(2)}</p>
            <p className="text-xs text-blue-700 mt-1">{totalesPorGrupo.conteoTextil} WIPs</p>
          </div>
        )}

        {desgloseData.desgloses_manufactura.length > 0 && (
          <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4 border border-orange-200">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-4 w-4 text-orange-600" />
              <h4 className="text-sm font-semibold text-orange-900">Manufactura Por Prenda</h4>
            </div>
            <p className="text-2xl font-bold text-orange-900">${totalesPorGrupo.manufactura.toFixed(2)}</p>
            <p className="text-xs text-orange-700 mt-1">{totalesPorGrupo.conteoManufactura} WIPs</p>
          </div>
        )}
      </div>

      {/* Tabla de desglose detallado CON CHECKBOXES */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
          {/* ✨ Contar solo WIPs con costo */}
          {(() => {
            const wipsConCosto = desgloseData.desgloses_total.filter((d) => d.textil_por_prenda > 0 || d.manufactura_por_prenda > 0);
            return (
              <h4 className="text-sm font-semibold text-gray-700">
                Desglose por WIP ({selectedWips.size} / {wipsConCosto.length} seleccionadas)
              </h4>
            );
          })()}

          <div className="flex items-center gap-2">
            {desgloseData.fecha_corrida && (
              <span className="text-xs text-gray-500">
                Datos: {new Date(desgloseData.fecha_corrida).toLocaleDateString("es-ES", { year: "numeric", month: "short", day: "numeric" })}
              </span>
            )}
            {(() => {
              const wipsConCosto = desgloseData.desgloses_total.filter((d) => d.textil_por_prenda > 0 || d.manufactura_por_prenda > 0);
              return (
                <button
                  onClick={toggleSelectAllWips}
                  className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                >
                  {selectedWips.size === wipsConCosto.length ? "Deseleccionar todas" : "Seleccionar todas"}
                </button>
              );
            })()}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-4 py-3 text-left w-8">
                  {(() => {
                    const wipsConCosto = desgloseData.desgloses_total.filter((d) => d.textil_por_prenda > 0 || d.manufactura_por_prenda > 0);
                    return (
                      <input
                        type="checkbox"
                        checked={selectedWips.size === wipsConCosto.length && wipsConCosto.length > 0}
                        onChange={toggleSelectAllWips}
                      />
                    );
                  })()}
                </th>
                <th className="px-4 py-3 text-left font-semibold text-gray-600">WIP ID - Nombre</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-600">Grupo</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-600">Total Prendas</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-600">Textil/Prenda</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-600">Manufactura/Prenda</th>
                <th className="px-4 py-3 text-center font-semibold text-gray-600">Factor</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-600">Textil Ajustado</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-600">Manufactura Ajustada</th>
              </tr>
            </thead>
            <tbody>
              {desgloseData.desgloses_total
                .filter((desglose) => desglose.textil_por_prenda > 0 || desglose.manufactura_por_prenda > 0)
                .map((desglose, idx) => (
                <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selectedWips.has(desglose.wip_id)}
                      onChange={() => toggleWipSelection(desglose.wip_id)}
                    />
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-900 font-semibold">
                    {desglose.wip_id} - {NOMBRES_WIPS[desglose.wip_id] || "Desconocido"}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                        desglose.grupo_wip === "textil"
                          ? "bg-blue-100 text-blue-800"
                          : desglose.grupo_wip === "manufactura"
                            ? "bg-orange-100 text-orange-800"
                            : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {desglose.grupo_wip === "textil" ? "Textil" : desglose.grupo_wip === "manufactura" ? "Manufactura" : "Otro"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-gray-900">{desglose.total_prendas.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right text-gray-900">${desglose.textil_por_prenda.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right text-gray-900">${desglose.manufactura_por_prenda.toFixed(2)}</td>
                  <td className="px-4 py-3 text-center">
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      defaultValue="1"
                      value={factoresWip[desglose.wip_id] !== undefined ? factoresWip[desglose.wip_id] : 1}
                      onChange={(e) => handleFactorChange(desglose.wip_id, parseFloat(e.target.value) || 1)}
                      className="w-16 px-2 py-1 border border-gray-300 rounded text-center text-sm"
                    />
                  </td>
                  <td className="px-4 py-3 text-right text-gray-900 bg-blue-50 font-semibold">
                    ${(desglose.textil_por_prenda * (factoresWip[desglose.wip_id] || 1)).toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-900 bg-orange-50 font-semibold">
                    ${(desglose.manufactura_por_prenda * (factoresWip[desglose.wip_id] || 1)).toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pie de tabla con resumen total */}
        <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
          {(() => {
            const wipsConCosto = desgloseData.desgloses_total.filter((d) => d.textil_por_prenda > 0 || d.manufactura_por_prenda > 0);
            return (
              <p className="text-xs text-gray-600">
                OPs analizadas: <strong>{desgloseData.ops_analizadas}</strong> | WIPs con costo: <strong>{wipsConCosto.length}</strong> (de {desgloseData.desgloses_total.length} totales)
              </p>
            );
          })()}
        </div>
      </div>
    </div>
  );
});

WipDesgloseTableComponent.displayName = "WipDesgloseTable";

export const WipDesgloseTable = WipDesgloseTableComponent;
