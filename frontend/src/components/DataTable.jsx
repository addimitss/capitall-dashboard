import { useEffect, useMemo, useState } from 'react'
import { ExcelAPI } from '../api/client'

function fmtCell(v) {
  if (v == null) return ''
  if (typeof v === 'number') return v.toLocaleString(undefined, { maximumFractionDigits: 4 })
  return String(v)
}

export default function DataTable({ sheet, columns }) {
  const [search, setSearch] = useState('')
  const [debounced, setDebounced] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [sort, setSort] = useState({ by: null, dir: 'asc' })
  const [filters, setFilters] = useState({})
  const [data, setData] = useState({ rows: [], total: 0, columns: [] })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // debounce search
  useEffect(() => {
    const t = setTimeout(() => setDebounced(search), 300)
    return () => clearTimeout(t)
  }, [search])

  // reset paging on sheet change
  useEffect(() => { setPage(1); setSort({ by: null, dir: 'asc' }); setFilters({}); setSearch(''); setDebounced('') }, [sheet])

  // fetch data
  useEffect(() => {
    let cancel = false
    setLoading(true); setError(null)
    ExcelAPI.data(sheet, {
      page, page_size: pageSize, search: debounced || null,
      sort_by: sort.by, sort_dir: sort.dir, filters,
    }).then(res => { if (!cancel) setData(res) })
      .catch(e => { if (!cancel) setError(e?.response?.data?.detail || e.message) })
      .finally(() => { if (!cancel) setLoading(false) })
    return () => { cancel = true }
  }, [sheet, page, pageSize, debounced, sort, filters])

  const totalPages = Math.max(1, Math.ceil(data.total / pageSize))
  const cols = data.columns?.length ? data.columns : columns

  const onSort = (col) => {
    setSort(prev => prev.by === col ? { by: col, dir: prev.dir === 'asc' ? 'desc' : 'asc' } : { by: col, dir: 'asc' })
  }

  // Categorical filter dropdowns (string columns with unique values)
  const filterCols = useMemo(
    () => (cols || []).filter(c => c.kind === 'string').slice(0, 3),
    [cols]
  )

  // Pagination window
  const pageButtons = useMemo(() => {
    const list = []
    const start = Math.max(1, page - 2)
    const end = Math.min(totalPages, start + 4)
    for (let i = start; i <= end; i++) list.push(i)
    return list
  }, [page, totalPages])

  return (
    <div>
      <div className="filters">
        <span className="lbl">Search</span>
        <input value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} placeholder="Search any column…" />
        <span className="lbl">Page Size</span>
        <select value={pageSize} onChange={e => { setPageSize(+e.target.value); setPage(1) }}>
          {[25, 50, 100, 200].map(n => <option key={n} value={n}>{n}</option>)}
        </select>
        {filterCols.map(c => (
          <FilterDropdown key={c.name} sheet={sheet} column={c.name}
            value={filters[c.name]}
            onChange={v => { setFilters(f => ({ ...f, [c.name]: v || undefined })); setPage(1) }} />
        ))}
        {(Object.keys(filters).length > 0 || search) && (
          <button className="btn outline" onClick={() => { setFilters({}); setSearch('') }}>Reset</button>
        )}
      </div>

      {error && <div className="state error">{error}</div>}

      <div className="table-wrap">
        <div className="table-scroll">
          {loading ? (
            <div className="state"><div className="spinner" />Loading…</div>
          ) : data.rows.length === 0 ? (
            <div className="state"><div className="title">No rows match</div>Adjust filters or search.</div>
          ) : (
            <table className="data">
              <thead>
                <tr>
                  {cols.map(c => (
                    <th key={c.name} onClick={() => onSort(c.name)} title="Click to sort">
                      {c.name}
                      {sort.by === c.name && <span className="arrow">{sort.dir === 'asc' ? '▲' : '▼'}</span>}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.rows.map((r, i) => (
                  <tr key={i}>
                    {cols.map(c => <td key={c.name}>{fmtCell(r[c.name])}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <div className="pagination">
          <div className="info">
            {data.total > 0
              ? <>Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, data.total)} of {data.total.toLocaleString()}</>
              : 'No results'}
          </div>
          <div className="pager">
            <button disabled={page === 1} onClick={() => setPage(1)}>«</button>
            <button disabled={page === 1} onClick={() => setPage(p => p - 1)}>‹</button>
            {pageButtons.map(p => (
              <button key={p} className={p === page ? 'active' : ''} onClick={() => setPage(p)}>{p}</button>
            ))}
            <button disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>›</button>
            <button disabled={page === totalPages} onClick={() => setPage(totalPages)}>»</button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Lightweight categorical filter — fetches a small page to derive distinct values
function FilterDropdown({ sheet, column, value, onChange }) {
  const [opts, setOpts] = useState([])
  useEffect(() => {
    let cancel = false
    ExcelAPI.data(sheet, { page: 1, page_size: 500, sort_by: column, sort_dir: 'asc' })
      .then(res => {
        if (cancel) return
        const seen = new Set()
        for (const r of res.rows) {
          const v = r[column]
          if (v != null && v !== '') seen.add(String(v))
          if (seen.size > 50) break
        }
        setOpts(Array.from(seen).sort())
      })
      .catch(() => setOpts([]))
    return () => { cancel = true }
  }, [sheet, column])

  return (
    <>
      <span className="lbl">{column}</span>
      <select value={value || ''} onChange={e => onChange(e.target.value)}>
        <option value="">All</option>
        {opts.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </>
  )
}
