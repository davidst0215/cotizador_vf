# REFACTORIZACIÓN RÁPIDA v8 - EJECUTÁNDOSE

**Estado:** EN PROGRESO
**Opción:** B (Refactorización Rápida)
**Tiempo:** 12-15 horas
**Cambios a realizar:** 7 cambios críticos

---

## 📋 CAMBIOS A EJECUTAR

### 1️⃣ ELIMINAR ENDPOINT DUPLICADO
**Archivo:** `backend/src/smp/main.py`
**Líneas:** 1023-1151
**Acción:** Borrar completamente esta función

### 2️⃣ REMOVER CAMPOS INNECESARIOS (familia, temporada)
**Archivos:**
- `backend/src/smp/models.py` - Remover de CotizacionInput
- `backend/src/smp/main.py` - Remover validaciones
- `frontend/src/components/SistemaCotizadorTDV.tsx` - Remover inputs

### 3️⃣ CORREGIR VersionCalculo ENUM ✅ (YA HECHO)
**Archivo:** `backend/src/smp/models.py`
**Cambio:** FLUIDO = "FLUIDA"

### 4️⃣ REMOVER _debug DE RESPUESTAS
**Archivo:** `backend/src/smp/main.py`
**Ubicación:** Endpoint /desglose-wip-ops

### 5️⃣ REDUCIR LOGGING EXCESIVO
**Archivo:** `backend/src/smp/main.py`
**Patrón:** Remover logs informativos, mantener solo errores

### 6️⃣ CREAR ÍNDICES EN POSTGRESQL
**Comando SQL:** Ejecutar en BD tdv (schema silver)

### 7️⃣ IMPLEMENTAR CACHÉ REDIS
**Archivo:** `backend/src/smp/database.py`
**Cambio:** Agregar capa de caché antes de queries

---

## ✅ COMPLETADOS

- [x] VersionCalculo enum corregido (models.py)
- [x] Documentación de flujo corregido
- [x] Plan definido

## ⏳ PENDIENTES

- [ ] Eliminar endpoint duplicado
- [ ] Remover campos familia/temporada
- [ ] Limpiar _debug
- [ ] Reducir logs
- [ ] Crear índices BD
- [ ] Implementar caché
- [ ] Levantar v8 y validar

---

**Siguiente paso:** Comenzar eliminación de endpoint duplicado

