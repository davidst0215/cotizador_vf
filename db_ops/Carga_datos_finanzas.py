import pandas as pd
import pyodbc

from typing import Callable
from dataclasses import dataclass
from datetime import datetime
import os
import getpass


@dataclass(frozen=True)
class ColSpec:
    transform: Callable
    default: object


def _apply_specs(df: pd.DataFrame, specs: dict) -> pd.DataFrame:
    cols = specs.keys()
    df = df.reindex(columns=cols)
    n = len(df)
    for k, spec in specs.items():
        s = df[k] if k in df else pd.Series([spec.default] * n)
        df[k] = spec.transform(s.fillna(spec.default))
    return df


def _append_constants(df: pd.DataFrame, consts: dict) -> pd.DataFrame:
    n = len(df)
    for name, val in consts.items():
        df[name] = [val] * n
    return df


class CargadorOptimizado:
    def __init__(self):
        """Configuración inicial"""
        self.server = "131.107.20.77"
        self.port = 1433
        self.username = "CHSAYA01"
        self.password = "NewServerAz654@!"
        self.lote_carga = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.usuario_carga = getpass.getuser()

    def conectar_bd(self):
        """Conecta a SQL Server con configuración optimizada"""
        try:
            conn_str = f"DRIVER={{SQL Server}};SERVER={self.server},{self.port};UID={self.username};PWD={self.password};TrustServerCertificate=yes"
            conn: pyodbc.Connection = pyodbc.connect(conn_str)  # type: ignore[annotation-unchecked]
            conn.autocommit = True  # AUTOCOMMIT para velocidad
            cursor: pyodbc.Cursor = conn.cursor()  # type: ignore[annotation-unchecked]
            cursor.execute("USE [TDV]")

            print("✅ Conectado con AUTOCOMMIT (modo rápido)")
            return conn, cursor

        except Exception as e:
            print(f"❌ Error conectando: {e}")
            raise

    def opcion_1_truncate_rapido(self, cursor, tabla):
        """OPCIÓN 1: TRUNCATE (MÁS RÁPIDO) - Solo para carga inicial"""
        print(f"🚀 TRUNCATE {tabla} (súper rápido)...")
        try:
            cursor.execute(f"TRUNCATE TABLE TDV.saya.{tabla}")
            print(f"✅ {tabla} truncada instantáneamente")
            return True
        except Exception as e:
            print(f"⚠️ TRUNCATE falló: {e}")
            print("   Intentando DELETE...")
            cursor.execute(f"DELETE FROM TDV.saya.{tabla}")
            print(f"✅ {tabla} limpiada con DELETE")
            return True

    def opcion_2_carga_masiva_fast_executemany(self, cursor, sql, datos, tabla):
        """OPCIÓN 2: fast_executemany para inserción masiva"""
        print(f"🚀 Carga MASIVA con fast_executemany en {tabla}...")

        # FORZAR fast_executemany
        cursor.fast_executemany = True
        inicio = datetime.now()

        try:
            # Insertar en lotes más pequeños para fast_executemany
            lote_size = 500
            total_insertados = 0

            for i in range(0, len(datos), lote_size):
                lote = datos[i : i + lote_size]
                cursor.executemany(sql, lote)
                total_insertados += len(lote)
                if i % 2000 == 0:  # Progress cada 2000
                    print(f"   📈 {total_insertados}/{len(datos)}")

            tiempo = (datetime.now() - inicio).total_seconds()
            velocidad = len(datos) / tiempo if tiempo > 0 else 0
            print(f"✅ {len(datos)} registros en {tiempo:.1f}s ({velocidad:.0f} reg/s)")
            return len(datos)
        except Exception as e:
            print(f"❌ Error carga masiva: {e}")
            raise

    def opcion_3_carga_lotes(self, cursor, sql, datos, tabla, lote_size=1000):
        """OPCIÓN 3: Carga por lotes (para evitar timeouts)"""
        print(f"🚀 Carga por LOTES de {lote_size} en {tabla}...")

        cursor.fast_executemany = True
        total_insertados = 0
        total_lotes = len(datos) // lote_size + (1 if len(datos) % lote_size else 0)

        inicio = datetime.now()

        for i in range(0, len(datos), lote_size):
            lote = datos[i : i + lote_size]
            cursor.executemany(sql, lote)
            total_insertados += len(lote)

            lote_num = (i // lote_size) + 1
            print(f"   📦 Lote {lote_num}/{total_lotes}: +{len(lote)} registros")

        tiempo = (datetime.now() - inicio).total_seconds()
        print(
            f"✅ {total_insertados} registros en {tiempo:.1f}s ({total_insertados / tiempo:.0f} reg/s)"
        )
        return total_insertados

    def preparar_datos_costos_fijos(self, df: pd.DataFrame):
        specs = {
            "TIPO_COSTO": ColSpec(lambda s: s.astype(str).str.strip(), ""),
            "PROCESO_PRODUCTIVO": ColSpec(lambda s: s.astype(str).str.strip(), ""),
            "MES": ColSpec(lambda s: pd.to_numeric(s, errors="coerce").astype(int), 1),
            "AÑO": ColSpec(
                lambda s: pd.to_numeric(s, errors="coerce").astype(int),
                2024,
            ),
            "COSTO_TOTAL_USD": ColSpec(
                lambda s: pd.to_numeric(s, errors="coerce").astype(float),
                0.01,
            ),
        }
        df2 = _apply_specs(df, specs)
        consts = {
            "FECHA": datetime.now(),
            "LOTE": self.lote_carga,
            "USUARIO": self.usuario_carga,
        }
        return _append_constants(df2, consts)

    def preparar_datos_costos_mp(self, df: pd.DataFrame):
        """Prepara datos para costos_mp_ct_avios"""
        specs = {
            "MES": ColSpec(lambda s: pd.to_numeric(s, errors="coerce").astype(int), 1),
            "AÑO": ColSpec(
                lambda s: pd.to_numeric(s, errors="coerce").astype(int),
                2024,
            ),
            "MATERIA_PRIMA": ColSpec(
                lambda s: pd.to_numeric(s, errors="coerce").astype(float),
                0.01,
            ),
            "TELA_COMPRADA": ColSpec(
                lambda s: pd.to_numeric(s, errors="coerce").astype(float),
                0.01,
            ),
            "MATERIAL_DIRECTO": ColSpec(
                lambda s: pd.to_numeric(s, errors="coerce").astype(float),
                0.01,
            ),
        }
        df2 = _apply_specs(df, specs)
        consts = {
            "FECHA": datetime.now(),
            "LOTE": self.lote_carga,
            "USUARIO": self.usuario_carga,
        }
        return _append_constants(df2, consts)

    def cargar_costos_fijos(self, cursor, df, carga_inicial):
        """Carga costos_fijos_mensuales"""
        print("🚀 CARGA: costos_fijos_mensuales")

        if carga_inicial:
            self.opcion_1_truncate_rapido(cursor, "costos_fijos_mensuales")

        datos = self.preparar_datos_costos_fijos(df)
        if not datos:
            print("⚠️ No hay datos de costos fijos")
            return 0

        sql = """
        INSERT INTO TDV.saya.costos_fijos_mensuales
        (TIPO_COSTO, PROCESO_PRODUCTIVO, MES, AÑO, COSTO_TOTAL_USD,
         FECHA_CARGA, LOTE_CARGA, USUARIO_CARGA)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        return self.opcion_2_carga_masiva_fast_executemany(
            cursor, sql, datos, "costos_fijos_mensuales"
        )

    def cargar_costos_mp(self, cursor, df, carga_inicial):
        """Carga costos_mp_ct_avios"""
        print("🚀 CARGA: costos_mp_ct_avios")

        if carga_inicial:
            self.opcion_1_truncate_rapido(cursor, "costos_mp_ct_avios")

        datos = self.preparar_datos_costos_mp(df)
        if not datos:
            print("⚠️ No hay datos de costos MP")
            return 0

        sql = """
        INSERT INTO TDV.saya.costos_mp_ct_avios
        (MES, AÑO, MATERIA_PRIMA, TELA_COMPRADA, MATERIAL_DIRECTO,
         FECHA_CARGA, LOTE_CARGA, USUARIO_CARGA)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        return self.opcion_2_carga_masiva_fast_executemany(
            cursor, sql, datos, "costos_mp_ct_avios"
        )

    def preparar_datos_bd_finanzas(self, df):
        """Prepara datos para inserción masiva en bd_finanzas"""
        datos = []
        for _, row in df.iterrows():
            if (
                pd.isna(row.get("COD_ORDPRO"))
                or str(row.get("COD_ORDPRO")).strip() == ""
            ):
                continue

            # Validar MONTO_FACTURA para evitar el error de restricción CHECK
            monto = row.get("MONTO_FACTURA", 0)
            if pd.isna(monto) or monto <= 0:
                monto = 0.01  # Valor mínimo válido

            datos.append(
                (
                    str(row["COD_ORDPRO"]).strip(),
                    str(row.get("CLIENTE", "")).strip(),
                    str(row.get("TIPO_DE_PRODUCTO", "")).strip(),
                    str(row.get("FAMILIA_DE_PRODUCTOS", "")).strip(),
                    str(row.get("TEMPORADA", "")).strip(),
                    int(row.get("PRENDAS_REQUERIDAS", 0))
                    if not pd.isna(row.get("PRENDAS_REQUERIDAS"))
                    else 0,
                    row.get("FECHA_FACTURACION")
                    if not pd.isna(row.get("FECHA_FACTURACION"))
                    else None,
                    float(monto),
                    str(row.get("ESTILO_PROPIO", "")).strip(),
                    datetime.now(),
                    self.lote_carga,
                    self.usuario_carga,
                )
            )
        return datos

    def cargar_bd_finanzas_optimizado(self, cursor, df, carga_inicial, metodo="fast"):
        """Carga optimizada de bd_finanzas"""
        print("🚀 CARGA OPTIMIZADA: bd_finanzas")
        print("-" * 40)

        inicio_total = datetime.now()

        # 1. Limpiar si es carga inicial
        if carga_inicial:
            self.opcion_1_truncate_rapido(cursor, "bd_finanzas")

        # 2. Preparar datos
        print("📊 Preparando datos...")
        datos = self.preparar_datos_bd_finanzas(df)
        print(f"   📋 {len(datos)} registros válidos preparados")

        if not datos:
            print("⚠️ No hay datos para cargar")
            return 0

        # 3. SQL de inserción
        sql = """
        INSERT INTO TDV.saya.bd_finanzas
        (COD_ORDPRO, CLIENTE, TIPO_DE_PRODUCTO, FAMILIA_DE_PRODUCTOS,
         TEMPORADA, PRENDAS_REQUERIDAS, FECHA_FACTURACION, MONTO_FACTURA,
         ESTILO_PROPIO, FECHA_CARGA, LOTE_CARGA, USUARIO_CARGA)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        # 4. Elegir método de carga
        if metodo == "fast" and len(datos) > 100:
            insertados = self.opcion_2_carga_masiva_fast_executemany(
                cursor, sql, datos, "bd_finanzas"
            )
        elif metodo == "lotes":
            insertados = self.opcion_3_carga_lotes(
                cursor, sql, datos, "bd_finanzas", 1000
            )
        else:
            # Método tradicional para pocos registros
            insertados = 0
            for dato in datos:
                cursor.execute(sql, dato)
                insertados += 1

        tiempo_total = (datetime.now() - inicio_total).total_seconds()
        print(f"⚡ TOTAL bd_finanzas: {insertados} registros en {tiempo_total:.1f}s")

        return insertados

    def elegir_metodo_carga(self):
        """Permite al usuario elegir el método de optimización"""
        print("\n⚡ MÉTODOS DE OPTIMIZACIÓN DISPONIBLES:")
        print("=" * 50)
        print("1️⃣ ULTRA RÁPIDO: TRUNCATE + fast_executemany")
        print("   - Más rápido posible")
        print("   - Solo para carga inicial")
        print("   - Riesgo: si falla, pierdes todos los datos")
        print()
        print("2️⃣ RÁPIDO SEGURO: Carga por lotes")
        print("   - Muy rápido pero más seguro")
        print("   - Funciona para inicial e incremental")
        print("   - Recomendado para +1000 registros")
        print()
        print("3️⃣ NORMAL: Método tradicional")
        print("   - Más lento pero ultra seguro")
        print("   - Para pocos registros o conexiones inestables")
        print()

        opcion = input("¿Qué método prefieres? (1/2/3): ").strip()

        if opcion == "1":
            return "ultra_rapido"
        elif opcion == "2":
            return "lotes"
        else:
            return "normal"

    def cargar_archivo_optimizado(
        self, archivo_excel, carga_inicial=False, metodo="fast"
    ):
        """Función principal optimizada"""
        print("⚡ CARGADOR OPTIMIZADO - MODO VELOCIDAD")
        print("=" * 50)
        print(f"📁 Archivo: {archivo_excel}")
        print(f"⚙️ Tipo: {'INICIAL' if carga_inicial else 'INCREMENTAL'}")
        print(f"🚀 Método: {metodo.upper()}")
        print(f"🏷️ Lote: {self.lote_carga}")
        print("=" * 50)

        inicio_global = datetime.now()

        try:
            # 1. Validar archivo
            if not os.path.exists(archivo_excel):
                print("❌ Archivo no encontrado")
                return False

            # 2. Conectar (con autocommit para velocidad)
            conn, cursor = self.conectar_bd()
            cursor.fast_executemany = True  # ASEGURAR que esté activado

            # 3. Leer Excel
            print("📊 Leyendo Excel...")

            # Leer todas las hojas
            try:
                df_bd = pd.read_excel(archivo_excel, sheet_name="DATOS_OPS")
                print(f"   📋 DATOS_OPS: {len(df_bd)} registros")
            except ValueError:
                print("❌ No se encontró hoja DATOS_OPS")
                return False

            try:
                df_cf = pd.read_excel(
                    archivo_excel, sheet_name="COSTOS_FIJOS_MENSUALES"
                )
                print(f"   📋 COSTOS_FIJOS_MENSUALES: {len(df_cf)} registros")
            except ValueError:
                print("⚠️ No se encontró hoja COSTOS_FIJOS_MENSUALES")
                df_cf = None

            try:
                df_mp = pd.read_excel(archivo_excel, sheet_name="COSTOS_MP_CT_AVIOS")
                print(f"   📋 COSTOS_MP_CT_AVIOS: {len(df_mp)} registros")
            except ValueError:
                print("⚠️ No se encontró hoja COSTOS_MP_CT_AVIOS")
                df_mp = None

            # 4. Carga optimizada en orden: COSTOS PRIMERO, FINANZAS AL FINAL
            total_insertados = 0

            # PASO 1: Cargar COSTOS_FIJOS_MENSUALES
            if df_cf is not None and len(df_cf) > 0:
                insertados_cf = self.cargar_costos_fijos(cursor, df_cf, carga_inicial)
                total_insertados += insertados_cf
            else:
                print("⚠️ Saltando COSTOS_FIJOS_MENSUALES - no hay datos")

            # PASO 2: Cargar COSTOS_MP_CT_AVIOS
            if df_mp is not None and len(df_mp) > 0:
                insertados_mp = self.cargar_costos_mp(cursor, df_mp, carga_inicial)
                total_insertados += insertados_mp
            else:
                print("⚠️ Saltando COSTOS_MP_CT_AVIOS - no hay datos")

            # PASO 3: Cargar BD_FINANZAS (al final)
            insertados_bd = self.cargar_bd_finanzas_optimizado(
                cursor, df_bd, carga_inicial, metodo
            )
            total_insertados += insertados_bd

            # 5. Verificación final
            print("\n🔍 Verificación final...")

            try:
                cursor.execute("SELECT COUNT(*) FROM TDV.saya.costos_fijos_mensuales")
                total_cf = cursor.fetchone()[0]
                print(f"   📊 costos_fijos_mensuales: {total_cf}")
            except pyodbc.Error:
                total_cf = 0
                print("   ⚠️ costos_fijos_mensuales: no accesible")

            try:
                cursor.execute("SELECT COUNT(*) FROM TDV.saya.costos_mp_ct_avios")
                total_mp = cursor.fetchone()[0]
                print(f"   📊 costos_mp_ct_avios: {total_mp}")
            except pyodbc.Error:
                total_mp = 0
                print("   ⚠️ costos_mp_ct_avios: no accesible")

            cursor.execute("SELECT COUNT(*) FROM TDV.saya.bd_finanzas")
            total_bd = cursor.fetchone()[0]
            print(f"   📊 bd_finanzas: {total_bd}")

            cursor.execute(
                "SELECT COUNT(*) FROM TDV.saya.bd_finanzas WHERE LOTE_CARGA = ?",
                self.lote_carga,
            )
            lote_bd = cursor.fetchone()[0]
            print(f"{lote_bd=}")

            # 6. Reporte final
            tiempo_total = (datetime.now() - inicio_global).total_seconds()

            print("\n" + "⚡" * 50)
            print("🎉 CARGA OPTIMIZADA COMPLETADA")
            print("⚡" * 50)
            print(f"⏱️ Tiempo total: {tiempo_total:.1f} segundos")
            print(f"📊 Total insertados: {total_insertados}")
            print(f"📊 bd_finanzas: {total_bd}")
            print(f"📊 costos_fijos: {total_cf}")
            print(f"📊 costos_mp_ct: {total_mp}")
            if total_insertados > 0:
                print(
                    f"🚀 Velocidad promedio: {total_insertados / tiempo_total:.0f} registros/segundo"
                )
            print("✅ Estado: EXITOSO")

            conn.close()
            return True

        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False


def main():
    """Función principal con opciones de velocidad"""
    print("⚡ CARGADOR EXCEL OPTIMIZADO - TDV")
    print("🎯 ORDEN: 1°Costos Fijos → 2°Costos MP → 3°BD Finanzas")
    print()

    archivo_default = r"C:\Users\siste\OneDrive\SAYA INVESTMENTS\Textileria del valle\BD_FINANZAS.xlsx"

    # 1. Archivo
    archivo = input("📁 Excel (Enter=default): ").strip()
    if not archivo:
        archivo = archivo_default
        print(f"📁 Usando: {archivo}")

    # 2. Tipo de carga
    print("\n⚙️ TIPO DE CARGA:")
    tipo = input("¿Carga inicial? (s/n): ").strip().lower()
    carga_inicial = tipo in ["s", "si", "yes", "y"]

    # 3. Método de optimización
    cargador = CargadorOptimizado()
    metodo = cargador.elegir_metodo_carga()

    print("\n🚀 Configuración elegida:")
    print(f"   📁 Archivo: {os.path.basename(archivo)}")
    print(f"   ⚙️ Carga: {'INICIAL' if carga_inicial else 'INCREMENTAL'}")

    print(f"   ⚡ Método: {metodo.upper()}")

    continuar = input("\n¿Continuar? (s/n): ").strip().lower()
    if continuar not in ["s", "si", "yes", "y"]:
        print("❌ Cancelado")
        return

    # 4. Ejecutar carga optimizada
    exito = cargador.cargar_archivo_optimizado(archivo, carga_inicial, metodo)

    if exito:
        print("\n✅ PROCESO ULTRA RÁPIDO COMPLETADO")
        print("\n🔍 VERIFICAR:")
        print("SELECT COUNT(*) FROM TDV.saya.costos_fijos_mensuales;")
        print("SELECT COUNT(*) FROM TDV.saya.costos_mp_ct_avios;")
        print("SELECT COUNT(*) FROM TDV.saya.bd_finanzas;")
    else:
        print("\n❌ PROCESO FALLÓ")

    input("\nPresiona Enter para salir...")


if __name__ == "__main__":
    main()
