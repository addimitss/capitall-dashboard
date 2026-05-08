function fmt(v) {
  if (v == null) return '—'
  if (typeof v === 'number') {
    if (Number.isInteger(v) && Math.abs(v) < 1e6) return v.toLocaleString()
    if (Math.abs(v) >= 1e7) return (v / 1e7).toFixed(2) + ' Cr'
    if (Math.abs(v) >= 1e5) return (v / 1e5).toFixed(2) + ' L'
    return v.toLocaleString(undefined, { maximumFractionDigits: 2 })
  }
  return String(v)
}

export default function SummaryCards({ cards = [] }) {
  if (!cards.length) return null
  return (
    <div className="cards">
      {cards.map((c, i) => (
        <div key={i} className="card">
          <div className="label">{c.label}</div>
          {typeof c.value === 'object' && c.value !== null && !Array.isArray(c.value) ? (
            <div className="breakdown">
              {Object.entries(c.value).map(([k, v]) => (
                <span key={k}>{k}: <b>{fmt(v)}</b></span>
              ))}
            </div>
          ) : (
            <div className="value">{fmt(c.value)}</div>
          )}
        </div>
      ))}
    </div>
  )
}
