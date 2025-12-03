import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { X, Search, TrendingUp, ArrowUp, ArrowDown, BarChart3 } from "lucide-react";

interface PrecioHistorico {
  fecha: string;
  precio: number;
  tipo_material?: string;
  descripcion?: string;
  unidad_medida?: string;
  fuente?: string;
}

interface CompraHistorico {
  fecha: string;
  precio: number;
  cantidad_comprada?: number;
  importe?: number;
  costo_kg?: number;
}

interface HistoricoData {
  cod_material: string;
  tipo_material: string | null;
  descripcion: string | null;
  precios_almacen: PrecioHistorico[];
  costos_compras?: CompraHistorico[];
  disponibles: string[];
  total_registros: number;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  basePath?: string;
  codigoMaterialInicial?: string;
}

const HistoricoPreciosModal: React.FC<Props> = ({
  isOpen,
  onClose,
  basePath = "",
  codigoMaterialInicial = "",
}) => {
  const [codigoMaterial, setCodigoMaterial] = useState("");
  const [historicoData, setHistoricoData] = useState<HistoricoData | null>(
    null
  );
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  // Cuando se abre el modal con un código inicial, pre-llenarlo y buscar automáticamente
  useEffect(() => {
    if (isOpen && codigoMaterialInicial) {
      setCodigoMaterial(codigoMaterialInicial);
    }
  }, [isOpen, codigoMaterialInicial]);

  const buscarHistorico = async () => {
    if (!codigoMaterial.trim()) {
      setError("Por favor ingresa un código de material");
      return;
    }

    setCargando(true);
    setError("");

    try {
      // Usar basePath del cotizador para proxy
      const url = `${basePath || ''}/api/proxy/historico-precios/${encodeURIComponent(
        codigoMaterial.trim()
      )}`;

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data: HistoricoData = await response.json();

      if ((!data.precios_almacen || data.precios_almacen.length === 0) && (!data.costos_compras || data.costos_compras.length === 0)) {
        setError(`No se encontró histórico para: ${codigoMaterial}`);
        setHistoricoData(null);
      } else {
        // Curva 1: Agrupar precios de almacén por mes
        const preciosAgrupados: { [key: string]: number[] } = {};
        data.precios_almacen?.forEach((row) => {
          const fecha = row.fecha.substring(0, 7);
          if (!preciosAgrupados[fecha]) {
            preciosAgrupados[fecha] = [];
          }
          preciosAgrupados[fecha].push(row.precio);
        });

        // Convertir a array de datos mensuales (Precios Almacén)
        const preciosPromedios = Object.entries(preciosAgrupados)
          .map(([mes, precios]) => ({
            fecha: mes,
            precio: precios.reduce((a, b) => a + b, 0) / precios.length,
          }))
          .sort((a, b) => a.fecha.localeCompare(b.fecha));

        // Curva 2: Agrupar costos de compras por mes
        const comprasAgrupadas: { [key: string]: number[] } = {};
        data.costos_compras?.forEach((row) => {
          const fecha = row.fecha.substring(0, 7);
          if (!comprasAgrupadas[fecha]) {
            comprasAgrupadas[fecha] = [];
          }
          comprasAgrupadas[fecha].push(row.precio);
        });

        // Convertir a array de datos mensuales (Costos Compras)
        const comprasPromedios = Object.entries(comprasAgrupadas)
          .map(([mes, precios]) => ({
            fecha: mes,
            precio: precios.reduce((a, b) => a + b, 0) / precios.length,
          }))
          .sort((a, b) => a.fecha.localeCompare(b.fecha));

        setHistoricoData({
          ...data,
          precios_almacen: preciosPromedios as any,
          costos_compras: comprasPromedios as any,
        });
        setError("");
      }
    } catch (err) {
      setError(`Error al buscar: ${err instanceof Error ? err.message : String(err)}`);
      setHistoricoData(null);
    } finally {
      setCargando(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      buscarHistorico();
    }
  };

  if (!isOpen) return null;

  // Paleta de colores del proyecto - basada en #821417
  const colors = {
    primary: "#821417",      // Rojo profundo del proyecto
    primaryLight: "#C41E3A", // Rojo más claro
    primaryDark: "#5C0F0F",  // Rojo muy oscuro
    primaryVeryLight: "#F5E6E8", // Fondo claro
    chart: "#821417",        // Para el gráfico
    chartLight: "#C41E3A",   // Variante clara
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-11/12 max-w-6xl" style={{ aspectRatio: '16/9', maxHeight: '85vh', overflowY: 'auto' }}>
        {/* Header */}
        <div
          className="sticky top-0 text-white p-6 flex items-center justify-between"
          style={{
            background: `linear-gradient(to right, ${colors.primary}, ${colors.primaryLight})`
          }}
        >
          <h2 className="text-2xl font-bold">Histórico de Precios</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg transition-colors hover:opacity-80"
            style={{ backgroundColor: colors.primaryDark }}
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="h-full flex flex-col p-4 gap-4">
          {/* Búsqueda */}
          <div className="flex gap-2">
            <div className="flex-1">
              <label className="block text-xs font-semibold mb-1" style={{ color: colors.primary }}>
                Código de Material
              </label>
              <input
                type="text"
                value={codigoMaterial}
                onChange={(e) => setCodigoMaterial(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ej: C5007JB001"
                className="w-full px-3 py-2 border rounded-lg focus:outline-none text-sm"
                style={{
                  borderColor: colors.primaryLight,
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = colors.primary;
                  e.target.style.boxShadow = `0 0 0 2px ${colors.primaryVeryLight}`;
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = colors.primaryLight;
                  e.target.style.boxShadow = "none";
                }}
              />
            </div>
            <button
              onClick={buscarHistorico}
              disabled={cargando}
              className="px-4 py-2 text-white rounded-lg transition-colors flex items-center gap-2 font-medium text-sm self-end"
              style={{
                backgroundColor: colors.primary,
                opacity: cargando ? 0.6 : 1,
                cursor: cargando ? "not-allowed" : "pointer",
              }}
              onMouseEnter={(e) => {
                if (!cargando) e.currentTarget.style.backgroundColor = colors.primaryDark;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = colors.primary;
              }}
            >
              <Search className="h-4 w-4" />
              {cargando ? "Buscando..." : "Buscar"}
            </button>
          </div>

          {/* Error */}
          {error && (
            <div
              className="p-3 border rounded-lg text-xs font-medium"
              style={{
                backgroundColor: colors.primaryVeryLight,
                borderColor: colors.primaryLight,
                color: colors.primaryDark,
              }}
            >
              {error}
            </div>
          )}

          {/* Datos */}
          {historicoData && (historicoData.precios_almacen.length > 0 || historicoData.costos_compras?.length! > 0) && (
            <div className="flex-1 flex flex-col gap-4 min-h-0">
              {/* Estadísticas - Franja Superior */}
              <div className="flex gap-3 rounded-lg p-4" style={{ backgroundColor: colors.primaryVeryLight }}>
                {/* Máximo */}
                <div className="flex-1 flex items-center gap-3 p-3 rounded-lg bg-white border" style={{ borderColor: colors.primaryLight }}>
                  <ArrowUp className="h-6 w-6" style={{ color: colors.primary }} />
                  <div>
                    <p className="text-xs font-semibold" style={{ color: colors.primary }}>Máximo</p>
                    <p className="text-lg font-bold" style={{ color: colors.primary }}>
                      ${Math.max(
                        ...(historicoData.precios_almacen.length > 0 ? historicoData.precios_almacen.map((d) => d.precio) : [0]),
                        ...(historicoData.costos_compras?.length! > 0 ? historicoData.costos_compras!.map((d) => d.precio) : [0])
                      ).toFixed(4)}
                    </p>
                  </div>
                </div>
                {/* Promedio */}
                <div className="flex-1 flex items-center gap-3 p-3 rounded-lg bg-white border" style={{ borderColor: colors.primaryLight }}>
                  <BarChart3 className="h-6 w-6" style={{ color: colors.primary }} />
                  <div>
                    <p className="text-xs font-semibold" style={{ color: colors.primary }}>Promedio</p>
                    <p className="text-lg font-bold" style={{ color: colors.primary }}>
                      ${(
                        (historicoData.precios_almacen.reduce((sum, d) => sum + d.precio, 0) +
                          (historicoData.costos_compras?.reduce((sum, d) => sum + d.precio, 0) || 0)) /
                        (historicoData.precios_almacen.length + (historicoData.costos_compras?.length || 0))
                      ).toFixed(4)}
                    </p>
                  </div>
                </div>
                {/* Mínimo */}
                <div className="flex-1 flex items-center gap-3 p-3 rounded-lg bg-white border" style={{ borderColor: colors.primaryLight }}>
                  <ArrowDown className="h-6 w-6" style={{ color: colors.primary }} />
                  <div>
                    <p className="text-xs font-semibold" style={{ color: colors.primary }}>Mínimo</p>
                    <p className="text-lg font-bold" style={{ color: colors.primary }}>
                      ${Math.min(
                        ...(historicoData.precios_almacen.length > 0 ? historicoData.precios_almacen.map((d) => d.precio) : [Infinity]),
                        ...(historicoData.costos_compras?.length! > 0 ? historicoData.costos_compras!.map((d) => d.precio) : [Infinity])
                      ).toFixed(4)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Chart - Ancho completo */}
              <div
                className="flex-1 rounded-lg p-3"
                style={{
                  backgroundColor: "#fff",
                  border: `1px solid ${colors.primaryLight}`
                }}
              >
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={historicoData.costos_compras && historicoData.costos_compras.length > 0
                      ? historicoData.precios_almacen.map((d, i) => ({
                          ...d,
                          precio_compra: historicoData.costos_compras?.[i]?.precio
                        }))
                      : historicoData.precios_almacen
                    }
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis
                      dataKey="fecha"
                      tick={{ fontSize: 11 }}
                      stroke="#9ca3af"
                    />
                    <YAxis
                      tick={{ fontSize: 11 }}
                      stroke="#9ca3af"
                      label={{
                        value: `Precio (${historicoData.precios_almacen[0]?.unidad_medida || "UNIDAD"})`,
                        angle: -90,
                        position: "insideLeft",
                        style: { textAnchor: "middle", fontSize: 11 },
                      }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#fff",
                        border: `2px solid ${colors.primary}`,
                        borderRadius: "8px",
                        fontSize: 12,
                      }}
                      formatter={(value) =>
                        `$${typeof value === "number" ? value.toFixed(4) : value}`
                      }
                      labelFormatter={(label) => `Mes: ${label}`}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="precio"
                      stroke={colors.primary}
                      strokeWidth={2}
                      dot={{ fill: colors.primary, r: 4 }}
                      activeDot={{ r: 6 }}
                      name="Costo Almacén (Requerido)"
                    />
                    {historicoData.costos_compras && historicoData.costos_compras.length > 0 && (
                      <Line
                        type="monotone"
                        dataKey="precio_compra"
                        stroke={colors.chartLight}
                        strokeWidth={2}
                        dot={{ fill: colors.chartLight, r: 4 }}
                        activeDot={{ r: 6 }}
                        name="Costo Órdenes Compra (Real)"
                        connectNulls
                      />
                    )}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Estado inicial */}
          {!historicoData && !error && !cargando && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <TrendingUp className="h-16 w-16 mx-auto mb-3" style={{ color: colors.primaryLight }} />
                <p style={{ color: colors.primary }} className="font-medium">
                  Ingresa un código de material para ver su histórico de precios
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HistoricoPreciosModal;
