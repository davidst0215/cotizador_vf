import React, { useState, useEffect, useRef } from "react";
import { RotateCcw, Settings2, Plus, Minus } from "lucide-react";

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
  factorEsfuerzo: number;  // ✨ Reemplaza directamente el factor de esfuerzo
  factorMarca: number;     // ✨ Reemplaza directamente el factor de marca
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
  factorEsfuerzo: 1.0,
  factorMarca: 1.0,
};

// Componente helper para input numérico con estado local y botones de incremento/decremento
interface NumericInputProps {
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step: number;
  label: string;
  suffix: string;
  borderColor: string;
  buttonColor: string;
}

const NumericInput = React.memo(({
  value,
  onChange,
  min,
  max,
  step,
  label,
  suffix,
  borderColor,
  buttonColor,
}: NumericInputProps) => {
  const [localValue, setLocalValue] = useState<string>(value.toFixed(2));
  const prevValueRef = useRef<number>(value);

  // Sincronizar cuando el valor externo cambia significativamente
  useEffect(() => {
    if (Math.abs(value - prevValueRef.current) > step / 2) {
      prevValueRef.current = value;
      setLocalValue(value.toFixed(2));
    }
  }, [value, step]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVal = e.target.value;
    setLocalValue(newVal);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.currentTarget.blur();
    }
  };

  const handleBlur = () => {
    const numVal = parseFloat(localValue);
    if (isNaN(numVal)) {
      setLocalValue(value.toFixed(2));
    } else {
      const clamped = Math.max(min, Math.min(max, numVal));
      setLocalValue(clamped.toFixed(2));
      onChange(clamped);
    }
  };

  const handleIncrement = () => {
    const numVal = parseFloat(localValue) || min;
    const newVal = Math.min(max, numVal + step);
    setLocalValue(newVal.toFixed(2));
    onChange(newVal);
  };

  const handleDecrement = () => {
    const numVal = parseFloat(localValue) || max;
    const newVal = Math.max(min, numVal - step);
    setLocalValue(newVal.toFixed(2));
    onChange(newVal);
  };

  return (
    <div>
      <label className={`font-semibold block mb-2`} style={{ color: borderColor }}>
        {label}
      </label>
      <div className="flex gap-1 items-center">
        <button
          type="button"
          onClick={handleDecrement}
          className="px-2 py-2 rounded-lg transition-colors hover:opacity-75"
          style={{ backgroundColor: buttonColor, color: "white" }}
        >
          <Minus className="h-4 w-4" />
        </button>
        <input
          type="number"
          autoComplete="off"
          min={min}
          max={max}
          step={step}
          value={localValue}
          onChange={handleChange}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          className="flex-1 px-3 py-2 border-2 rounded-lg focus:outline-none focus:ring-2 transition-colors bg-white"
          style={{
            borderColor: borderColor,
            "--tw-ring-color": borderColor,
          } as React.CSSProperties}
        />
        <span className="text-sm font-semibold min-w-fit" style={{ color: borderColor }}>
          {suffix}
        </span>
        <button
          type="button"
          onClick={handleIncrement}
          className="px-2 py-2 rounded-lg transition-colors hover:opacity-75"
          style={{ backgroundColor: buttonColor, color: "white" }}
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>
      <div className="text-xs mt-1" style={{ color: borderColor }}>
        Rango: {min} a {max} | Incremento: {step}
      </div>
    </div>
  );
});

NumericInput.displayName = "NumericInput";

// Componente compacto para uso inline en tarjetas
interface CompactNumericInputProps {
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step: number;
  borderColor: string;
  buttonColor: string;
}

export const CompactNumericInput = React.memo(({
  value,
  onChange,
  min,
  max,
  step,
  borderColor,
  buttonColor,
}: CompactNumericInputProps) => {
  const [localValue, setLocalValue] = useState<string>(value.toFixed(2));
  const prevValueRef = useRef<number>(value);

  useEffect(() => {
    if (Math.abs(value - prevValueRef.current) > step / 2) {
      prevValueRef.current = value;
      setLocalValue(value.toFixed(2));
    }
  }, [value, step]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVal = e.target.value;
    setLocalValue(newVal);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.currentTarget.blur();
    }
  };

  const handleBlur = () => {
    const numVal = parseFloat(localValue);
    if (isNaN(numVal)) {
      setLocalValue(value.toFixed(2));
    } else {
      const clamped = Math.max(min, Math.min(max, numVal));
      setLocalValue(clamped.toFixed(2));
      onChange(clamped);
    }
  };

  const handleIncrement = () => {
    const numVal = parseFloat(localValue) || min;
    const newVal = Math.min(max, numVal + step);
    setLocalValue(newVal.toFixed(2));
    onChange(newVal);
  };

  const handleDecrement = () => {
    const numVal = parseFloat(localValue) || max;
    const newVal = Math.max(min, numVal - step);
    setLocalValue(newVal.toFixed(2));
    onChange(newVal);
  };

  return (
    <div className="flex gap-0.5 items-center">
      <button
        type="button"
        onClick={handleDecrement}
        className="p-1 rounded transition-colors hover:opacity-75"
        style={{ backgroundColor: buttonColor, color: "white" }}
        title="Disminuir"
      >
        <Minus className="h-3 w-3" />
      </button>
      <input
        type="number"
        autoComplete="off"
        min={min}
        max={max}
        step={step}
        value={localValue}
        onChange={handleChange}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        className="w-14 px-1 py-1 text-sm text-center border rounded focus:outline-none focus:ring-2 transition-colors bg-white font-semibold"
        style={{
          borderColor: borderColor,
          fontSize: "0.75rem",
        }}
      />
      <button
        type="button"
        onClick={handleIncrement}
        className="p-1 rounded transition-colors hover:opacity-75"
        style={{ backgroundColor: buttonColor, color: "white" }}
        title="Aumentar"
      >
        <Plus className="h-3 w-3" />
      </button>
    </div>
  );
});

CompactNumericInput.displayName = "CompactNumericInput";

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

  const handleFactorEsfuerzoChange = (value: number) => {
    onParametrosChange({
      ...parametros,
      factorEsfuerzo: Math.max(0.1, Math.min(3.0, value)),
    });
  };

  const handleFactorMarcaChange = (value: number) => {
    onParametrosChange({
      ...parametros,
      factorMarca: Math.max(0.1, Math.min(3.0, value)),
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
            <NumericInput
              value={parametros.margenBase * 100}
              onChange={(v) => handleMargenChange(v / 100)}
              min={0}
              max={100}
              step={0.01}
              label="Margen Base (%)"
              suffix="%"
              borderColor="#dc2626"
              buttonColor="#dc2626"
            />

            {/* Factor Esfuerzo */}
            <NumericInput
              value={parametros.factorEsfuerzo}
              onChange={handleFactorEsfuerzoChange}
              min={0.1}
              max={3.0}
              step={0.01}
              label="Factor Esfuerzo (Reemplazo Directo)"
              suffix=""
              borderColor="#ea580c"
              buttonColor="#ea580c"
            />

            {/* Factor Marca */}
            <NumericInput
              value={parametros.factorMarca}
              onChange={handleFactorMarcaChange}
              min={0.1}
              max={3.0}
              step={0.01}
              label="Factor Marca (Reemplazo Directo)"
              suffix=""
              borderColor="#ca8a04"
              buttonColor="#ca8a04"
            />

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
