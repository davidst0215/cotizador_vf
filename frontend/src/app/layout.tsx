import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Sistema Cotizador TDV',
  description: 'Sistema de cotización inteligente basado en metodología WIP',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es">
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}