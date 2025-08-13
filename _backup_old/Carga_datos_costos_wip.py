import pandas as pd
import pyodbc
from datetime import datetime
import numpy as np

def conectar_sql_server():
    """Establece conexión con SQL Server"""
    server = os.environ.get('DB_SERVER', '131.107.20.77')
    port = 1433
    username = 'CHSAYA01'
    password = 'NewServerAz654@!'

    try:
        conn_str = f'DRIVER={{SQL Server}};SERVER={server},{port};UID={username};PWD={password};TrustServerCertificate=yes'
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("USE [TDV]")
        print("✅ Conectado a SQL Server - Base TDV")
        return conn, cursor
    except Exception as e:
        print(f"❌ Error conectando a SQL Server: {e}")
        raise

def leer_excel_costos(archivo_excel, hoja_nombre=None):
    """Lee el Excel y lo convierte a formato para base"""
    print(f"📖 Leyendo Excel: {archivo_excel}")
    
    try:
        # Leer Excel
        if hoja_nombre:
            df = pd.read_excel(archivo_excel, sheet_name=hoja_nombre)
        else:
            df = pd.read_excel(archivo_excel)
        
        print(f"✅ Excel leído: {len(df)} filas, {len(df.columns)} columnas")
        print(f"📊 Columnas encontradas: {list(df.columns[:10])}...")
        
        # Limpiar valores que pueden ser texto con comas o guiones
        print(f"🧹 Limpiando formato de números...")
        
        # Identificar columnas de períodos (las que no son ID)
        columnas_id = ['wip_id', 'wip name', 'Grupo', 'Subproceso']
        columnas_valores = [col for col in df.columns if col not in columnas_id]
        
        # Limpiar valores en columnas de períodos
        for col in columnas_valores:
            if col in df.columns:
                # Convertir a string, limpiar comas, guiones y espacios
                df[col] = df[col].astype(str)
                df[col] = df[col].str.replace(',', '')  # Quitar comas
                df[col] = df[col].str.replace('-', '0')  # Reemplazar guiones con 0
                df[col] = df[col].str.strip()  # Quitar espacios
                df[col] = df[col].replace(['', 'nan', 'None'], '0')  # Reemplazar vacíos
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)  # Convertir a número
        
        # Mostrar preview después de limpieza
        print(f"\n📋 PREVIEW (después de limpieza):")
        print(df.head(3).to_string())
        
        return df
        
    except Exception as e:
        print(f"❌ Error leyendo Excel: {e}")
        return None

def transformar_datos_excel(df):
    """Transforma el Excel de formato ancho a formato largo para base"""
    print(f"🔄 Transformando datos de formato ancho a largo...")
    
    # Columnas fijas de identificación (SIN 'textil') ✅ CORREGIDO
    columnas_id = ['wip_id', 'wip name', 'Grupo', 'Subproceso']
    
    # Todas las demás columnas son períodos (datetime objects)
    columnas_valores = [col for col in df.columns if col not in columnas_id]
    
    print(f"📝 Columnas ID: {columnas_id}")
    print(f"💰 Columnas valores (períodos): {len(columnas_valores)} meses")
    print(f"📅 Primer período: {columnas_valores[0] if columnas_valores else 'N/A'}")
    print(f"📅 Último período: {columnas_valores[-1] if columnas_valores else 'N/A'}")
    
    # Verificar que las columnas existen
    columnas_faltantes = [col for col in columnas_id if col not in df.columns]
    if columnas_faltantes:
        print(f"⚠️ Columnas faltantes: {columnas_faltantes}")
        print(f"📊 Columnas disponibles: {list(df.columns)}")
        return None
    
    # Transformar a formato largo
    df_largo = df.melt(
        id_vars=columnas_id,
        value_vars=columnas_valores,
        var_name='periodo',
        value_name='costo'
    )
    
    # Limpiar datos
    df_largo['costo'] = pd.to_numeric(df_largo['costo'], errors='coerce')
    df_largo['costo'] = df_largo['costo'].fillna(0)  # ✅ Reemplazar NaN con 0
    # ✅ MANTENER filas con costo 0 para mapeo completo
    # df_largo = df_largo[df_largo['costo'] != 0]   # ❌ ELIMINADO: No quitar zeros
    
    print(f"🔍 Registros antes de filtrar: {len(df_largo)}")
    print(f"📊 Registros con costo 0: {len(df_largo[df_largo['costo'] == 0])}")
    print(f"📊 Registros con costo > 0: {len(df_largo[df_largo['costo'] > 0])}")
    
    # Separar período en año y mes (DATETIME OBJECTS)
    print(f"📅 Separando períodos datetime en año y mes...")
    
    def separar_periodo_datetime(periodo_dt):
        """Convierte datetime object en año=2023, mes='ene'"""
        try:
            if pd.isna(periodo_dt):
                return None, None
            
            # Convertir datetime a año y mes
            año = periodo_dt.year
            
            # Mapear números de mes a nombres
            meses_nombres = {
                1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 
                5: 'may', 6: 'jun', 7: 'jul', 8: 'ago',
                9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'
            }
            
            mes = meses_nombres.get(periodo_dt.month, f'mes{periodo_dt.month}')
            
            return año, mes
        except Exception as e:
            print(f"⚠️ Error procesando período {periodo_dt}: {e}")
            return None, None
    
    df_largo[['año', 'mes']] = df_largo['periodo'].apply(
        lambda x: pd.Series(separar_periodo_datetime(x))
    )
    
    # Quitar la columna periodo original y registros con año/mes inválidos
    df_largo = df_largo.drop('periodo', axis=1)
    df_largo = df_largo.dropna(subset=['año', 'mes'])
    
    print(f"✅ Transformación completada: {len(df_largo)} registros (incluyendo costos 0)")
    print(f"📊 Años encontrados: {sorted(df_largo['año'].unique())}")
    print(f"📊 Meses encontrados: {list(df_largo['mes'].unique())}")
    print(f"📊 Distribución de costos:")
    print(f"   💰 Con costo > 0: {len(df_largo[df_largo['costo'] > 0]):,}")
    print(f"   🔴 Con costo = 0: {len(df_largo[df_largo['costo'] == 0]):,}")
    
    return df_largo

def crear_tabla_destino(conn, nombre_tabla='saya.costos_procesos'):
    """Crea la tabla destino si no existe"""
    print(f"🏗️ Verificando/creando tabla {nombre_tabla}...")
    
    cursor = conn.cursor()
    
    # SQL para crear tabla (FORZAR RECREACIÓN) ✅ CORREGIDO
    sql_crear_tabla = f"""
    -- Crear esquema si no existe
    IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'saya')
    BEGIN
        EXEC('CREATE SCHEMA saya')
    END
    
    -- ELIMINAR tabla si existe (FORZAR RECREACIÓN)
    IF EXISTS (SELECT * FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id 
               WHERE s.name = 'saya' AND t.name = 'costos_procesos')
    BEGIN
        DROP TABLE TDV.saya.costos_procesos
        PRINT '🗑️ Tabla anterior eliminada para recrear con estructura correcta'
    END
    
    -- Crear tabla con estructura corregida
    CREATE TABLE TDV.saya.costos_procesos (
        id_registro         BIGINT IDENTITY(1,1) PRIMARY KEY,
        wip_id             NVARCHAR(50) NULL,  -- ✅ NVARCHAR para manejar "19a"
        wip_name           NVARCHAR(200) NULL,
        grupo              NVARCHAR(100) NULL,
        subproceso         NVARCHAR(200) NULL,
        año                INT NULL,
        mes                NVARCHAR(20) NULL,
        costo              DECIMAL(18,4) NULL,
        
        -- Campos adicionales para futuro
        unidades           DECIMAL(18,2) NULL,
        costo_unitario     DECIMAL(18,4) NULL,
        
        -- Auditoría
        usuario_carga      NVARCHAR(100) DEFAULT SYSTEM_USER,
        estado_registro    NVARCHAR(20) DEFAULT 'ACTIVO'
    );
    
    -- Índices
    CREATE INDEX IX_costos_procesos_wip ON TDV.saya.costos_procesos (wip_id);
    CREATE INDEX IX_costos_procesos_grupo ON TDV.saya.costos_procesos (grupo);
    CREATE INDEX IX_costos_procesos_subproceso ON TDV.saya.costos_procesos (subproceso);
    CREATE INDEX IX_costos_procesos_año_mes ON TDV.saya.costos_procesos (año, mes);
    
    PRINT '✅ Tabla saya.costos_procesos creada con estructura corregida'
    """
    
    try:
        cursor.execute(sql_crear_tabla)
        conn.commit()
        print(f"✅ Tabla {nombre_tabla} recreada con wip_id como NVARCHAR")
        return True
    except Exception as e:
        print(f"❌ Error creando tabla: {e}")
        return False

def limpiar_tabla_antes_carga(conn, nombre_tabla='saya.costos_procesos'):
    """Limpia la tabla antes de cargar datos nuevos"""
    print(f"🧹 Limpiando tabla {nombre_tabla}...")
    
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"DELETE FROM TDV.{nombre_tabla}")
        conn.commit()
        print(f"✅ Tabla {nombre_tabla} limpiada")
        return True
    except Exception as e:
        print(f"❌ Error limpiando tabla: {e}")
        return False

def insertar_datos_excel(df_largo, conn, nombre_tabla='saya.costos_procesos'):
    """Inserta los datos del Excel en la base"""
    print(f"💾 Insertando {len(df_largo)} registros en {nombre_tabla}...")
    
    cursor = conn.cursor()
    registros_insertados = 0
    registros_error = 0
    
    try:
        for _, row in df_largo.iterrows():
            try:
                # Preparar valores (wip_id como string) ✅ CORREGIDO
                wip_id = str(row.get('wip_id', ''))[:50] if pd.notna(row.get('wip_id')) else None
                wip_name = str(row.get('wip name', ''))[:200] if pd.notna(row.get('wip name')) else None
                grupo = str(row.get('Grupo', ''))[:100] if pd.notna(row.get('Grupo')) else None
                subproceso = str(row.get('Subproceso', ''))[:200] if pd.notna(row.get('Subproceso')) else None
                año = int(row['año']) if pd.notna(row['año']) else None
                mes = str(row['mes'])[:20] if pd.notna(row['mes']) else None
                costo = float(row['costo']) if pd.notna(row['costo']) else 0
                
                # Insertar registro (SIN textil) ✅ CORREGIDO
                cursor.execute("""
                    INSERT INTO TDV.saya.costos_procesos 
                    (wip_id, wip_name, grupo, subproceso, año, mes, costo)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, wip_id, wip_name, grupo, subproceso, año, mes, costo)
                
                registros_insertados += 1
                
                # Mostrar progreso cada 100 registros
                if registros_insertados % 100 == 0:
                    print(f"   📊 Insertados: {registros_insertados}")
                
            except Exception as e:
                print(f"⚠️ Error en fila {registros_insertados + registros_error}: {e}")
                registros_error += 1
                if registros_error > 10:  # Límite de errores
                    print(f"❌ Demasiados errores, deteniendo inserción")
                    break
        
        # Confirmar transacción
        conn.commit()
        
        print(f"✅ Inserción completada:")
        print(f"   📝 Registros insertados: {registros_insertados:,}")
        print(f"   ❌ Registros con error: {registros_error:,}")
        
        return registros_insertados > 0
        
    except Exception as e:
        print(f"❌ Error general insertando: {e}")
        conn.rollback()
        return False

def verificar_carga(conn, nombre_tabla='saya.costos_procesos'):
    """Verifica que los datos se cargaron correctamente"""
    print(f"🔍 Verificando carga en {nombre_tabla}...")
    
    cursor = conn.cursor()
    
    try:
        # Contar registros totales
        cursor.execute(f"SELECT COUNT(*) FROM TDV.{nombre_tabla}")
        total_registros = cursor.fetchone()[0]
        
        # Contar registros por tipo de costo
        cursor.execute(f"SELECT COUNT(*) FROM TDV.{nombre_tabla} WHERE costo = 0")
        registros_cero = cursor.fetchone()[0]
        
        cursor.execute(f"SELECT COUNT(*) FROM TDV.{nombre_tabla} WHERE costo > 0")
        registros_con_costo = cursor.fetchone()[0]
        
        # Contar registros por wip_id
        cursor.execute(f"SELECT COUNT(DISTINCT wip_id) FROM TDV.{nombre_tabla}")
        wips_unicos = cursor.fetchone()[0]
        
        # Verificar años y meses
        cursor.execute(f"SELECT DISTINCT año FROM TDV.{nombre_tabla} ORDER BY año")
        años = [row[0] for row in cursor.fetchall()]
        
        cursor.execute(f"SELECT DISTINCT mes FROM TDV.{nombre_tabla} ORDER BY mes")
        meses = [row[0] for row in cursor.fetchall()]
        
        # Verificar algunos registros
        cursor.execute(f"SELECT TOP 5 wip_id, wip_name, grupo, año, mes, costo FROM TDV.{nombre_tabla} ORDER BY wip_id, año, mes")
        muestra = cursor.fetchall()
        
        print(f"✅ VERIFICACIÓN COMPLETADA:")
        print(f"   📊 Total registros: {total_registros:,}")
        print(f"   📅 Años: {años}")
        print(f"   📅 Meses: {meses}")
        print(f"\n📋 MUESTRA DE DATOS:")
        for row in muestra:
            print(f"   WIP {row[0]}: {row[1][:30]}... - {row[2]} - {row[3]}/{row[4]} = ${row[5]:,.2f}")
        
        return total_registros > 0
        
    except Exception as e:
        print(f"❌ Error verificando: {e}")
        return False

def procesar_excel_completo(archivo_excel, hoja_nombre=None, nombre_tabla='saya.costos_procesos'):
    """Función principal que ejecuta todo el proceso"""
    print("🚀 SUBIENDO EXCEL A BASE TDV")
    print(f"📄 Archivo: Costos por Subprocesos.xlsx")
    print(f"🗄️ Destino: TDV.{nombre_tabla}")
    print("=" * 70)
    
    try:
        # 1. Conectar a base
        conn, cursor = conectar_sql_server()
        
        # 2. Leer Excel
        df = leer_excel_costos(archivo_excel, hoja_nombre)
        if df is None:
            return False
        
        # 3. Transformar datos
        df_largo = transformar_datos_excel(df)
        if df_largo is None:
            return False
        
        # 4. Crear tabla destino (RECREARÁ la tabla con estructura correcta)
        tabla_ok = crear_tabla_destino(conn, nombre_tabla)
        if not tabla_ok:
            return False
        
        # 5. Insertar datos (ya no necesita limpiar porque tabla se recreó)
        exito = insertar_datos_excel(df_largo, conn, nombre_tabla)
        
        # 6. Verificar carga
        if exito:
            verificar_carga(conn, nombre_tabla)
        
        # 7. Cerrar conexión
        conn.close()
        
        if exito:
            print(f"\n🎉 PROCESO COMPLETADO EXITOSAMENTE")
            print(f"🗄️ Datos cargados en TDV.{nombre_tabla}")
            print(f"📊 Formato: año + mes separados")
            print(f"📅 Período: 2023-2024")
        else:
            print(f"\n❌ Proceso completado con errores")
        
        return exito
        
    except Exception as e:
        print(f"❌ Error en proceso completo: {e}")
        import traceback
        traceback.print_exc()
        return False

# EJECUCIÓN PRINCIPAL
if __name__ == "__main__":
    # CONFIGURACIÓN DINÁMICA MEJORADA
    print("📁 SELECCIONAR ARCHIVO EXCEL")
    print("=" * 50)
    
    # Opción 1: Buscar en directorio actual
    import os
    archivo_local = os.path.join(os.getcwd(), "Costos por Subprocesos.xlsx")
    
    if os.path.exists(archivo_local):
        print(f"✅ Archivo encontrado: {archivo_local}")
        ARCHIVO_EXCEL = archivo_local
    else:
        # Opción 2: Pedir ruta al usuario
        print("❌ Archivo no encontrado en directorio actual")
        print("📝 Ingresa la ruta completa del archivo:")
        ARCHIVO_EXCEL = input("Ruta: ").strip().replace('"', '')
        
        # VALIDACIÓN MEJORADA
        print(f"🔍 Validando ruta: {ARCHIVO_EXCEL}")
        
        if not ARCHIVO_EXCEL:
            print("❌ No se ingresó ninguna ruta")
            input("Presiona Enter para salir...")
            exit()
            
        if not os.path.exists(ARCHIVO_EXCEL):
            print(f"❌ Archivo no encontrado: {ARCHIVO_EXCEL}")
            print(f"📂 Directorio actual: {os.getcwd()}")
            input("Presiona Enter para salir...")
            exit()
        
        if not ARCHIVO_EXCEL.endswith('.xlsx'):
            print(f"⚠️ Advertencia: El archivo no tiene extensión .xlsx")
        
        print(f"✅ Archivo validado correctamente")
    
    HOJA_NOMBRE = None
    TABLA_DESTINO = "saya.costos_procesos"
    
    print("\n⚙️ CONFIGURACIÓN:")
    print(f"   📄 Excel: {os.path.basename(ARCHIVO_EXCEL)}")
    print(f"   📂 Ruta: {ARCHIVO_EXCEL}")
    print(f"   📊 Hoja: {HOJA_NOMBRE or 'Primera hoja'}")
    print(f"   🗄️ Tabla: TDV.{TABLA_DESTINO}")
    print(f"   📅 Estructura: año + mes separados (2023-2024)")
    print(f"   📅 Períodos: datetime objects → año + mes")
    print(f"   🧹 Limpieza: números y fechas")
    print()
    
    # Confirmación antes de procesar
    confirmar = input("¿Continuar con la carga? (s/n): ").strip().lower()
    if confirmar not in ['s', 'si', 'y', 'yes']:
        print("❌ Proceso cancelado")
        exit()
    
    # ✅ EJECUTAR PROCESO COMPLETO
    print("\n🚀 INICIANDO PROCESO...")
    print("=" * 50)
    
    exito = procesar_excel_completo(
        archivo_excel=ARCHIVO_EXCEL,
        hoja_nombre=HOJA_NOMBRE,
        nombre_tabla=TABLA_DESTINO
    )
    
    if exito:
        print(f"\n✅ EXCEL SUBIDO EXITOSAMENTE")
        print(f"\n🔍 CONSULTAS DE VERIFICACIÓN:")
        print(f"SELECT COUNT(*) FROM TDV.saya.costos_procesos;")
        print(f"SELECT TOP 10 * FROM TDV.saya.costos_procesos ORDER BY wip_id, año, mes;")
        print(f"SELECT año, COUNT(*) FROM TDV.saya.costos_procesos GROUP BY año;")
    else:
        print(f"\n❌ ERROR EN CARGA")
    
    # Pausa para ver resultados
    input("\nPresiona Enter para terminar...")