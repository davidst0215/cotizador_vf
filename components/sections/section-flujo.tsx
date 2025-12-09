import { GitBranch, ArrowRight, CheckCircle2 } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"

export function SectionFlujo() {
  const pasos = [
    {
      numero: 1,
      titulo: "Formulario de Cotización",
      descripcion: "Ingrese código de estilo, cliente/marca y tipo de prenda",
      accion: "Configurar Producción",
    },
    {
      numero: 2,
      titulo: "Resultados de Procesos",
      descripcion: "Seleccione OPs de referencia y configure WIPs",
      accion: "Continuar a Materiales",
    },
    {
      numero: 3,
      titulo: "Análisis de Materiales",
      descripcion: "Configure hilos, avíos y telas con el modo deseado",
      accion: "Calcular Costos Finales",
    },
    {
      numero: 4,
      titulo: "Costos Finales",
      descripcion: "Revise el desglose, ajuste factores y exporte",
      accion: "Descargar PDF",
    },
  ]

  return (
    <section className="mb-16">
      <SectionHeader
        id="flujo"
        number={7}
        title="Flujo Completo de Trabajo"
        description="Resumen del proceso de cotización paso a paso"
        icon={GitBranch}
      />

      <div className="prose prose-slate max-w-none">
        <div className="relative">
          {/* Timeline */}
          <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-border hidden md:block" />

          <div className="space-y-6">
            {pasos.map((paso, index) => (
              <div key={paso.numero} className="relative flex gap-4 md:gap-6">
                {/* Number */}
                <div className="relative z-10 w-12 h-12 bg-primary text-primary-foreground rounded-xl flex items-center justify-center font-bold text-lg flex-shrink-0">
                  {paso.numero}
                </div>

                {/* Content */}
                <div className="flex-1 bg-card border border-border rounded-xl p-5 pb-4">
                  <h3 className="font-semibold text-foreground text-lg mb-2">{paso.titulo}</h3>
                  <p className="text-muted-foreground mb-4">{paso.descripcion}</p>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-muted-foreground">Botón:</span>
                    <span className="bg-primary/10 text-primary px-3 py-1 rounded-full font-medium">{paso.accion}</span>
                  </div>

                  {index < pasos.length - 1 && (
                    <div className="absolute -bottom-3 left-1/2 transform -translate-x-1/2 md:hidden">
                      <ArrowRight className="w-5 h-5 text-primary rotate-90" />
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Summary Box */}
        <div className="mt-12 bg-secondary rounded-xl p-6">
          <div className="flex items-start gap-4">
            <CheckCircle2 className="w-8 h-8 text-green-600 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-foreground text-lg mb-2">Cotización Completada</h3>
              <p className="text-muted-foreground">
                Al finalizar el flujo, tendrá una cotización completa con desglose detallado de costos, vectores de
                ajuste aplicados y un PDF profesional listo para presentar al cliente.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
