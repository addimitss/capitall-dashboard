import { useEffect, useState } from 'react'
import { InsightsAPI } from '../api/client'
import SummaryCards from '../components/SummaryCards'
import Charts from '../components/Charts'

const SEV_COLORS = { high: '#7a1212', medium: '#CC7722', low: '#7393B3' }

function fmt(v) {
  if (v == null) return '—'
  if (typeof v === 'number') {
    if (Math.abs(v) >= 1e7) return (v / 1e7).toFixed(2) + ' Cr'
    if (Math.abs(v) >= 1e5) return (v / 1e5).toFixed(2) + ' L'
    return v.toLocaleString(undefined, { maximumFractionDigits: 2 })
  }
  return String(v)
}

export default function Overview() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancel = false
    setLoading(true); setError(null)
    InsightsAPI.overview()
      .then(d => { if (!cancel) setData(d) })
      .catch(e => { if (!cancel) setError(e?.response?.data?.detail || e.message) })
      .finally(() => { if (!cancel) setLoading(false) })
    return () => { cancel = true }
  }, [])

  if (loading) return <div className="state"><div className="spinner" />Loading overview…</div>
  if (error) return <div className="state error">{error}</div>
  if (!data) return null

  return (
    <div>
      <SummaryCards cards={data.cards} />

      {data.alerts?.length > 0 && (
        <div style={{ marginBottom: 18 }}>
          {data.alerts.map((a, i) => (
            <div key={i} style={{
              borderLeft: `4px solid ${SEV_COLORS[a.severity] || '#CC7722'}`,
              background: '#fff', padding: '10px 14px', marginBottom: 8,
              boxShadow: '0 1px 2px rgba(0,0,0,.05)', borderRadius: 4,
              border: '1px solid #e5e7eb',
            }}>
              <div style={{ fontWeight: 600, color: '#000', fontSize: 13 }}>{a.title}</div>
              <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>{a.detail}</div>
            </div>
          ))}
        </div>
      )}

      <Charts charts={data.charts} />

      {data.top_risks?.length > 0 && (
        <div className="table-wrap" style={{ marginTop: 6 }}>
          <div style={{ padding: '10px 14px', borderBottom: '1px solid #e5e7eb', fontWeight: 600, color: '#023020', fontSize: 13 }}>
            Top 10 Highest-Risk Customers
          </div>
          <div className="table-scroll">
            <table className="data">
              <thead>
                <tr>
                  {Object.keys(data.top_risks[0]).map(k => <th key={k}>{k}</th>)}
                </tr>
              </thead>
              <tbody>
                {data.top_risks.map((r, i) => (
                  <tr key={i}>
                    {Object.entries(r).map(([k, v]) => (
                      <td key={k} style={k === 'Rating' && (v === 'High' || v === 'Critical')
                        ? { color: '#7a1212', fontWeight: 600 } : undefined}>
                        {fmt(v)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
