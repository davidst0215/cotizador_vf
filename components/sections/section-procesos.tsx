import { BarChart3, Factory, Scissors } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { ScreenshotFrame } from "@/components/ui/screenshot-frame"
import { InfoCard } from "@/components/ui/info-card"
import { DataTable } from "@/components/ui/data-table"

export function SectionProcesos() {
  const wipTextiles = [
    ["10", "Abastecimiento de Hilado", "Compra y preparación de hilos"],
    ["14", "Teñido de Hilado", "Teñido de hilos antes del tejido"],
    ["16", "Tejido de Tela y Rectilíneos", "Fabricación de la tela base"],
    ["19a", "Teñido de Tela", "Teñido de tela terminada"],
    ["19c", "Despacho", "Logística y distribución de tela"],
    ["24", "Estampado Tela", "Aplicación de diseños en tela"],
  ]

  const wipManufactura = [
    ["34", "Corte", "Corte de piezas de la prenda"],
    ["40", "Costura", "Ensamblaje de la prenda"],
    ["49", "Acabado", "Inspección, planchado, etiquetado"],
    ["37", "Bordado Pieza", "Bordado de las piezas antes de la costura"],
    ["43", "Bordado Prenda", "Bordado de las prendas despues de la costura"],
    ["44", "Estampado Prendas", "Estampado de logos y otros"],
    ["45", "Lavado en Prenda", "Lavado de prenda despues de estampado"],
    ["50", "Movimiento logístico", "Trasporte entre areas/procesos"],
  ]

  return (
    <section className="mb-16 page-break">
      <SectionHeader
        id="procesos"
        number={3}
        title="Resultados de Procesos"
        description="Selección de OPs de referencia y procesos productivos (WIPs) para la fabricación"
        icon={BarChart3}
      />

      <div className="prose prose-slate max-w-none">
        <h3 className="text-xl font-semibold text-foreground mt-4 mb-4">Header de Cotización</h3>

        <p className="text-foreground mb-4">
          Al ingresar a esta pestaña, verá un resumen de la cotización generada con su ID único, fecha de creación y
          versión de datos utilizada.
        </p>

        <div className="bg-primary text-primary-foreground rounded-xl p-6 my-4">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-white/60 block">ID:</span>
              <span className="font-mono">COT_20251206_111243</span>
            </div>
            <div>
              <span className="text-white/60 block">Fecha:</span>
              <span>6/12/2025, 11:12 a.m.</span>
            </div>
            <div>
              <span className="text-white/60 block">Versión:</span>
              <span className="bg-white/20 px-2 py-0.5 rounded">FLUIDO</span>
            </div>
          </div>
        </div>

        <h3 className="text-xl font-semibold text-foreground mt-8 mb-4">Tabla de OPs de Referencia</h3>

        <p className="text-foreground mb-4">
          Seleccione las órdenes de producción históricas que servirán como referencia para el cálculo de costos. El
          sistema recomienda mínimo 3 OPs para mayor precisión.
        </p>

        <InfoCard type="info" title="Filtros Disponibles">
          Puede filtrar las OPs por tamaño de lote: <strong>Micro Lote (1-50)</strong>,{" "}
          <strong>Lote Pequeño (51-500)</strong>, <strong>Lote Mediano (501-1000)</strong>,{" "}
          <strong>Lote Grande (1001-4000)</strong> o <strong>Lote Masivo (4001+)</strong>. El sistema también permite
          una selección 1 a 1 de las OPs para mayor personalización.
        </InfoCard>

        <ScreenshotFrame
          src="/images/procesos.png"
          alt="Pestaña Resultados de Procesos"
          caption="Figura 3.1: Vista de Resultados de Procesos con OPs de referencia seleccionadas"
        />

        <h3 className="text-xl font-semibold text-foreground mt-8 mb-4">Análisis de Costos por WIP</h3>

        <p className="text-foreground mb-4">
          En esta sección puede configurar la ruta de producción seleccionando o deseleccionando los WIPs (Work In
          Progress) que aplican a su producto. Cada WIP muestra su costo Textil y de Manufactura por prenda.
        </p>

        <InfoCard type="tip" title="Configuración de Ruta">
          Marque o desmarque los WIPs según los procesos que requiera su producto. Por ejemplo, si no necesita teñido de
          hilado, puede desmarcarlo para excluirlo del cálculo de costos.
        </InfoCard>

        <ScreenshotFrame
          src="/images/wips.png"
          alt="Análisis de Costos por WIP"
          caption="Figura 3.2: Análisis detallado de Costos por WIP con desglose Textil y Manufactura"
        />

        <h3 className="text-xl font-semibold text-foreground mt-8 mb-4">Procesos Textiles</h3>

        <div className="flex items-center gap-2 mb-4">
          <Factory className="w-5 h-5 text-primary" />
          <span className="text-sm font-medium text-primary">WIPs del área Textil</span>
        </div>

        <DataTable headers={["WIP", "Nombre", "Descripción"]} rows={wipTextiles} />

        <h3 className="text-xl font-semibold text-foreground mt-8 mb-4">Procesos de Manufactura</h3>

        <div className="flex items-center gap-2 mb-4">
          <Scissors className="w-5 h-5 text-primary" />
          <span className="text-sm font-medium text-primary">WIPs del área Manufactura</span>
        </div>

        <DataTable headers={["WIP", "Nombre", "Descripción"]} rows={wipManufactura} />

        <InfoCard type="tip" title="Factor de Ajuste">
          Para cada WIP puede ajustar un <strong>factor multiplicador</strong>. Valor 1.00 = sin cambio. Ejemplo: 1.15 =
          15% más costo, 0.85 = 15% menos costo.
        </InfoCard>
      </div>
    </section>
  )
}
