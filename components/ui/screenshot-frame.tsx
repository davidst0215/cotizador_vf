interface ScreenshotFrameProps {
  src: string
  alt: string
  caption?: string
}

export function ScreenshotFrame({ src, alt, caption }: ScreenshotFrameProps) {
  return (
    <figure className="my-6">
      <div className="bg-muted rounded-xl p-2 border border-border">
        <div className="bg-card rounded-lg overflow-hidden shadow-sm">
          <div className="bg-muted border-b border-border px-4 py-2 flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-400" />
              <div className="w-3 h-3 rounded-full bg-yellow-400" />
              <div className="w-3 h-3 rounded-full bg-green-400" />
            </div>
            <span className="text-xs text-muted-foreground ml-2">Sistema Cotizador TDV</span>
          </div>
          <img src={src || "/placeholder.svg"} alt={alt} className="w-full h-auto" />
        </div>
      </div>
      {caption && <figcaption className="text-center text-sm text-muted-foreground mt-3 italic">{caption}</figcaption>}
    </figure>
  )
}
