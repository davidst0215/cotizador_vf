# 🔍 Guía de Debugging - Factor Esfuerzo v2.0

## Problema
El Factor Esfuerzo muestra 6/10 (Medio) en la pestaña "Costos Finales" aunque se hayan seleccionado OPs con diferentes valores de esfuerzo.

## Solución Implementada
Se agregaron console.log detallados en el frontend y enhanced logging en el backend para rastrear:

1. **Qué OPs se seleccionan** (valores de esfuerzo en cada una)
2. **Cómo se calcula el promedio** de esfuerzo
3. **Qué se envía al backend** en el payload de cotización
4. **Qué recibe y usa el backend** como valor de esfuerzo

---

## 📋 Pasos para Debuggear

### Paso 1: Abre las herramientas de desarrollo del navegador
- Presiona **F12** en Chrome/Edge
- Ve a la pestaña **Console** (Consola)

### Paso 2: Selecciona OPs y busca estos logs en la consola

#### Log 1️⃣: Cuando haces clic en "Setear OPs Seleccionadas"
```
📊 OPs Seleccionadas (X):
  {cod: "30082", esfuerzo: 8, prendas: 500, cliente: "..."}
  {cod: "30083", esfuerzo: 6, prendas: 300, cliente: "..."}
```
**Qué significa:**
- Debe mostrar el número de OPs que seleccionaste
- Cada OP debe mostrar su `esfuerzo` value

**Si no ves esto:**
- Los OPs no se están guardando correctamente en `selectedOpsData`

---

#### Log 2️⃣: Cuando haces clic en "Procesar Cotización" (ANTES de enviar al backend)
```
🔍 DEBUG: selectedOpsData length: 2
✅ Esfuerzo Promedio: 7 (2 OPs seleccionadas)
📝 Detalles OPs:
  {cod: "30082", esfuerzo: 8, prendas: 500, cliente: "..."}
  {cod: "30083", esfuerzo: 6, prendas: 300, cliente: "..."}

🚀 Enviando Cotización: {
  ...,
  esfuerzo_total: 7,
  cod_ordpros_count: 2
}
```
**Qué significa:**
- `esfuerzo_total: 7` debe ser el PROMEDIO de los esfuerzo de las OPs
- Fórmula: (8 + 6) / 2 = 7

**Si ves `esfuerzo_total: null` o no ves el log:**
- No hay OPs seleccionadas o `selectedOpsCode` está vacío

---

### Paso 3: Revisa los logs del backend

#### Log en el servidor (terminal donde corre el backend)
```
[ESFUERZO v2.0] input_data.esfuerzo_total: 7
[ESFUERZO v2.0] costos_hist.esfuerzo_promedio: 6
[ESFUERZO v2.0] ✅ Usando esfuerzo de OPs seleccionadas: 7
```

**Qué significa:**
- ✅ = El backend RECIBIÓ el esfuerzo_total del frontend
- ⚠️ = El backend NO lo recibió y usó el valor histórico (default: 6)

---

## 🎯 Árbol de Decisión para Debugging

```
¿Ves el Log 1️⃣ (📊 OPs Seleccionadas)?
├─ NO → Problema en OpsSelectionTable.handleOpsSelected
│       (No está llamando a onOpsSelected correctamente)
│
└─ SÍ → ¿Ves el Log 2️⃣ (✅ Esfuerzo Promedio)?
    ├─ NO → Problema: selectedOpsData se perdió entre clics
    │       (Verificar dependencias del useCallback)
    │
    └─ SÍ → ¿El esforzoPromedio es correcto?
        ├─ NO → Los valores de esfuerzo en OPs son incorrectos
        │       (Verificar backend/database.py línea 1371)
        │
        └─ SÍ → ¿Ves en backend "[ESFUERZO v2.0] ✅"?
            ├─ NO → El payload no incluye esfuerzo_total
            │       (Verificar línea 1300 del frontend)
            │
            └─ SÍ → El esfuerzo DEBE ser correcto en Costos Finales
                    Si sigue mostrando 6/10, es un problema en
                    cómo se muestra en la respuesta
```

---

## 🔧 Cambios Realizados

### Frontend (SistemaCotizadorTDV.tsx)
✅ **Línea 843-858:** Agregó debug log en `handleOpsSelected`
✅ **Línea 1273-1287:** Agregó debug logs detallados en procesarCotizacion
✅ **Línea 1308:** Agregó `selectedOpsData` a las dependencias del useCallback
✅ **Línea 1307-1311:** Muestra el payload completo siendo enviado

### Backend (utils.py)
✅ **Línea 709-718:** Enhanced logging para ver qué esfuerzo se recibe y se usa (v2.0 - recurrente)
✅ **Línea 886-893:** Enhanced logging para nuevos estilos

---

## 📊 Ejemplo de Ejecución Correcta

### Frontend Console:
```
📊 OPs Seleccionadas (1):
Array [
  {cod: "30082", esfuerzo: 8, prendas: 500, cliente: "..."}
]

🔍 DEBUG: selectedOpsData length: 1
✅ Esfuerzo Promedio: 8 (1 OPs seleccionadas)
📝 Detalles OPs:
Array [
  {cod: "30082", esfuerzo: 8, prendas: 500, cliente: "..."}
]

🚀 Enviando Cotización: {
  estilo_cliente: "XF7256",
  cliente_marca: "...",
  ...
  esfuerzo_total: 8,
  cod_ordpros_count: 1
}
```

### Backend Logs:
```
[ESFUERZO v2.0] input_data.esfuerzo_total: 8
[ESFUERZO v2.0] costos_hist.esfuerzo_promedio: 6
[ESFUERZO v2.0] ✅ Usando esfuerzo de OPs seleccionadas: 8
```

### Resultado esperado:
Factor Esfuerzo debería mostrar **8/10 (Alto)** con `factor_esfuerzo = 1.15`

---

## 🚨 Casos Comunes de Error

### Caso 1: Log 1️⃣ muestra esfuerzo: null o undefined
**Problema:** OpsSelectionTable no devuelve esfuerzo_total
**Solución:** Verificar database.py línea 1371 - el SELECT debe incluir esfuerzo_total

### Caso 2: Log 2️⃣ muestra "No hay OPs seleccionadas"
**Problema:** selectedOpsData está vacío cuando se procesa cotización
**Solución:** Ver si handleOpsSelected fue llamado antes de procesar

### Caso 3: Backend muestra "⚠️ Usando esfuerzo histórico"
**Problema:** El payload NO incluye esfuerzo_total
**Solución:** Verificar línea 1300 del frontend - condición `selectedOpsCode && selectedOpsCode.length > 0`

---

## ✅ Checklist Final

- [ ] Ves 📊 Log en consola al seleccionar OPs
- [ ] Ves ✅ Esfuerzo Promedio en consola al procesar
- [ ] El payload incluye esfuerzo_total correcto (Line 1307-1311)
- [ ] Backend muestra [ESFUERZO v2.0] ✅ Usando esfuerzo de OPs
- [ ] Costos Finales muestra el Factor Esfuerzo correcto

**Si cualquier item falla, sigue el árbol de decisión más arriba.**
