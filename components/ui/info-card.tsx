import type React from "react"
import { Info, AlertTriangle, CheckCircle2, Lightbulb } from "lucide-react"

interface InfoCardProps {
  type?: "info" | "warning" | "success" | "tip"
  title?: string
  children: React.ReactNode
}

const variants = {
  info: {
    bg: "bg-blue-50",
    border: "border-blue-200",
    icon: Info,
    iconColor: "text-blue-600",
    titleColor: "text-blue-800",
  },
  warning: {
    bg: "bg-amber-50",
    border: "border-amber-200",
    icon: AlertTriangle,
    iconColor: "text-amber-600",
    titleColor: "text-amber-800",
  },
  success: {
    bg: "bg-green-50",
    border: "border-green-200",
    icon: CheckCircle2,
    iconColor: "text-green-600",
    titleColor: "text-green-800",
  },
  tip: {
    bg: "bg-purple-50",
    border: "border-purple-200",
    icon: Lightbulb,
    iconColor: "text-purple-600",
    titleColor: "text-purple-800",
  },
}

export function InfoCard({ type = "info", title, children }: InfoCardProps) {
  const variant = variants[type]
  const Icon = variant.icon

  return (
    <div className={`${variant.bg} ${variant.border} border rounded-xl p-4 my-4`}>
      <div className="flex gap-3">
        <Icon className={`w-5 h-5 ${variant.iconColor} flex-shrink-0 mt-0.5`} />
        <div>
          {title && <h4 className={`font-semibold ${variant.titleColor} mb-1`}>{title}</h4>}
          <div className="text-sm text-foreground/80">{children}</div>
        </div>
      </div>
    </div>
  )
}
