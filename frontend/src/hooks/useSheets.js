import { useEffect, useState, useCallback } from 'react'
import { ExcelAPI } from '../api/client'

export function useWorkbook() {
  const [meta, setMeta] = useState({ filename: null, uploaded_at: null, sheets: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true); setError(null)
    try { setMeta(await ExcelAPI.workbook()) }
    catch (e) { setError(e?.response?.data?.detail || e.message) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  return { meta, loading, error, refresh, setMeta }
}
