import type React from "react"
interface DataTableProps {
  headers: string[]
  rows: (string | React.ReactNode)[][]
  caption?: string
}

export function DataTable({ headers, rows, caption }: DataTableProps) {
  return (
    <div className="my-6 overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-primary text-primary-foreground">
            {headers.map((header, i) => (
              <th key={i} className="px-4 py-3 text-left text-sm font-semibold first:rounded-tl-lg last:rounded-tr-lg">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className={`border-b border-border ${i % 2 === 0 ? "bg-card" : "bg-muted/50"}`}>
              {row.map((cell, j) => (
                <td key={j} className="px-4 py-3 text-sm">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {caption && <p className="text-xs text-muted-foreground mt-2 italic">{caption}</p>}
    </div>
  )
}
