import type { LucideIcon } from "lucide-react"

interface SectionHeaderProps {
  id: string
  number: number
  title: string
  description: string
  icon: LucideIcon
}

export function SectionHeader({ id, number, title, description, icon: Icon }: SectionHeaderProps) {
  return (
    <div id={id} className="scroll-mt-24 mb-8">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center flex-shrink-0">
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-medium text-primary bg-secondary px-2 py-0.5 rounded">Sección {number}</span>
          </div>
          <h2 className="text-2xl lg:text-3xl font-bold text-foreground">{title}</h2>
          <p className="text-muted-foreground mt-1">{description}</p>
        </div>
      </div>
    </div>
  )
}
