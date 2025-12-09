import { Settings, Zap, Timer } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { InfoCard } from "@/components/ui/info-card"

export function SectionVersiones() {
  return (
    <section className="mb-16 page-break">
      <SectionHeader
        id="versiones"
        number={6}
        title="Versiones de Cálculo"
        description="Metodologías FLUIDO y TRUNCADO para diferentes escenarios"
        icon={Settings}
      />

      <div className="prose prose-slate max-w-none">
        <p className="text-lg text-foreground leading-relaxed mb-8">
          El sistema ofrece <strong>2 metodologías</strong> de cálculo diferentes según las necesidades de precisión y
          velocidad.
        </p>

        <div className="grid md:grid-cols-2 gap-6">
          {/* FLUIDO */}
          <div className="bg-card border-2 border-primary rounded-xl overflow-hidden">
            <div className="bg-primary text-primary-foreground p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                  <Zap className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-lg">FLUIDO</h3>
                  <p className="text-sm text-white/70">Metodología flexible y dinámica</p>
                </div>
              </div>
            </div>
            <div className="p-5">
              <h4 className="font-semibold text-foreground mb-3">Características:</h4>
              <ul className="space-y-2 text-sm text-foreground">
                <li className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2" />
                  Cálculos más complejos y precisos
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2" />
                  Mayor cantidad de factores aplicados
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2" />
                  Ajustes dinámicos en tiempo real
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2" />
                  Considera más variables históricas
                </li>
              </ul>
              <div className="mt-4 p-3 bg-secondary rounded-lg">
                <h5 className="text-sm font-medium text-foreground mb-1">Cuándo usar:</h5>
                <p className="text-xs text-muted-foreground">
                  Cotizaciones de nuevos productos, estilos complejos, máxima precisión requerida.
                </p>
              </div>
            </div>
          </div>

          {/* TRUNCADO */}
          <div className="bg-card border border-border rounded-xl overflow-hidden">
            <div className="bg-muted p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-foreground/10 rounded-lg flex items-center justify-center">
                  <Timer className="w-5 h-5 text-foreground" />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-foreground">TRUNCADO</h3>
                  <p className="text-sm text-muted-foreground">Metodología simplificada</p>
                </div>
              </div>
            </div>
            <div className="p-5">
              <h4 className="font-semibold text-foreground mb-3">Características:</h4>
              <ul className="space-y-2 text-sm text-foreground">
                <li className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full mt-2" />
                  Cálculos más directos y simples
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full mt-2" />
                  Menos factores de ajuste
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full mt-2" />
                  Proceso más rápido
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full mt-2" />
                  Estimaciones conservadoras
                </li>
              </ul>
              <div className="mt-4 p-3 bg-muted rounded-lg">
                <h5 className="text-sm font-medium text-foreground mb-1">Cuándo usar:</h5>
                <p className="text-xs text-muted-foreground">
                  Cotizaciones rápidas, estilos repetitivos, renovación de órdenes existentes.
                </p>
              </div>
            </div>
          </div>
        </div>

        <InfoCard type="info" title="Selector de Versión">
          El selector se encuentra en la parte superior del <strong>Formulario de Cotización</strong>. Al cambiar la
          versión, el sistema recarga automáticamente la lista de clientes, tipos de prenda y catálogo de materiales
          correspondientes.
        </InfoCard>
      </div>
    </section>
  )
}
