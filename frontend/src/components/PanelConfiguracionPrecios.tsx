import React from "react";
import { RotateCcw, Settings2 } from "lucide-react";

// Estilos CSS para inputs numéricos
const inputStyles = `
  input[type="number"] {
    font-size: 0.875rem;
    font-weight: 600;
  }

  /* Eliminar spinners por defecto y usar custom */
  input[type="number"]::-webkit-outer-spin-button,
  input[type="number"]::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
  }

  input[type="number"] {
    -moz-appearance: textfield;
  }

  /* Focus styles */
  input[type="number"]:focus {
    outline: none;
  }
`;

export interface ParametrosAjustables {
  margenBase: number;
  pesoFactorEsfuerzo: number;
  pesoFactorMarca: number;
}

interface PanelConfiguracionPreciosProps {
  parametros: ParametrosAjustables;
  onParametrosChange: (parametros: ParametrosAjustables) => void;
  isOpen: boolean;
  onToggle: () => void;
  precioPreview?: number;
  vectorPreview?: number;
}

const DEFAULTS: ParametrosAjustables = {
  margenBase: 0.15,
  pesoFactorEsfuerzo: 1.0,
  pesoFactorMarca: 1.0,
};

export const PanelConfiguracionPrecios: React.FC<PanelConfiguracionPreciosProps> = ({
  parametros,
  onParametrosChange,
  isOpen,
  onToggle,
  precioPreview,
  vectorPreview,
}) => {
  const handleMargenChange = (value: number) => {
    onParametrosChange({
      ...parametros,
      margenBase: Math.max(0, Math.min(1, value)),
    });
  };

  const handlePesoEsfuerzoChange = (value: number) => {
    onParametrosChange({
      ...parametros,
      pesoFactorEsfuerzo: Math.max(0.1, Math.min(3.0, value)),
    });
  };

  const handlePesoMarcaChange = (value: number) => {
    onParametrosChange({
      ...parametros,
      pesoFactorMarca: Math.max(0.1, Math.min(3.0, value)),
    });
  };

  const handleRestaurar = () => {
    onParametrosChange(DEFAULTS);
  };

  return (
    <>
      <style>{inputStyles}</style>
      <div className="border-t-2 border-red-300 pt-4 mt-4">
      {/* Botón para expandir/contraer */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-3 rounded-lg bg-red-50 hover:bg-red-100 transition-colors mb-3"
      >
        <div className="flex items-center gap-2">
          <Settings2 className="h-5 w-5 text-red-700" />
          <span className="font-semibold text-red-900">Configurar Parámetros de Precio</span>
        </div>
        <span className="text-red-700 text-lg">
          {isOpen ? "−" : "+"}
        </span>
      </button>

      {/* Panel colapsable */}
      {isOpen && (
        <div className="space-y-4 p-4 bg-red-50 rounded-lg border border-red-200">
          {/* Margen Base */}
          <div>
            <label className="font-semibold text-red-900 block mb-2">
              Margen Base (%)
            </label>
            <div className="flex gap-2 items-center">
              <input
                type="number"
                min="0"
                max="100"
                step="0.01"
                value={(parametros.margenBase * 100).toFixed(2)}
                onChange={(e) => handleMargenChange(parseFloat(e.target.value) / 100)}
                className="flex-1 px-3 py-2 border-2 border-red-300 rounded-lg focus:border-red-600 transition-colors bg-white"
              />
              <span className="text-sm font-semibold text-red-600 min-w-fit">%</span>
            </div>
            <div className="text-xs text-red-600 mt-1">
              Rango: 0% a 100% (default: 15%) | Incremento: 0.01%
            </div>
          </div>

          {/* Peso Factor Esfuerzo */}
          <div>
            <label className="font-semibold text-orange-900 block mb-2">
              Peso Factor Esfuerzo
            </label>
            <div className="flex gap-2 items-center">
              <input
                type="number"
                min="0.1"
                max="3.0"
                step="0.01"
                value={parametros.pesoFactorEsfuerzo.toFixed(2)}
                onChange={(e) => handlePesoEsfuerzoChange(parseFloat(e.target.value))}
                className="flex-1 px-3 py-2 border-2 border-orange-300 rounded-lg focus:border-orange-600 transition-colors bg-white"
              />
              <span className="text-sm font-semibold text-orange-600 min-w-fit">x</span>
            </div>
            <div className="text-xs text-orange-600 mt-1">
              Rango: 0.1x a 3.0x (default: 1.0x) | Incremento: 0.01x
            </div>
          </div>

          {/* Peso Factor Marca */}
          <div>
            <label className="font-semibold text-yellow-900 block mb-2">
              Peso Factor Marca
            </label>
            <div className="flex gap-2 items-center">
              <input
                type="number"
                min="0.1"
                max="3.0"
                step="0.01"
                value={parametros.pesoFactorMarca.toFixed(2)}
                onChange={(e) => handlePesoMarcaChange(parseFloat(e.target.value))}
                className="flex-1 px-3 py-2 border-2 border-yellow-300 rounded-lg focus:border-yellow-600 transition-colors bg-white"
              />
              <span className="text-sm font-semibold text-yellow-600 min-w-fit">x</span>
            </div>
            <div className="text-xs text-yellow-600 mt-1">
              Rango: 0.1x a 3.0x (default: 1.0x) | Incremento: 0.01x
            </div>
          </div>

          {/* Preview */}
          {vectorPreview !== undefined && precioPreview !== undefined && (
            <div className="p-3 bg-white rounded-lg border border-red-300 space-y-2">
              <div className="text-xs font-semibold text-gray-600 uppercase">
                Preview del Cálculo
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-700">Vector Ajustado:</span>
                <span className="font-bold text-red-600">{vectorPreview.toFixed(3)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-700">Precio Final:</span>
                <span className="font-bold text-lg text-red-700">
                  ${precioPreview.toFixed(2)}/prenda
                </span>
              </div>
            </div>
          )}

          {/* Botón Restaurar */}
          <button
            onClick={handleRestaurar}
            className="w-full flex items-center justify-center gap-2 p-2 bg-red-200 hover:bg-red-300 text-red-900 rounded-lg font-semibold transition-colors text-sm"
          >
            <RotateCcw className="h-4 w-4" />
            Restaurar Valores por Defecto
          </button>
        </div>
      )}
    </div>
    </>
  );
};
