import { Layers, Package, Ribbon } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { ScreenshotFrame } from "@/components/ui/screenshot-frame"
import { InfoCard } from "@/components/ui/info-card"
import { DataTable } from "@/components/ui/data-table"

export function SectionMateriales() {
  return (
    <section className="mb-16 page-break">
      <SectionHeader
        id="materiales"
        number={4}
        title="Análisis de Materiales"
        description="Configuración de costos de hilos, avíos y telas"
        icon={Layers}
      />

      <div className="prose prose-slate max-w-none">
        <p className="text-lg text-foreground leading-relaxed mb-6">
          Esta pestaña contiene <strong>3 desgloses independientes</strong> para configurar los materiales utilizados en
          la producción de la prenda.
        </p>

        {/* Desglose de Hilos */}
        <div className="bg-card border border-border rounded-xl p-6 my-8">
          <h3 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
            <div className="w-8 h-8 bg-secondary rounded-lg flex items-center justify-center">
              <Ribbon className="w-4 h-4 text-primary" />
            </div>
            Desglose de Hilos
          </h3>

          <ScreenshotFrame
            src="/images/hilos.png"
            alt="Análisis de Materiales - Hilos"
            caption="Figura 4.1: Configuración de hilos con modo Monto Fijo seleccionado"
          />

          <h4 className="font-semibold text-foreground mt-6 mb-3">Modos de Configuración</h4>

          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-muted rounded-lg p-4">
              <h5 className="font-medium text-foreground mb-2">Detallado</h5>
              <p className="text-sm text-muted-foreground">Editar el costo unitario de cada hilo manualmente.</p>
            </div>
            <div className="bg-primary/10 border border-primary/20 rounded-lg p-4">
              <h5 className="font-medium text-primary mb-2">Monto Fijo</h5>
              <p className="text-sm text-muted-foreground">Establecer un costo total fijo para todos los hilos.</p>
            </div>
            <div className="bg-muted rounded-lg p-4">
              <h5 className="font-medium text-foreground mb-2">Automático</h5>
              <p className="text-sm text-muted-foreground">Usa costos históricos con factores de ajuste.</p>
            </div>
          </div>
        </div>

        {/* Desglose de Avíos */}
        <div className="bg-card border border-border rounded-xl p-6 my-8">
          <h3 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
            <div className="w-8 h-8 bg-secondary rounded-lg flex items-center justify-center">
              <Package className="w-4 h-4 text-primary" />
            </div>
            Desglose de Avíos
          </h3>

          <ScreenshotFrame
            src="/images/avios.png"
            alt="Análisis de Materiales - Avíos"
            caption="Figura 4.2: Tabla de avíos con selección y costos por prenda"
          />

          <p className="text-foreground mt-4">
            Los avíos son accesorios y complementos necesarios para la prenda: botones, cierres, etiquetas, ribetes,
            elásticos, etc.
          </p>

          <DataTable
            headers={["Columna", "Descripción"]}
            rows={[
              ["Selección", "Checkbox para incluir/excluir el avío"],
              ["Nombre Avio", "Descripción completa del material"],
              ["Código Avio", "Identificador único del avío"],
              ["Unidades/prenda", "Cantidad necesaria por prenda"],
              ["Costo/prenda", "Costo unitario editable"],
              ["Histórico", "Acceso a gráfica de precios históricos"],
              ["Frecuencia", "Porcentaje de uso en OPs similares"],
            ]}
          />
        </div>

        {/* Desglose de Telas */}
        <div className="bg-card border border-border rounded-xl p-6 my-8">
          <h3 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
            <div className="w-8 h-8 bg-secondary rounded-lg flex items-center justify-center">
              <Layers className="w-4 h-4 text-primary" />
            </div>
            Desglose de Telas
          </h3>

          <InfoCard type="warning" title="Telas No Disponibles">
            Si no hay telas disponibles para el estilo seleccionado, el sistema mostrará un mensaje de advertencia. En
            este caso, el costo de telas será $0.00.
          </InfoCard>
        </div>

        <InfoCard type="success" title="Persistencia de Datos">
          El sistema <strong>guarda automáticamente</strong> toda la configuración cuando hace clic en "Calcular Costos
          Finales". Puede navegar a otras pestañas y regresar sin perder su trabajo.
        </InfoCard>
      </div>
    </section>
  )
}
