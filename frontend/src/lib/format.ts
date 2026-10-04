export function money(value: string | number | null | undefined, symbol = '৳'): string {
  const n = Number(value ?? 0)
  return `${symbol}${n.toFixed(2)}`
}

export function formatDate(value: string): string {
  return new Date(value).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}
