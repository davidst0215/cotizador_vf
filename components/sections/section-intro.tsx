import { BookOpen, CheckCircle2 } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { InfoCard } from "@/components/ui/info-card"

export function SectionIntro() {
  const features = [
    "Buscar estilos existentes o crear cotizaciones para nuevos estilos",
    "Seleccionar procesos productivos basados en órdenes de producción históricas",
    "Ajustar costos de materiales con múltiples opciones de configuración",
    "Aplicar factores comerciales y de complejidad",
    "Generar cotizaciones detalladas exportables a PDF",
  ]

  return (
    <section className="mb-16 page-break">
      <SectionHeader
        id="introduccion"
        number={1}
        title="Introducción"
        description="Descripción general del Sistema Cotizador TDV"
        icon={BookOpen}
      />

      <div className="prose prose-slate max-w-none">
        <p className="text-lg text-foreground leading-relaxed">
          El <strong>Sistema Cotizador TDV </strong> es una herramienta diseñada para generar
          cotizaciones considerando todos los aspectos del proceso productivo y de manteriales.
        </p>

        <div className="grid md:grid-cols-2 gap-4 my-8">
          <div className="bg-card border border-border rounded-xl p-5">
            <h3 className="font-semibold text-foreground mb-3">Procesos de Producción</h3>
            <p className="text-sm text-muted-foreground">
              Análisis de WIPs textiles y de manufactura basados en datos históricos.
            </p>
          </div>
          <div className="bg-card border border-border rounded-xl p-5">
            <h3 className="font-semibold text-foreground mb-3">Materiales</h3>
            <p className="text-sm text-muted-foreground">
              Configuración detallada de hilos, avíos y telas con múltiples modos.
            </p>
          </div>
          <div className="bg-card border border-border rounded-xl p-5">
            <h3 className="font-semibold text-foreground mb-3">Factores de Ajuste</h3>
            <p className="text-sm text-muted-foreground">
              Vectores de lote, esfuerzo, marca y estilo para precisión comercial.
            </p>
          </div>
          <div className="bg-card border border-border rounded-xl p-5">
            <h3 className="font-semibold text-foreground mb-3">Costos Indirectos</h3>
            <p className="text-sm text-muted-foreground">
              Administración, ventas y gastos fijos integrados automáticamente.
            </p>
          </div>
        </div>

        <h3 className="text-xl font-semibold text-foreground mt-8 mb-4">Capacidades del Sistema</h3>

        <ul className="space-y-3">
          {features.map((feature, i) => (
            <li key={i} className="flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <span className="text-foreground">{feature}</span>
            </li>
          ))}
        </ul>

        <InfoCard type="info" title="Estructura del Sistema">
          El sistema está organizado en <strong>4 pestañas principales</strong> que representan un flujo secuencial de
          trabajo: Formulario → Procesos → Materiales → Costos Finales.
        </InfoCard>
      </div>
    </section>
  )
}
