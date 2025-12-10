"use client"

import { useState } from "react"
import {
  Printer,
  Database,
  ArrowRight,
  ArrowDown,
  Server,
  FileSpreadsheet,
  Cloud,
  BarChart3,
  Monitor,
  ChevronDown,
  ChevronRight,
  Table2,
} from "lucide-react"
import { Button } from "@/components/ui/button"

const tablesByCategory = {
  excel: {
    title: "Bases de Finanzas - EXCEL",
    color: "bg-primary",
    borderColor: "border-primary",
    bgColor: "bg-primary/10",
    textColor: "text-primary",
    tables: [
      { id: "excel_materiales", name: "Costos de materiales" },
      { id: "excel_indirectos", name: "Costos indirectos" },
      { id: "excel_procesos", name: "Costos de procesos" },
      { id: "excel_produccion", name: "Producción por procesos" },
    ],
  },
  sige: {
    title: "Base en la Nube - SIGE",
    color: "bg-slate-700",
    borderColor: "border-slate-600",
    bgColor: "bg-slate-100",
    textColor: "text-slate-800",
    tables: [
      { id: "sige_cotizaciones", name: "Data de cotizaciones" },
      { id: "sige_estilos", name: "Data de estilos" },
      { id: "sige_ops", name: "Data de OPs" },
      { id: "sige_materiales", name: "Data de materiales" },
      { id: "sige_produccion", name: "Data de producción" },
      { id: "sige_facturacion", name: "Data de facturación" },
    ],
  },
  azure_base: {
    title: "Tablas Base - Azure TDV",
    color: "bg-primary/80",
    borderColor: "border-primary/60",
    bgColor: "bg-primary/5",
    textColor: "text-primary",
    tables: [
      { id: "base_costos_material", name: "Base de costos material" },
      { id: "base_costos_indirectos", name: "Base de costos indirectos" },
      { id: "base_costos_procesos", name: "Base de costos de procesos" },
      { id: "base_po_ruta", name: "Base de Po ruta y tiempos de procesos" },
      { id: "base_finanzas", name: "Base de finanzas" },
      { id: "base_wip_allocation", name: "Base Wip time allocation" },
      { id: "base_wip_facturation", name: "Base Wip time facturation" },
      { id: "base_historica_estilos", name: "Base histórica de estilos" },
    ],
  },
  azure_materiales: {
    title: "Tablas de Materiales - Azure TDV",
    color: "bg-amber-600",
    borderColor: "border-amber-500",
    bgColor: "bg-amber-50",
    textColor: "text-amber-800",
    tables: [
      { id: "base_costos_ordenes_compra", name: "Base de costos de órdenes de compra" },
      { id: "base_costos_requerimiento", name: "Base de costos de requerimiento de material" },
      { id: "base_costos_avios", name: "Base de costos de avíos / Materia prima" },
      { id: "base_costos_detalle", name: "Base costos detalle de avíos / Hilos / Tela comprada" },
    ],
  },
  azure_truncado: {
    title: "Tablas Modelo Truncado",
    color: "bg-rose-700",
    borderColor: "border-rose-600",
    bgColor: "bg-rose-50",
    textColor: "text-rose-800",
    tables: [
      { id: "costo_op_factura_truncado", name: "Costo Op Factura truncado" },
      { id: "costo_op_detalle_truncado", name: "Costo Op detalle truncado" },
    ],
  },
  azure_fluido: {
    title: "Tablas Modelo Fluido",
    color: "bg-emerald-700",
    borderColor: "border-emerald-600",
    bgColor: "bg-emerald-50",
    textColor: "text-emerald-800",
    tables: [
      { id: "costos_wip_op_fluido", name: "Costos Wip Op mes fluido" },
      { id: "costos_op_detalle_fluido", name: "Costos Op detalle fluido" },
      { id: "costos_op_factura_fluido", name: "Costos Op Factura fluido" },
    ],
  },
  destinos: {
    title: "Destinos Finales",
    color: "bg-slate-700",
    borderColor: "border-slate-600",
    bgColor: "bg-slate-50",
    textColor: "text-slate-800",
    tables: [
      { id: "superset", name: "Reportería en la Nube Superset" },
      { id: "cotizador", name: "Sistema Cotizador en la Nube Azure" },
    ],
  },
}

const spCategories = [
  {
    id: "input",
    title: "Creación de Tablas Input",
    description: "Procedimientos para ingestar y transformar datos base desde Excel y fuentes externas",
    color: "bg-primary",
    sps: [
      {
        number: 1,
        title: "Ingestar tablas de Excel de Finanzas a PostgreSQL",
        sp: "Ingesta manual / ETL",
        inputTables: ["excel_materiales", "excel_indirectos", "excel_procesos", "excel_produccion"],
        outputTables: ["base_costos_material", "base_costos_indirectos", "base_costos_procesos"],
      },
      {
        number: 2,
        title: "Formatear la tabla de costos indirectos",
        sp: "SP transform_costos",
        inputTables: ["base_costos_indirectos"],
        outputTables: ["base_costos_indirectos"],
      },
      {
        number: 3,
        title: "Formatear la tabla de costos de producción",
        sp: "SP transform_costos_proc",
        inputTables: ["base_costos_procesos"],
        outputTables: ["base_costos_procesos"],
      },
      {
        number: 4,
        title: "Reasignar costos por procesos",
        sp: "SP Cargar_costos_procesos",
        inputTables: ["base_costos_procesos"],
        outputTables: ["base_po_ruta"],
      },
      {
        number: 6,
        title: "Crear y popular la tabla WIP time allocation",
        sp: "SP create_wip_time_costos_allocation",
        inputTables: ["sige_produccion", "base_costos_procesos"],
        outputTables: ["base_wip_allocation"],
      },
      {
        number: 7,
        title: "Crear y popular la tabla WIP time facturation",
        sp: "SP calculate_costo_wip_facturacion_truncado",
        inputTables: ["base_wip_allocation", "sige_facturacion"],
        outputTables: ["base_wip_facturation"],
      },
      {
        number: 8,
        title: "Crear y popular la tabla de finanzas",
        sp: "SP create_bd_finanzas",
        inputTables: ["excel_indirectos", "sige_facturacion"],
        outputTables: ["base_finanzas"],
      },
    ],
  },
  {
    id: "materiales",
    title: "Creación de Tablas Intermedias de Materiales",
    description: "Procedimientos para calcular costos detallados de materiales (avíos, hilos, telas)",
    color: "bg-amber-600",
    sps: [
      {
        number: 9,
        title: "Crear y popular la tabla costo avíos",
        sp: "SP populate_costo_avios_v2",
        inputTables: ["sige_materiales"],
        outputTables: ["base_costos_avios"],
      },
      {
        number: 10,
        title: "Crear y popular la tabla costo materia prima",
        sp: "SP populate_costo_materia_prima_v4",
        inputTables: ["sige_materiales"],
        outputTables: ["base_costos_avios"],
      },
      {
        number: 11,
        title: "Crear y popular la tabla costo avíos detalle OP",
        sp: "SP populate_costo_avios_detalle_op",
        inputTables: ["base_costos_avios", "sige_ops"],
        outputTables: ["base_costos_detalle"],
      },
      {
        number: 12,
        title: "Crear y popular la tabla costo hilos detalle OP",
        sp: "SP populate_costo_hilado_detalle_op",
        inputTables: ["base_costos_avios", "sige_ops"],
        outputTables: ["base_costos_detalle"],
      },
      {
        number: 13,
        title: "Crear y popular la tabla costo tela detalle OP",
        sp: "SP populate_costo_telas_detalle_op",
        inputTables: ["base_costos_avios", "sige_ops"],
        outputTables: ["base_costos_detalle"],
      },
      {
        number: 14,
        title: "Crear y popular la tabla histórica de costos de requerimiento de materiales",
        sp: "SP populate_histórico_precios_materiales",
        inputTables: ["sige_materiales"],
        outputTables: ["base_costos_requerimiento"],
      },
      {
        number: 15,
        title: "Crear y popular la tabla histórica de costos de órdenes de compra",
        sp: "SP populate_histórico_compras_materiales",
        inputTables: ["sige_materiales"],
        outputTables: ["base_costos_ordenes_compra"],
      },
    ],
  },
  {
    id: "finales",
    title: "Creación de Tablas Finales",
    description: "Procedimientos para generar las tablas de costeo final (truncado y fluido)",
    color: "bg-emerald-700",
    sps: [
      {
        number: 16,
        title: "Crear y popular la tabla costo Op factura truncado",
        sp: "SP calculate_bd_margen_truncado",
        inputTables: ["base_costos_procesos", "base_costos_material", "base_finanzas"],
        outputTables: ["costo_op_factura_truncado"],
      },
      {
        number: 17,
        title: "Crear y popular la tabla costo Op detalle truncado",
        sp: "SP calculate_costo_op_resumen_truncado",
        inputTables: ["costo_op_factura_truncado"],
        outputTables: ["costo_op_detalle_truncado"],
      },
      {
        number: 18,
        title: "Crear y popular la tabla costo WIP Op fluido",
        sp: "SP populate_costo_hibrido_fluido",
        inputTables: ["base_wip_allocation", "base_costos_procesos", "base_finanzas"],
        outputTables: ["costos_wip_op_fluido"],
      },
      {
        number: 19,
        title: "Crear y popular la tabla costo Op detalle fluido",
        sp: "SP populate_costo_op_detalle_v2",
        inputTables: ["costos_wip_op_fluido"],
        outputTables: ["costos_op_detalle_fluido"],
      },
      {
        number: 20,
        title: "Crear y popular la tabla costo Op factura fluido",
        sp: "SP populate_costo_bd_margen",
        inputTables: ["costos_op_detalle_fluido"],
        outputTables: ["costos_op_factura_fluido"],
      },
      {
        number: 21,
        title: "Crear y popular la tabla histórica de estilos",
        sp: "SP create_historial_estilos",
        inputTables: ["sige_estilos", "costos_op_detalle_fluido"],
        outputTables: ["base_historica_estilos"],
      },
      {
        number: 22,
        title: "Crear y popular el esfuerzo y kg prenda a las tablas",
        sp: "SP populate_esfuerzo_op_detalle_v2",
        inputTables: ["sige_produccion", "costos_op_detalle_fluido"],
        outputTables: ["costos_op_detalle_fluido"],
      },
    ],
  },
]

const getTableInfo = (tableId: string) => {
  for (const [categoryKey, category] of Object.entries(tablesByCategory)) {
    const table = category.tables.find((t) => t.id === tableId)
    if (table) {
      return { ...table, category: categoryKey, categoryInfo: category }
    }
  }
  return null
}

export default function ManualSPs() {
  const [expandedSp, setExpandedSp] = useState<number | null>(null)

  const handlePrint = () => {
    window.print()
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-primary text-primary-foreground py-8 print:py-4">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold mb-2">Manual de Ejecución de Stored Procedures</h1>
              <p className="text-primary-foreground/80">
                Proceso de actualización de datos para el Sistema Cotizador TDV y Reportería en la Nube
              </p>
            </div>
            <Button onClick={handlePrint} variant="secondary" className="print:hidden flex items-center gap-2">
              <Printer className="h-4 w-4" />
              Imprimir PDF
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-primary mb-6 flex items-center gap-2">
            <Server className="h-6 w-6" />
            Arquitectura de Costeo y Reportería en la Nube
          </h2>

          <div className="bg-gradient-to-br from-slate-50 to-slate-100 rounded-2xl p-8 border border-slate-200 shadow-sm">
            {/* Sources Row */}
            <div className="flex justify-center gap-8 mb-8">
              {/* Excel Source */}
              <div className="w-64">
                <div className="bg-primary text-white px-4 py-3 rounded-t-xl font-semibold flex items-center gap-2">
                  <FileSpreadsheet className="h-5 w-5" />
                  Bases de Finanzas - EXCEL
                </div>
                <div className="bg-white border-2 border-primary border-t-0 rounded-b-xl p-4 shadow-sm">
                  <ul className="space-y-2">
                    {tablesByCategory.excel.tables.map((table) => (
                      <li key={table.id} className="flex items-center gap-2 text-sm text-slate-700">
                        <div className="w-2 h-2 rounded-full bg-primary" />
                        {table.name}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* SIGE Source */}
              <div className="w-64">
                <div className="bg-slate-700 text-white px-4 py-3 rounded-t-xl font-semibold flex items-center gap-2">
                  <Cloud className="h-5 w-5" />
                  Base en la Nube - SIGE
                </div>
                <div className="bg-white border-2 border-slate-600 border-t-0 rounded-b-xl p-4 shadow-sm">
                  <ul className="space-y-2">
                    {tablesByCategory.sige.tables.map((table) => (
                      <li key={table.id} className="flex items-center gap-2 text-sm text-slate-700">
                        <div className="w-2 h-2 rounded-full bg-slate-600" />
                        {table.name}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* Arrow Down */}
            <div className="flex justify-center mb-8">
              <div className="flex flex-col items-center">
                <div className="w-0.5 h-8 bg-slate-400" />
                <ArrowDown className="h-6 w-6 text-slate-400 -mt-1" />
              </div>
            </div>

            {/* Azure Server Box */}
            <div className="bg-white rounded-2xl border-2 border-primary/30 shadow-lg p-6 mb-8">
              <div className="text-center mb-6">
                <div className="inline-flex items-center gap-2 bg-primary text-white px-6 py-2 rounded-full font-semibold">
                  <Database className="h-5 w-5" />
                  Bases en la Nube - SERVIDOR AZURE TDV
                </div>
              </div>

              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Tablas Base */}
                <div className="bg-gradient-to-b from-primary/5 to-primary/10 rounded-xl border border-primary/20 overflow-hidden">
                  <div className="bg-primary/80 text-white px-3 py-2 text-sm font-semibold text-center">
                    Tablas Base
                  </div>
                  <div className="p-3 space-y-1.5">
                    {tablesByCategory.azure_base.tables.map((table) => (
                      <div
                        key={table.id}
                        className="text-xs text-slate-700 bg-white/80 px-2 py-1.5 rounded-lg border border-primary/10"
                      >
                        {table.name}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Tablas Materiales */}
                <div className="bg-gradient-to-b from-amber-50 to-amber-100 rounded-xl border border-amber-200 overflow-hidden">
                  <div className="bg-amber-600 text-white px-3 py-2 text-sm font-semibold text-center">
                    Tablas Materiales
                  </div>
                  <div className="p-3 space-y-1.5">
                    {tablesByCategory.azure_materiales.tables.map((table) => (
                      <div
                        key={table.id}
                        className="text-xs text-slate-700 bg-white/80 px-2 py-1.5 rounded-lg border border-amber-200"
                      >
                        {table.name}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Modelo Truncado */}
                <div className="bg-gradient-to-b from-rose-50 to-rose-100 rounded-xl border border-rose-200 overflow-hidden">
                  <div className="bg-rose-700 text-white px-3 py-2 text-sm font-semibold text-center">
                    Modelo Truncado
                  </div>
                  <div className="p-3 space-y-1.5">
                    {tablesByCategory.azure_truncado.tables.map((table) => (
                      <div
                        key={table.id}
                        className="text-xs text-slate-700 bg-white/80 px-2 py-1.5 rounded-lg border border-rose-200"
                      >
                        {table.name}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Modelo Fluido */}
                <div className="bg-gradient-to-b from-emerald-50 to-emerald-100 rounded-xl border border-emerald-200 overflow-hidden">
                  <div className="bg-emerald-700 text-white px-3 py-2 text-sm font-semibold text-center">
                    Modelo Fluido
                  </div>
                  <div className="p-3 space-y-1.5">
                    {tablesByCategory.azure_fluido.tables.map((table) => (
                      <div
                        key={table.id}
                        className="text-xs text-slate-700 bg-white/80 px-2 py-1.5 rounded-lg border border-emerald-200"
                      >
                        {table.name}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Arrow Down */}
            <div className="flex justify-center mb-8">
              <div className="flex flex-col items-center">
                <div className="w-0.5 h-8 bg-slate-400" />
                <ArrowDown className="h-6 w-6 text-slate-400 -mt-1" />
              </div>
            </div>

            {/* Destinations Row */}
            <div className="flex justify-center gap-8">
              <div className="w-64 bg-white rounded-xl border-2 border-indigo-300 p-5 text-center shadow-sm hover:shadow-md transition-shadow">
                <div className="w-14 h-14 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <BarChart3 className="h-7 w-7 text-indigo-600" />
                </div>
                <h4 className="font-bold text-indigo-800 mb-1">Reportería en la Nube</h4>
                <p className="text-sm text-slate-500">Superset</p>
              </div>
              <div className="w-64 bg-white rounded-xl border-2 border-primary p-5 text-center shadow-sm hover:shadow-md transition-shadow">
                <div className="w-14 h-14 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Monitor className="h-7 w-7 text-primary" />
                </div>
                <h4 className="font-bold text-primary mb-1">Sistema Cotizador</h4>
                <p className="text-sm text-slate-500">en la Nube Azure</p>
              </div>
            </div>
          </div>
        </section>

        {/* Process of SPs Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-primary mb-6 flex items-center gap-2">
            <Table2 className="h-6 w-6" />
            Proceso de Ejecución de SPs para el Cotizador y Reportería
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {spCategories.map((category, catIndex) => (
              <div key={category.id} className="relative">
                {/* Category Header */}
                <div className={`${category.color} text-white px-4 py-3 rounded-t-xl`}>
                  <div className="flex items-center gap-2">
                    <Database className="h-5 w-5" />
                    <span className="font-bold">{category.title}</span>
                  </div>
                  <p className="text-xs opacity-80 mt-1">{category.description}</p>
                </div>

                {/* SPs List */}
                <div className="border border-t-0 border-border rounded-b-xl bg-card">
                  {category.sps.map((sp, spIndex) => (
                    <div
                      key={sp.number}
                      className={`p-3 ${spIndex !== category.sps.length - 1 ? "border-b border-border" : ""}`}
                    >
                      <button
                        onClick={() => setExpandedSp(expandedSp === sp.number ? null : sp.number)}
                        className="w-full text-left"
                      >
                        <div className="flex items-start gap-3">
                          <div
                            className={`${category.color} text-white w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0`}
                          >
                            {sp.number}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              {expandedSp === sp.number ? (
                                <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
                              ) : (
                                <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                              )}
                              <span className="text-sm font-medium text-foreground line-clamp-2">{sp.title}</span>
                            </div>
                            <code className="text-[10px] bg-muted px-1.5 py-0.5 rounded text-primary font-mono mt-1 inline-block">
                              {sp.sp}
                            </code>
                          </div>
                        </div>
                      </button>

                      {/* Expanded Details */}
                      {expandedSp === sp.number && (
                        <div className="mt-3 ml-10 space-y-2">
                          <div>
                            <span className="text-xs font-semibold text-muted-foreground">Tablas de Entrada:</span>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {sp.inputTables.map((tableId, i) => {
                                const tableInfo = getTableInfo(tableId)
                                return tableInfo ? (
                                  <span
                                    key={i}
                                    className={`text-[10px] px-2 py-0.5 rounded ${tableInfo.categoryInfo.bgColor} ${tableInfo.categoryInfo.textColor}`}
                                  >
                                    {tableInfo.name}
                                  </span>
                                ) : (
                                  <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-gray-100 text-gray-700">
                                    {tableId}
                                  </span>
                                )
                              })}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <ArrowRight className="h-3 w-3 text-muted-foreground" />
                          </div>
                          <div>
                            <span className="text-xs font-semibold text-muted-foreground">Tablas de Salida:</span>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {sp.outputTables.map((tableId, i) => {
                                const tableInfo = getTableInfo(tableId)
                                return tableInfo ? (
                                  <span
                                    key={i}
                                    className={`text-[10px] px-2 py-0.5 rounded ${tableInfo.categoryInfo.bgColor} ${tableInfo.categoryInfo.textColor} font-semibold`}
                                  >
                                    {tableInfo.name}
                                  </span>
                                ) : (
                                  <span
                                    key={i}
                                    className="text-[10px] px-2 py-0.5 rounded bg-green-100 text-green-700 font-semibold"
                                  >
                                    {tableId}
                                  </span>
                                )
                              })}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Arrow to next category */}
                {catIndex < spCategories.length - 1 && (
                  <div className="hidden md:flex absolute -right-3 top-1/2 transform -translate-y-1/2 z-10">
                    <ArrowRight className="h-6 w-6 text-primary" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
