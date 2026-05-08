import { useEffect, useState } from 'react'
import { ExcelAPI } from '../api/client'
import SummaryCards from '../components/SummaryCards'
import Charts from '../components/Charts'
import DataTable from '../components/DataTable'

export default function SheetView({ sheet }) {
  const [summary, setSummary] = useState(null)
  const [meta, setMeta] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancel = false
    setLoading(true); setError(null); setSummary(null); setMeta(null)
    Promise.all([ExcelAPI.summary(sheet), ExcelAPI.meta(sheet)])
      .then(([s, m]) => { if (!cancel) { setSummary(s); setMeta(m) } })
      .catch(e => { if (!cancel) setError(e?.response?.data?.detail || e.message) })
      .finally(() => { if (!cancel) setLoading(false) })
    return () => { cancel = true }
  }, [sheet])

  if (loading) return <div className="state"><div className="spinner" />Loading sheet…</div>
  if (error) return <div className="state error">{error}</div>
  if (!summary || !meta) return null

  return (
    <div>
      <SummaryCards cards={summary.cards} />
      <Charts charts={summary.charts} />
      <DataTable sheet={sheet} columns={meta.columns} />
    </div>
  )
}
