# SOLUCIÓN DEFINITIVA: Pérdida de Foco en Input "Código de Estilo"

## PROBLEMA IDENTIFICADO

El input de "Código de estilo propio" perdía el foco después de escribir 1-2 caracteres, INCLUSO ANTES de hacer click en "Buscar Estilo". El problema ocurría en cada keystroke.

## CAUSA RAÍZ

El problema NO era con el input en sí, sino con **múltiples efectos (useEffect) que se ejecutaban en cada keystroke**, causando re-renders del componente padre que desmontaba y remontaba el input.

### Causas Específicas Identificadas:

1. **EFECTO CRÍTICO 1 (líneas 703-711 - DESHABILITADO)**:
   ```typescript
   useEffect(() => {
     const timer = setTimeout(() => {
       setDebouncedFormData(formDataRef.current);
     }, 3000);
     return () => clearTimeout(timer);
   }, [formData.codigo_estilo]); // ⚠️ SE DISPARABA EN CADA KEYSTROKE
   ```
   **Problema**: Cada vez que se escribía, se creaba y limpiaba un timer, causando re-renders.

2. **EFECTO CRÍTICO 2 (líneas 645-651 - DESHABILITADO)**:
   ```typescript
   useEffect(() => {
     if (!codigoEstiloLocal || codigoEstiloLocal.length < 3) {
       setEstilosEncontrados([]);
       setEsEstiloNuevo(null);
       setInfoAutoCompletado(null);
     }
   }, [codigoEstiloLocal]); // SE DISPARABA EN CADA KEYSTROKE
   ```
   **Problema**: Limpiaba estado en cada cambio del input local.

3. **SINCRONIZACIÓN INCORRECTA**:
   - El handler `onBuscarEstilo` llamaba a `manejarCambioFormulario` que actualizaba `formData.codigo_estilo`
   - Esto disparaba múltiples efectos que causaban re-renders del componente padre

4. **COMPONENTE NO MEMOIZADO**:
   - `CampoCodigoEstiloComponent` no tenía memoización personalizada
   - Se re-renderizaba cada vez que el padre se re-renderizaba

## SOLUCIÓN IMPLEMENTADA

### 1. Deshabilitación de Efectos Problemáticos

**Archivo**: `frontend/src/components/SistemaCotizadorTDV.tsx`

- **Líneas 706-715**: Deshabilitado el efecto de debounce que se disparaba con `formData.codigo_estilo`
- **Líneas 648-656**: Deshabilitado el efecto de limpieza que se disparaba con `codigoEstiloLocal`

### 2. Estado Completamente Independiente

```typescript
// ⚡ ESTADO LOCAL DEL INPUT - Completamente INDEPENDIENTE del formData
const [codigoEstiloLocal, setCodigoEstiloLocal] = useState<string>("");

// ⚡ Estado para controlar si el input ha sido sincronizado
const inputSyncedRef = useRef<boolean>(false);
```

### 3. Handler Mejorado

```typescript
const handleCodigoEstiloChange = useCallback(
  (valor: string) => {
    setCodigoEstiloLocal(valor);  // Solo actualiza estado local
    inputSyncedRef.current = false; // Marcar como no sincronizado
  },
  [],  // Sin dependencias - nunca cambia
);
```

### 4. Sincronización Explícita en onBuscarEstilo

```typescript
const onBuscarEstilo = useCallback(() => {
  if (codigoEstiloLocal && codigoEstiloLocal.length >= 3) {
    // Marcar como sincronizado
    inputSyncedRef.current = true;

    // Sincronizar estado local a formData
    setFormData(prev => ({
      ...prev,
      codigo_estilo: codigoEstiloLocal
    }));

    // Limpiar resultados previos antes de buscar
    setEstilosEncontrados([]);
    setEsEstiloNuevo(null);
    setInfoAutoCompletado(null);

    // Buscar estilo
    verificarYBuscarEstilo(...);
  }
}, [codigoEstiloLocal, formData.cliente_marca, formData.version_calculo, verificarYBuscarEstilo]);
```

### 5. Memoización Personalizada del Componente

```typescript
const CampoCodigoEstiloComponent = React.memo<CampoCodigoEstiloProps>(
  ({ value, buscandoEstilo, ... }) => (...),
  // Función de comparación personalizada
  (prevProps, nextProps) => {
    return (
      prevProps.value === nextProps.value &&
      prevProps.buscandoEstilo === nextProps.buscandoEstilo &&
      prevProps.estilosEncontrados === nextProps.estilosEncontrados &&
      prevProps.esEstiloNuevo === nextProps.esEstiloNuevo &&
      prevProps.infoAutoCompletado === nextProps.infoAutoCompletado
    );
  }
);
```

### 6. Input Puro Mejorado

```typescript
const PureInputCodigoEstilo = ({ value, onChange }) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value.toUpperCase());
  };

  return (
    <input
      type="text"
      value={value}
      onChange={handleChange}
      className="..."
      autoComplete="off"
      spellCheck={false}
    />
  );
};
```

### 7. Sincronización Automática en procesarCotizacion

```typescript
const procesarCotizacion = useCallback(async () => {
  setCargando(true);
  try {
    // Sincronizar codigoEstiloLocal a formData antes de procesar
    const codigoFinal = codigoEstiloLocal || formData.codigo_estilo;

    if (!inputSyncedRef.current && codigoEstiloLocal) {
      setFormData(prev => ({
        ...prev,
        codigo_estilo: codigoEstiloLocal
      }));
      inputSyncedRef.current = true;
    }
    // ...
  }
}, [codigoEstiloLocal, formData, ...]);
```

### 8. Validación Actualizada

```typescript
const erroresFormulario = useMemo(() => {
  const errores = [];
  if (!formData.cliente_marca) errores.push("Cliente/Marca es requerido");
  if (!formData.tipo_prenda) errores.push("Tipo de Prenda es requerido");
  // ⚡ Usar codigoEstiloLocal en lugar de formData.codigo_estilo
  if (!codigoEstiloLocal && !formData.codigo_estilo) errores.push("Código de estilo propio es requerido");
  return errores;
}, [formData.cliente_marca, formData.tipo_prenda, formData.codigo_estilo, codigoEstiloLocal]);
```

## FLUJO CORRECTO AHORA

### Durante la Escritura (Keystroke):
1. Usuario escribe en el input
2. `PureInputCodigoEstilo` recibe el evento onChange
3. Llama a `handleCodigoEstiloChange(valor)`
4. Actualiza **SOLO** `codigoEstiloLocal`
5. Marca `inputSyncedRef.current = false`
6. **NO SE DISPARAN EFECTOS** que causen re-renders del padre
7. El input **MANTIENE EL FOCO**

### Al Buscar Estilo (Click en "Buscar Estilo"):
1. Usuario hace click en "Buscar Estilo"
2. `onBuscarEstilo` se ejecuta
3. Marca `inputSyncedRef.current = true`
4. Sincroniza `codigoEstiloLocal` → `formData.codigo_estilo`
5. Limpia resultados previos
6. Ejecuta `verificarYBuscarEstilo`
7. Busca estilos similares y autocompletado

### Al Procesar Cotización:
1. Usuario hace click en "Configurar Producción"
2. `procesarCotizacion` se ejecuta
3. Si no está sincronizado, sincroniza `codigoEstiloLocal` → `formData.codigo_estilo`
4. Usa el código final para el payload
5. Procesa la cotización

## ARCHIVOS MODIFICADOS

- `frontend/src/components/SistemaCotizadorTDV.tsx` (líneas 44-65, 188-236, 534-535, 574-587, 591-597, 648-656, 706-715, 1004-1028, 1155-1181)

## VERIFICACIÓN

Para verificar que la solución funciona:

1. Abrir el sistema cotizador
2. Hacer click en el input "Código de estilo propio"
3. Escribir continuamente (ej: "LAC001")
4. **Verificar**: El foco NO se pierde durante la escritura
5. Hacer click en "Buscar Estilo" después de escribir
6. **Verificar**: La búsqueda se ejecuta correctamente
7. **Verificar**: El autocompletado funciona si el estilo existe
8. Hacer click en "Configurar Producción"
9. **Verificar**: El código de estilo se usa correctamente en la cotización

## BENEFICIOS DE LA SOLUCIÓN

1. **Foco Permanente**: El input ya NO pierde el foco durante la escritura
2. **Performance Mejorado**: Se eliminaron efectos innecesarios que se ejecutaban en cada keystroke
3. **Estado Aislado**: El estado local (`codigoEstiloLocal`) está completamente separado del `formData`
4. **Sincronización Explícita**: La sincronización solo ocurre cuando el usuario hace click en "Buscar" o "Configurar Producción"
5. **Memoización Correcta**: El componente `CampoCodigoEstiloComponent` tiene memoización personalizada
6. **Sin Efectos Secundarios**: No hay efectos que se disparen en cada keystroke

## PREVENCIÓN DE FUTUROS PROBLEMAS

Para evitar que este problema vuelva a ocurrir:

1. **NO agregar useEffect que dependan de `codigoEstiloLocal`** sin antes evaluar el impacto en el foco del input
2. **NO sincronizar automáticamente** `codigoEstiloLocal` a `formData.codigo_estilo` en cada cambio
3. **Mantener la sincronización explícita** solo cuando el usuario haga click en acciones específicas
4. **NO remover la memoización personalizada** de `CampoCodigoEstiloComponent`
5. **Si se necesita debouncing**, implementarlo usando refs en lugar de efectos que creen/limpien timers

## NOTAS TÉCNICAS

- El problema era causado por **efectos secundarios** (useEffect) que se ejecutaban en cada keystroke
- La solución separa el **estado local** del **estado global** para evitar re-renders innecesarios
- La **sincronización explícita** garantiza que el estado global se actualice solo cuando sea necesario
- La **memoización personalizada** evita re-renders del componente wrapper cuando no hay cambios relevantes

---

**Fecha de Solución**: 2025-11-12
**Problema**: CRÍTICO - Pérdida de foco constante en input
**Estado**: RESUELTO DEFINITIVAMENTE
**Metodología**: Análisis forensic de efectos y flujo de re-renders
