# 🚀 Setup SMP-DEV Local (Conectado a PostgreSQL)

## Información de Conexión

```
Host: 18.118.59.50
Puerto: 5432
Usuario: david
Base de Datos: tdv
SSL: Habilitado (verify-ca)
```

## ✅ Paso 1: Instalar Dependencias

### Opción A: Usando UV (recomendado)

```powershell
cd C:\Users\siste\smp-dev\backend

# Instalar proyecto con todas las dependencias
uv sync
```

### Opción B: Usando pip

```powershell
cd C:\Users\siste\smp-dev\backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
venv\Scripts\activate

# Instalar dependencias
pip install -e .
```

## ✅ Paso 2: Probar Conexión a PostgreSQL

```powershell
cd C:\Users\siste\smp-dev\backend

# Ejecutar script de prueba
python test_connection.py
```

**Resultado esperado:**
```
🔍 Intentando conectar a PostgreSQL...
   Host: 18.118.59.50
   Puerto: 5432
   Usuario: david
   Base de datos: tdv
   ✓ Certificado cliente: ...
   ✓ Clave privada: ...
   ✓ Certificado CA: ...

✅ CONEXIÓN EXITOSA!
   PostgreSQL versión: PostgreSQL 14.x ...

📊 Tablas disponibles (X):
   - costo_op_detalle
   - historial_estilos
   - ...
```

## ✅ Paso 3: Levantar el Servidor Local

### Con UV:

```powershell
cd C:\Users\siste\smp-dev\backend

# Ejecutar con uvicorn
uv run uvicorn src.smp.main:app --host 0.0.0.0 --port 8000 --reload
```

### Con pip:

```powershell
cd C:\Users\siste\smp-dev\backend

# Asegúrate que venv está activado
venv\Scripts\activate

# Ejecutar con uvicorn
uvicorn src.smp.main:app --host 0.0.0.0 --port 8000 --reload
```

**Resultado esperado:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

## ✅ Paso 4: Verificar que Funciona

1. **API Docs:**
   - http://localhost:8000/docs

2. **Health Check:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Cotización de prueba:**
   ```bash
   curl -X POST http://localhost:8000/cotizar \
     -H "Content-Type: application/json" \
     -d '{
       "cliente_marca": "LACOSTE",
       "temporada": "Primavera 2025",
       "categoria_lote": "Lote Mediano",
       "familia_producto": "Polos",
       "tipo_prenda": "Polo Hombre",
       "codigo_estilo": "EST-2024-001",
       "usuario": "david-dev",
       "version_calculo": "FLUIDO"
     }'
   ```

## 📝 Estructura del Proyecto

```
smp-dev/
├── backend/
│   ├── .env              ← Configuración PostgreSQL
│   ├── test_connection.py ← Script de prueba
│   ├── src/smp/
│   │   ├── main.py       ← API principal
│   │   ├── config.py     ← Configuración (ACTUALIZADO)
│   │   ├── database.py   ← Conexión a BD
│   │   ├── utils.py      ← Lógica de cotización
│   │   └── models.py     ← Modelos Pydantic
│   ├── pyproject.toml    ← Dependencias
│   └── uv.lock           ← Lock file (si usas uv)
│
└── frontend/
    └── (Next.js app)
```

## 🔧 Comandos Útiles

### Ver logs en tiempo real
```powershell
# En otra terminal (con server corriendo)
cd C:\Users\siste\smp-dev\backend
uv run uvicorn src.smp.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

### Ejecutar tests
```powershell
cd C:\Users\siste\smp-dev\backend
uv run pytest
```

### Formato de código
```powershell
cd C:\Users\siste\smp-dev\backend
# Con black (si está instalado)
uv run black src/ tests/
```

## ⚠️ Problemas Comunes

### "SSL certificate verification failed"

**Solución:** Verifica que los certificados existan en las rutas especificadas en `.env`:
```powershell
# Verificar archivos
Test-Path "C:\Users\siste\OneDrive\SAVA INVESTMENTS\calidad de venta\audios\piloto_abril\root.crt"
Test-Path "C:\Users\siste\OneDrive\SAVA INVESTMENTS\calidad de venta\audios\piloto_abril\david (1).crt"
Test-Path "C:\Users\siste\OneDrive\SAVA INVESTMENTS\calidad de venta\audios\piloto_abril\david.pk8"
```

### "Connection refused"

**Solución:** Verifica que PostgreSQL está accesible:
```powershell
# Prueba conexión
python test_connection.py
```

### "Module not found: smp"

**Solución:** Asegúrate de instalar el proyecto en modo desarrollo:
```powershell
cd C:\Users\siste\smp-dev\backend
pip install -e .
```

## 📊 Flujo de Desarrollo Recomendado

```
1. Haces cambios en el código
   ↓
2. El servidor se recarga automáticamente (--reload)
   ↓
3. Pruebas en http://localhost:8000/docs
   ↓
4. Ves errores en la terminal
   ↓
5. Corriges y repite
   ↓
6. Cuando esté listo, haces git commit
   ↓
7. Pusheas a GitHub (davidst0215/smp-dev)
```

## 🎯 Próximos Pasos

1. **Levantar el servidor local** (Paso 3)
2. **Experimentar con los endpoints** (Paso 4)
3. **Modificar lógica** sin miedo (el servidor se recarga automáticamente)
4. **Visualizar errores** en la terminal
5. **Commitear cambios** cuando esté estable

---

¿Necesitas ayuda? Ejecuta en este orden:

```powershell
# 1. Instalar
cd C:\Users\siste\smp-dev\backend
pip install -e .

# 2. Probar conexión
python test_connection.py

# 3. Levantar servidor
uvicorn src.smp.main:app --host 0.0.0.0 --port 8000 --reload
```
