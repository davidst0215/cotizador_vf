import { FileText, Search, CheckCircle2 } from "lucide-react"
import { SectionHeader } from "@/components/ui/section-header"
import { ScreenshotFrame } from "@/components/ui/screenshot-frame"
import { InfoCard } from "@/components/ui/info-card"
import { DataTable } from "@/components/ui/data-table"

export function SectionFormulario() {
  const camposTable = [
    ["Estilo Cliente", "Texto con búsqueda", "Condicional*", "Código del estilo proporcionado por el cliente"],
    ["Cliente/Marca", "Lista desplegable", "Sí", "Marca o cliente para quien se cotiza"],
    ["Estilo Propio", "Texto con búsqueda", "Condicional*", "Código interno de la empresa para el estilo"],
    ["Tipo de Prenda", "Lista desplegable", "Sí", "Clasificación del producto"],
    ["Versión de Cálculo", "Selector visual", "No", "FLUIDO o TRUNCADO"],
  ]

  return (
    <section className="mb-16 page-break">
      <SectionHeader
        id="formulario"
        number={2}
        title="Formulario de Cotización"
        description="Ingreso de información básica del producto a cotizar"
        icon={FileText}
      />

      <ScreenshotFrame
        src="/images/formulario.png"
        alt="Pestaña Formulario de Cotización"
        caption="Figura 2.1: Vista del Formulario de Cotización con información del producto"
      />

      <div className="prose prose-slate max-w-none">
        <h3 className="text-xl font-semibold text-foreground mt-8 mb-4">Campos del Formulario</h3>

        <DataTable
          headers={["Campo", "Tipo", "Obligatorio", "Descripción"]}
          rows={camposTable}
          caption="* Debe ingresar AL MENOS UNO: Estilo Cliente O Estilo Propio"
        />

        <InfoCard type="warning" title="Nota Importante">
          Debe ingresar <strong>al menos uno</strong> de los siguientes campos: Estilo Cliente O Estilo Propio. No es
          necesario llenar ambos.
        </InfoCard>

        <h3 className="text-xl font-semibold text-foreground mt-8 mb-4">Búsqueda Automática</h3>

        <div className="bg-secondary/50 rounded-xl p-6 my-4">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
              <Search className="w-5 h-5 text-white" />
            </div>
            <div>
              <h4 className="font-semibold text-foreground mb-2">Autocompletado Inteligente</h4>
              <p className="text-sm text-muted-foreground mb-3">
                Al escribir en los campos de estilo, el sistema busca coincidencias y sugiere opciones:
              </p>
              <ol className="text-sm text-foreground space-y-2">
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-primary text-white rounded-full flex items-center justify-center text-xs flex-shrink-0">
                    1
                  </span>
                  El sistema busca coincidencias en la base de datos
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 bg-primary text-white rounded-full flex items-center justify-center text-xs flex-shrink-0">
                   
                    2
                  </span>
                  Al seleccionar, rellena automáticamente tipo de prenda y cliente
                </li>
              </ol>
            </div>
          </div>
        </div>

        <h3 className="text-xl font-semibold text-foreground mt-8 mb-4">Validaciones</h3>

        <p className="text-foreground mb-4">Antes de continuar, el sistema verifica:</p>

        <ul className="space-y-2">
          {["Al menos un código de estilo ingresado", "Cliente/Marca seleccionado", "Tipo de prenda seleccionado"].map(
            (item, i) => (
              <li key={i} className="flex items-center gap-2 text-foreground">
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                {item}
              </li>
            ),
          )}
        </ul>

        <InfoCard type="tip" title="Botón Configurar Producción">
          Este botón procesa la información ingresada, busca órdenes de producción históricas similares y avanza
          automáticamente a la Pestaña 2.
        </InfoCard>
      </div>
    </section>
  )
}
