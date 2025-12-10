import { DollarSign, TrendingUp, Download, Percent } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { ScreenshotFrame } from "@/components/ui/screenshot-frame"
import { InfoCard } from "@/components/ui/info-card"
import { DataTable } from "@/components/ui/data-table"

export function SectionCostos() {
  const componentesTable = [
    ["Costo Textil", "WIPs Textiles", "$5.19"],
    ["Costo Manufactura", "WIPs Manufactura", "$9.14"],
    ["Materia Prima (Hilos)", "Configuración materiales", "$20.00"],
    ["Tela Comprada", "Configuración materiales", "$0.00"],
    ["Costo Avíos", "Configuración materiales", "$0.15"],
    ["Costo Indirecto Fijo", "Base de datos", "$1.13"],
    ["Gasto Administración", "Base de datos", "$0.75"],
    ["Gasto Ventas", "Base de datos", "$0.44"],
  ]

  return (
    <section className="mb-16 page-break">
      <SectionHeader
        id="costos"
        number={5}
        title="Costos Finales"
        description="Desglose completo y precio final de cotización"
        icon={DollarSign}
      />

      <ScreenshotFrame
        src="/images/costos.png"
        alt="Pestaña Costos Finales"
        caption="Figura 5.1: Desglose detallado de costos con vectores de ajuste y precio final"
      />

      <div className="prose prose-slate max-w-none">
        <h3 className="text-xl font-semibold text-foreground mt-8 mb-4">Componentes de Costo</h3>

        <DataTable headers={["Componente", "Fuente", "Costo"]} rows={componentesTable} />

        <h3 className="text-xl font-semibold text-foreground mt-8 mb-4">Vector de Ajuste</h3>

        <p className="text-foreground mb-4">
          Los vectores de ajuste permiten modificar el precio final aplicando factores multiplicadores.
          <strong> Todos los valores son configurables</strong> mediante los controles +/- en la interfaz.
        </p>

        <div className="bg-secondary rounded-xl p-6 my-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-foreground mb-3">Factores Multiplicadores (Configurables)</h4>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-card rounded-lg p-4 border border-border">
                  <span className="text-sm text-muted-foreground">Factor Esfuerzo (Original: 1.15)</span>
                  <div className="flex items-center justify-between mt-2">
                    <span className="font-medium">Valor Ajustado:</span>
                    <span className="font-mono bg-muted px-3 py-1 rounded">1.00</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">Ajustable con controles +/-</p>
                </div>
                <div className="bg-card rounded-lg p-4 border border-border">
                  <span className="text-sm text-muted-foreground">Factor Marca (Original: 1.10)</span>
                  <div className="flex items-center justify-between mt-2">
                    <span className="font-medium">Valor Ajustado:</span>
                    <span className="font-mono bg-muted px-3 py-1 rounded">1.00</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">Ajustable con controles +/-</p>
                </div>
              </div>
              <div className="mt-4 p-4 bg-card rounded-lg border border-border">
                <div className="flex items-center justify-between">
                  <span className="font-semibold">Vector Total:</span>
                  <span className="text-2xl font-bold text-primary">1.000</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <h3 className="text-xl font-semibold text-foreground mt-8 mb-4">Precio Final y Margen</h3>

        <div className="bg-primary text-primary-foreground rounded-xl p-6 my-6">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-white/70 mb-2">Costo Base Total</h4>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold">$36.79</span>
                <span className="text-white/60">por prenda</span>
              </div>
              <p className="text-sm text-white/60 mt-2">Total por Kg: $102.77</p>
            </div>
            <div className="bg-accent rounded-lg p-4">
              <h4 className="text-white/90 mb-1">Precio Final ($ por prenda)</h4>
              <div className="text-4xl font-bold">$42.31/prenda</div>
              <p className="text-sm text-white/70 mt-2">Margen: 15.00%</p>
              <p className="text-xs text-white/50 mt-1">$36.79 × (1 + 15.0% × 1.000)</p>
            </div>
          </div>
        </div>

        <div className="bg-secondary rounded-xl p-6 my-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-accent rounded-lg flex items-center justify-center flex-shrink-0">
              <Percent className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-foreground mb-2">Margen de Ganancia (Configurable)</h4>
              <p className="text-foreground text-sm mb-3">
                El margen de ganancia es <strong>completamente configurable</strong>. Por defecto se muestra en 15%,
                pero puede ajustarse según las necesidades comerciales de cada cotización.
              </p>
              <div className="bg-card rounded-lg p-4 border border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-sm text-muted-foreground">Margen (%)</span>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="px-2 py-1 bg-muted rounded text-xs">-</span>
                      <span className="font-mono bg-muted px-3 py-1 rounded font-medium">15.00</span>
                      <span className="px-2 py-1 bg-muted rounded text-xs">+</span>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground max-w-[200px]">
                    Use los controles +/- para ajustar el porcentaje de margen deseado
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <InfoCard type="tip" title="Controles Dinámicos">
          Los cambios en el margen y factores de ajuste recalculan el precio final <strong>inmediatamente</strong>. Útil
          para simulaciones y negociaciones con clientes.
        </InfoCard>

        <div className="flex items-center gap-4 mt-8 p-4 bg-muted rounded-xl">
          <Download className="w-8 h-8 text-primary" />
          <div>
            <h4 className="font-semibold text-foreground">Descargar PDF</h4>
            <p className="text-sm text-muted-foreground">
              Genera un documento PDF profesional con toda la información de la cotización.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
