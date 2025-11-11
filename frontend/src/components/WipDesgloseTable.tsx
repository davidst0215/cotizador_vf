"use client";

import React, { useState, useCallback, useMemo } from "react";
import { AlertCircle, TrendingUp } from "lucide-react";

// Interfaces para los datos de desglose WIP
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
}

interface WipDesgloseTableProps {
  codigoEstilo: string;
  versionCalculo: string;
  codOrdpros: string[]; // OPs seleccionadas de OpsSelectionTable
  onError?: (error: string) => void;
  onCostosCalculados?: (textilPorPrenda: number, manufacturaPorPrenda: number) => void;
}

export const WipDesgloseTable = React.memo(
  ({ codigoEstilo, versionCalculo, codOrdpros, onError, onCostosCalculados }: WipDesgloseTableProps) => {
    const [desgloseData, setDesgloseData] = useState<WipDesgloseResponse | null>(null);
    const [cargando, setCargando] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Cargar desglose WIP cuando las OPs seleccionadas cambian
    const cargarDesgloseWip = useCallback(async () => {
      if (!codOrdpros || codOrdpros.length === 0) {
        setError("No hay OPs seleccionadas para analizar");
        setDesgloseData(null);
        return;
      }

      setCargando(true);
      setError(null);

      try {
        const response = await fetch("http://localhost:8000/desglose-wip-ops", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            cod_ordpros: codOrdpros,
            version_calculo: versionCalculo,
          }),
        });

        if (!response.ok) {
          throw new Error(`Error ${response.status}: No se pudo obtener el desglose WIP`);
        }

        const data: WipDesgloseResponse = await response.json();
        setDesgloseData(data);

        if (data.desgloses_total.length === 0) {
          setError("No hay datos WIP disponibles para las OPs seleccionadas");
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : "Error desconocido";
        setError(errorMsg);
        if (onError) onError(errorMsg);
      } finally {
        setCargando(false);
      }
    }, [codOrdpros, versionCalculo, onError]);

    // Cargar desglose cuando las OPs cambian
    React.useEffect(() => {
      if (codOrdpros.length > 0) {
        cargarDesgloseWip();
      }
    }, [codOrdpros, cargarDesgloseWip]);

    // Calcular totales por grupo
    const totalesPorGrupo = useMemo(() => {
      if (!desgloseData) return { textil: 0, manufactura: 0 };

      const totalTextil = desgloseData.desgloses_textil.reduce(
        (sum, d) => sum + d.textil_por_prenda,
        0
      );
      const totalManufactura = desgloseData.desgloses_manufactura.reduce(
        (sum, d) => sum + d.manufactura_por_prenda,
        0
      );

      return {
        textil: totalTextil,
        manufactura: totalManufactura,
      };
    }, [desgloseData]);

    // Notificar al padre cuando se calculen los costos
    React.useEffect(() => {
      if (onCostosCalculados && totalesPorGrupo.textil > 0 && totalesPorGrupo.manufactura > 0) {
        onCostosCalculados(totalesPorGrupo.textil, totalesPorGrupo.manufactura);
      }
    }, [totalesPorGrupo, onCostosCalculados]);

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
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm text-yellow-800">{error}</p>
              {codOrdpros.length > 0 && (
                <button
                  onClick={cargarDesgloseWip}
                  className="mt-2 px-3 py-1 text-xs bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors"
                >
                  Reintentar
                </button>
              )}
            </div>
          </div>
        </div>
      );
    }

    if (!desgloseData || desgloseData.desgloses_total.length === 0) {
      return null;
    }

    return (
      <div className="space-y-4">
        {/* Resumen de costos por grupo */}
        <div className="grid grid-cols-2 gap-4">
          {/* Textil */}
          {desgloseData.desgloses_textil.length > 0 && (
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-4 w-4 text-blue-600" />
                <h4 className="text-sm font-semibold text-blue-900">Textil Por Prenda</h4>
              </div>
              <p className="text-2xl font-bold text-blue-900">
                ${totalesPorGrupo.textil.toFixed(2)}
              </p>
              <p className="text-xs text-blue-700 mt-1">
                {desgloseData.desgloses_textil.length} WIPs
              </p>
            </div>
          )}

          {/* Manufactura */}
          {desgloseData.desgloses_manufactura.length > 0 && (
            <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4 border border-orange-200">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-4 w-4 text-orange-600" />
                <h4 className="text-sm font-semibold text-orange-900">Manufactura Por Prenda</h4>
              </div>
              <p className="text-2xl font-bold text-orange-900">
                ${totalesPorGrupo.manufactura.toFixed(2)}
              </p>
              <p className="text-xs text-orange-700 mt-1">
                {desgloseData.desgloses_manufactura.length} WIPs
              </p>
            </div>
          )}
        </div>

        {/* Tabla de desglose detallado */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
            <h4 className="text-sm font-semibold text-gray-700">Desglose por WIP</h4>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">WIP ID</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Grupo</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-600">Total Prendas</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-600">Textil/Prenda</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-600">Manufactura/Prenda</th>
                </tr>
              </thead>
              <tbody>
                {desgloseData.desgloses_total.map((desglose, idx) => (
                  <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-mono text-gray-900 font-semibold">{desglose.wip_id}</td>
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
                        {desglose.grupo_wip === "textil"
                          ? "Textil"
                          : desglose.grupo_wip === "manufactura"
                          ? "Manufactura"
                          : "Otro"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-gray-900">
                      {desglose.total_prendas.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-900">
                      ${desglose.textil_por_prenda.toFixed(4)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-900">
                      ${desglose.manufactura_por_prenda.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pie de tabla con resumen total */}
          <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
            <p className="text-xs text-gray-600">
              OPs analizadas: <strong>{desgloseData.ops_analizadas}</strong> |
              WIPs encontrados: <strong>{desgloseData.desgloses_total.length}</strong>
            </p>
          </div>
        </div>
      </div>
    );
  }
);

WipDesgloseTable.displayName = "WipDesgloseTable";
