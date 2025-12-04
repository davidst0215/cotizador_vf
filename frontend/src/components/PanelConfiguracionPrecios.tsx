import React from "react";
import { RotateCcw, Settings2 } from "lucide-react";

// Estilos CSS para los sliders
const sliderStyles = `
  input[type="range"] {
    -webkit-appearance: none;
    appearance: none;
    width: 100%;
    height: 8px;
    border-radius: 5px;
    background: inherit;
    outline: none;
    cursor: pointer;
  }

  input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: currentColor;
    cursor: grab;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
    transition: all 0.2s ease;
  }

  input[type="range"]::-webkit-slider-thumb:active {
    cursor: grabbing;
    transform: scale(1.2);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
  }

  input[type="range"]::-moz-range-thumb {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: currentColor;
    cursor: grab;
    border: none;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
    transition: all 0.2s ease;
  }

  input[type="range"]::-moz-range-thumb:active {
    cursor: grabbing;
    transform: scale(1.2);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
  }

  input[type="range"]::-moz-range-track {
    background: transparent;
    border: none;
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
      <style>{sliderStyles}</style>
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
            <div className="flex justify-between items-center mb-2">
              <label className="font-semibold text-red-900">
                Margen Base (%)
              </label>
              <span className="text-lg font-bold text-red-700">
                {(parametros.margenBase * 100).toFixed(2)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="0.01"
              value={parametros.margenBase * 100}
              onChange={(e) => handleMargenChange(parseFloat(e.target.value) / 100)}
              className="w-full h-2 bg-red-200 rounded-lg appearance-none cursor-pointer accent-red-600"
            />
            <div className="text-xs text-red-600 mt-1">
              Rango: 0% a 100% (default: 15%)
            </div>
          </div>

          {/* Peso Factor Esfuerzo */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="font-semibold text-red-900">
                Peso Factor Esfuerzo
              </label>
              <span className="text-lg font-bold text-red-700">
                {parametros.pesoFactorEsfuerzo.toFixed(2)}x
              </span>
            </div>
            <input
              type="range"
              min="0.1"
              max="3.0"
              step="0.05"
              value={parametros.pesoFactorEsfuerzo}
              onChange={(e) => handlePesoEsfuerzoChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-orange-200 rounded-lg appearance-none cursor-pointer accent-orange-600"
            />
            <div className="text-xs text-orange-600 mt-1">
              Rango: 0.1x a 3.0x (default: 1.0x)
            </div>
          </div>

          {/* Peso Factor Marca */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="font-semibold text-red-900">
                Peso Factor Marca
              </label>
              <span className="text-lg font-bold text-red-700">
                {parametros.pesoFactorMarca.toFixed(2)}x
              </span>
            </div>
            <input
              type="range"
              min="0.1"
              max="3.0"
              step="0.05"
              value={parametros.pesoFactorMarca}
              onChange={(e) => handlePesoMarcaChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-yellow-200 rounded-lg appearance-none cursor-pointer accent-yellow-600"
            />
            <div className="text-xs text-yellow-600 mt-1">
              Rango: 0.1x a 3.0x (default: 1.0x)
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
