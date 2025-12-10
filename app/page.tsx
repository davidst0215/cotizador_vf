"use client"

import { useState } from "react"
import ManualUsuario from "@/components/manual-usuario"
import ManualSPs from "@/components/manual-sps"

export default function Page() {
  const [activeTab, setActiveTab] = useState<"cotizador" | "sps">("cotizador")

  return (
    <div className="min-h-screen bg-background">
      {/* Tab Navigation */}
      <div className="sticky top-0 z-50 bg-primary border-b border-primary/20 print:hidden">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-1">
            <button
              onClick={() => setActiveTab("cotizador")}
              className={`px-6 py-4 font-medium text-sm transition-colors ${
                activeTab === "cotizador"
                  ? "bg-background text-primary rounded-t-lg"
                  : "text-primary-foreground/80 hover:text-primary-foreground hover:bg-primary/80"
              }`}
            >
              Manual del Cotizador
            </button>
            <button
              onClick={() => setActiveTab("sps")}
              className={`px-6 py-4 font-medium text-sm transition-colors ${
                activeTab === "sps"
                  ? "bg-background text-primary rounded-t-lg"
                  : "text-primary-foreground/80 hover:text-primary-foreground hover:bg-primary/80"
              }`}
            >
              Manual de Ejecución de SPs
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      {activeTab === "cotizador" ? <ManualUsuario /> : <ManualSPs />}
    </div>
  )
}
