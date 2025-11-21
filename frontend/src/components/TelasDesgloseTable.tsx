"use client";

import React, { useState, useCallback, useEffect, forwardRef, useRef, useImperativeHandle } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

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
}

export interface TelasDesgloseTableRef {
  getSelectedTelas: () => TelaConFactor[];
  getTotalCostoTelas: () => number;
}

const TelasDesgloseTableComponent = forwardRef<TelasDesgloseTableRef, TelasDesgloseTableProps>(({
  versionCalculo,
  estiloCliente,
  codigoEstilo,
  clienteMarca,
  tipoPrenda,
  onError,
  telasPreseleccionadas = [],
}, ref) => {
  const [telasData, setTelasData] = useState<Tela[]>([]);
  const [totalOps, setTotalOps] = useState<number>(0);
  const [fechaCorrida, setFechaCorrida] = useState<string>("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTelas, setSelectedTelas] = useState<Set<string>>(new Set(telasPreseleccionadas));
  const [factoreTelaLocal, setFactoreTelaLocal] = useState<Record<string, number>>({}); // (tela_codigo) -> factor
  const [factoresInputLocal, setFactoresInputLocal] = useState<Record<string, string>>({}); // (tela_codigo) -> factor (para typing)
  const [sortField, setSortField] = useState<"tela_descripcion" | "combinacion" | "precio_por_kg_real" | "frecuencia_ops">("tela_descripcion");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const [busqueda, setBusqueda] = useState<string>("");

  // ✨ Ref para almacenar factoreTelaLocal sin crear dependencias
  const factoreTelaRef = useRef<Record<string, number>>(factoreTelaLocal);

  // ✨ Sincronizar el Ref cuando los factores locales cambian
  useEffect(() => {
    factoreTelaRef.current = factoreTelaLocal;
  }, [factoreTelaLocal]);

  // ✨ Sincronizar el estado local de inputs cuando factoreTelaLocal cambia
  useEffect(() => {
    const newLocalState: Record<string, string> = {};
    Object.entries(factoreTelaLocal).forEach(([telaCodigo, value]) => {
      newLocalState[telaCodigo] = value.toString();
    });
    setFactoresInputLocal(newLocalState);
  }, [factoreTelaLocal]);

  // Sincronizar selectedTelas cuando telasPreseleccionadas cambia
  useEffect(() => {
    if (telasPreseleccionadas.length > 0) {
      setSelectedTelas(new Set(telasPreseleccionadas));
    }
  }, [telasPreseleccionadas]);

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

        const url = `http://localhost:8000/obtener-telas-detalladas?${params.toString()}`;
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Error ${response.status}: No se pudieron cargar las telas`);
        }

        const data: TelasResponse = await response.json();
        setTelasData(data.telas || []);
        setTotalOps(data.total_ops || 0);
        setFechaCorrida(data.fecha_corrida || "");

        // Inicializar factores en 1.0 para todas las telas
        const factoresIniciales: Record<string, number> = {};
        (data.telas || []).forEach((tela) => {
          const clave = tela.tela_codigo;
          factoresIniciales[clave] = 1.0;
        });
        setFactoreTelaLocal(factoresIniciales);

        // Si no hay preseleccionadas, seleccionar todas por defecto
        if (telasPreseleccionadas.length === 0) {
          setSelectedTelas(new Set(data.telas.map((t) => t.tela_codigo)));
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
  }, [versionCalculo, estiloCliente, codigoEstilo, clienteMarca, tipoPrenda]); // 🔒 NO incluir onError ni telasPreseleccionadas

  const toggleSelection = useCallback((clave: string) => {
    setSelectedTelas((prev) => {
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
    if (selectedTelas.size === telasData.length) {
      setSelectedTelas(new Set());
    } else {
      setSelectedTelas(new Set(telasData.map((t) => t.tela_codigo)));
    }
  }, [telasData, selectedTelas.size]);

  // ✨ Actualizar factor con soporte para typing intermedio
  const handleFactorChange = useCallback((clave: string, value: string) => {
    setFactoresInputLocal((prev) => ({
      ...prev,
      [clave]: value,
    }));

    // Intentar convertir a número y actualizar el valor real
    const numValue = parseFloat(value);
    if (!isNaN(numValue) && numValue >= 0.1 && numValue <= 10) {
      setFactoreTelaLocal((prev) => ({
        ...prev,
        [clave]: numValue,
      }));
    }
  }, []);

  // ✨ Telas con factor y costos ajustados - cálculo en cascada
  const telasConFactor: TelaConFactor[] = telasData.map((tela) => {
    const clave = tela.tela_codigo;
    const factor = factoreTelaLocal[clave] || 1.0;

    // Cálculo en cascada:
    // 1. precio_por_kg_ajustado = precio_por_kg × factor
    const precio_por_kg_ajustado = tela.precio_por_kg_real * factor;

    // 2. costo_por_prenda_ajustado = precio_por_kg_ajustado × kg_por_prenda
    const costo_por_prenda_ajustado = precio_por_kg_ajustado * tela.kg_por_prenda;

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
      tela.tela_descripcion.toLowerCase().includes(term) ||
      tela.combinacion.toLowerCase().includes(term) ||
      tela.color.toLowerCase().includes(term)
    );
  });

  // ✨ Ordenar telas
  const telasOrdenadas = [...telasFiltradas].sort((a, b) => {
    let aValue = a[sortField] ?? 0;
    let bValue = b[sortField] ?? 0;

    if (typeof aValue === "string") {
      return sortDirection === "asc"
        ? aValue.localeCompare(bValue as string)
        : (bValue as string).localeCompare(aValue);
    }

    return sortDirection === "asc"
      ? (aValue as number) - (bValue as number)
      : (bValue as number) - (aValue as number);
  });

  // ✨ Exponer métodos al componente padre
  useImperativeHandle(
    ref,
    () => ({
      getSelectedTelas: () => {
        return telasConFactor.filter((tela) => selectedTelas.has(tela.tela_codigo));
      },
      getTotalCostoTelas: () => {
        return telasConFactor
          .filter((tela) => selectedTelas.has(tela.tela_codigo))
          .reduce((sum, tela) => sum + tela.costo_por_prenda_ajustado, 0);
      },
    }),
    [telasConFactor, selectedTelas]
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
      {/* Búsqueda */}
      <div className="flex items-center gap-2 mb-4">
        <input
          type="text"
          placeholder="Buscar por código, descripción, combinación o color..."
          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
        />
        <span className="text-sm text-gray-600">
          {telasFiltradas.length} de {telasData.length}
        </span>
      </div>

      {/* Tabla */}
      <div className="overflow-x-auto border border-gray-300 rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 border-b border-gray-300">
            <tr>
              <th className="p-2 text-left">
                <input
                  type="checkbox"
                  checked={selectedTelas.size === telasData.length && telasData.length > 0}
                  onChange={toggleSelectAll}
                  className="cursor-pointer"
                />
              </th>
              <th
                className="p-2 text-left cursor-pointer hover:bg-gray-200"
                onClick={() => handleSort("tela_descripcion")}
              >
                <div className="flex items-center gap-1">
                  Descripción
                  {sortField === "tela_descripcion" && (
                    sortDirection === "asc" ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                  )}
                </div>
              </th>
              <th className="p-2 text-left">Combinación</th>
              <th className="p-2 text-left">Color</th>
              <th className="p-2 text-right">kg/prenda</th>
              <th
                className="p-2 text-right cursor-pointer hover:bg-gray-200"
                onClick={() => handleSort("precio_por_kg_real")}
              >
                <div className="flex items-center justify-end gap-1">
                  Precio/kg
                  {sortField === "precio_por_kg_real" && (
                    sortDirection === "asc" ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                  )}
                </div>
              </th>
              <th className="p-2 text-right">Factor</th>
              <th className="p-2 text-right">Precio/kg Ajustado</th>
              <th className="p-2 text-right">Costo/prenda</th>
              <th
                className="p-2 text-right cursor-pointer hover:bg-gray-200"
                onClick={() => handleSort("frecuencia_ops")}
              >
                <div className="flex items-center justify-end gap-1">
                  Freq.
                  {sortField === "frecuencia_ops" && (
                    sortDirection === "asc" ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                  )}
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {telasOrdenadas.map((tela) => (
              <tr key={tela.tela_codigo} className="border-b border-gray-200 hover:bg-gray-50">
                <td className="p-2">
                  <input
                    type="checkbox"
                    checked={selectedTelas.has(tela.tela_codigo)}
                    onChange={() => toggleSelection(tela.tela_codigo)}
                    className="cursor-pointer"
                  />
                </td>
                <td className="p-2">{tela.tela_descripcion}</td>
                <td className="p-2">{tela.combinacion}</td>
                <td className="p-2">{tela.color}</td>
                <td className="p-2 text-right">{tela.kg_por_prenda.toFixed(4)}</td>
                <td className="p-2 text-right">${tela.precio_por_kg_real.toFixed(2)}</td>
                <td className="p-2 text-right">
                  <input
                    type="number"
                    min="0.1"
                    max="10"
                    step="0.1"
                    value={factoresInputLocal[tela.tela_codigo] || "1.0"}
                    onChange={(e) => handleFactorChange(tela.tela_codigo, e.target.value)}
                    className="w-16 px-2 py-1 border border-gray-300 rounded text-right"
                  />
                </td>
                <td className="p-2 text-right">${tela.precio_por_kg_ajustado.toFixed(2)}</td>
                <td className="p-2 text-right font-semibold">${tela.costo_por_prenda_ajustado.toFixed(2)}</td>
                <td className="p-2 text-right">{tela.frecuencia_ops}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Info */}
      <div className="text-xs text-gray-600">
        {fechaCorrida && <p>Última actualización: {fechaCorrida}</p>}
        <p>Total OPs del estilo: {totalOps}</p>
      </div>
    </div>
  );
});

TelasDesgloseTableComponent.displayName = "TelasDesgloseTable";

export const TelasDesgloseTable = TelasDesgloseTableComponent;
