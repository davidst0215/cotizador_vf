"use client"

import { BookOpen, FileText, BarChart3, Layers, DollarSign, Settings, GitBranch } from "lucide-react"

interface TableOfContentsProps {
  onItemClick?: () => void
}

const sections = [
  { id: "introduccion", title: "Introducción", icon: BookOpen },
  { id: "formulario", title: "Formulario de Cotización", icon: FileText },
  { id: "procesos", title: "Resultados de Procesos", icon: BarChart3 },
  { id: "materiales", title: "Análisis de Materiales", icon: Layers },
  { id: "costos", title: "Costos Finales", icon: DollarSign },
  { id: "versiones", title: "Versiones de Cálculo", icon: Settings },
  { id: "flujo", title: "Flujo de Trabajo", icon: GitBranch },
]

export function TableOfContents({ onItemClick }: TableOfContentsProps) {
  return (
    <nav className="p-4">
      <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4 px-3">Contenido</h2>
      <ul className="space-y-1">
        {sections.map((section, index) => (
          <li key={section.id}>
            <a
              href={`#${section.id}`}
              onClick={onItemClick}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-foreground hover:bg-secondary transition-colors group"
            >
              <span className="w-6 h-6 bg-muted rounded flex items-center justify-center text-xs font-medium text-muted-foreground group-hover:bg-primary group-hover:text-white transition-colors">
                {index + 1}
              </span>
              <span className="text-sm font-medium">{section.title}</span>
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}
