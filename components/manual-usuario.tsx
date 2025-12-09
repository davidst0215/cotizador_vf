"use client"

import { useState } from "react"
import { FileText, BarChart3, Layers, DollarSign, BookOpen, Printer, Menu, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { TableOfContents } from "@/components/table-of-contents"
import { SectionIntro } from "@/components/sections/section-intro"
import { SectionFormulario } from "@/components/sections/section-formulario"
import { SectionProcesos } from "@/components/sections/section-procesos"
import { SectionMateriales } from "@/components/sections/section-materiales"
import { SectionCostos } from "@/components/sections/section-costos"
import { SectionVersiones } from "@/components/sections/section-versiones"
import { SectionFlujo } from "@/components/sections/section-flujo"

export default function ManualUsuario() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const handlePrint = () => {
    window.print()
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-primary text-primary-foreground no-print">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden p-2 hover:bg-primary/80 rounded-lg"
            >
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center">
                <DollarSign className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-lg font-bold">Sistema Cotizador TDV</h1>
                <p className="text-xs text-white/70">Manual de Usuario v2.0</p>
              </div>
            </div>
          </div>
          <Button
            onClick={handlePrint}
            variant="outline"
            className="bg-white/10 border-white/20 text-white hover:bg-white/20"
          >
            <Printer className="w-4 h-4 mr-2" />
            Imprimir PDF
          </Button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto flex">
        {/* Sidebar */}
        <aside
          className={`
          fixed lg:sticky top-[72px] left-0 h-[calc(100vh-72px)] w-72 bg-card border-r border-border
          transform transition-transform duration-300 z-40 overflow-y-auto no-print
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
        >
          <TableOfContents onItemClick={() => setSidebarOpen(false)} />
        </aside>

        {/* Overlay for mobile */}
        {sidebarOpen && (
          <div className="fixed inset-0 bg-black/50 z-30 lg:hidden no-print" onClick={() => setSidebarOpen(false)} />
        )}

        {/* Main Content */}
        <main className="flex-1 min-w-0 px-4 lg:px-8 py-8">
          {/* Cover Page */}
          <section className="mb-16 page-break">
            <div className="bg-primary text-primary-foreground rounded-2xl p-8 lg:p-12 mb-8">
              <div className="flex items-center gap-2 text-white/70 text-sm mb-4">
                <BookOpen className="w-4 h-4" />
                <span>Documentación Oficial</span>
              </div>
              <h1 className="text-3xl lg:text-5xl font-bold mb-4 text-balance">Manual de Usuario</h1>
              <p className="text-xl lg:text-2xl text-white/80 mb-6">Sistema Cotizador TDV v2.0</p>
              <p className="text-white/60 max-w-2xl leading-relaxed">
                Guía completa para la generación de cotizaciones precisas de prendas de vestir, considerando procesos
                productivos, materiales y factores de ajuste comercial.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <span className="px-3 py-1.5 bg-white/10 rounded-full text-sm">Metodología WIP-Based</span>
                <span className="px-3 py-1.5 bg-white/10 rounded-full text-sm">Costos Históricos</span>
                <span className="px-3 py-1.5 bg-white/10 rounded-full text-sm">Exportación PDF</span>
              </div>
            </div>

            {/* Quick Navigation */}
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { icon: FileText, title: "Formulario", desc: "Información del producto", section: "formulario" },
                { icon: BarChart3, title: "Procesos", desc: "WIPs y costos", section: "procesos" },
                { icon: Layers, title: "Materiales", desc: "Hilos, avíos y telas", section: "materiales" },
                { icon: DollarSign, title: "Costos", desc: "Precio final", section: "costos" },
              ].map((item) => (
                <a
                  key={item.section}
                  href={`#${item.section}`}
                  className="group bg-card border border-border rounded-xl p-5 hover:border-primary/50 hover:shadow-lg transition-all"
                >
                  <div className="w-10 h-10 bg-secondary rounded-lg flex items-center justify-center mb-3 group-hover:bg-primary group-hover:text-white transition-colors">
                    <item.icon className="w-5 h-5 text-primary group-hover:text-white" />
                  </div>
                  <h3 className="font-semibold text-foreground mb-1">{item.title}</h3>
                  <p className="text-sm text-muted-foreground">{item.desc}</p>
                </a>
              ))}
            </div>
          </section>

          {/* Content Sections */}
          <SectionIntro />
          <SectionFormulario />
          <SectionProcesos />
          <SectionMateriales />
          <SectionCostos />
          <SectionVersiones />
          <SectionFlujo />

          {/* Footer */}
          <footer className="mt-16 pt-8 border-t border-border text-center text-muted-foreground">
            <p className="text-sm">Sistema Cotizador TDV v2.0 - Manual de Usuario</p>
            <p className="text-xs mt-1">
              Documento generado el{" "}
              {new Date().toLocaleDateString("es-ES", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>
          </footer>
        </main>
      </div>
    </div>
  )
}
