import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import UploadButton from './components/UploadButton'
import Chatbot from './components/Chatbot'
import EmptyState from './components/EmptyState'
import SheetView from './pages/SheetView'
import Overview from './pages/Overview'
import Login from './pages/Login'
import { AuthAPI } from './api/client'
import { useWorkbook } from './hooks/useSheets'

const OVERVIEW = '__overview__'

export default function App() {
  // Auth state
  const [authConfig, setAuthConfig] = useState(null)
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('auth_user') || 'null') } catch { return null }
  })

  // Workbook state
  const { meta, loading, error, refresh } = useWorkbook()
  const [active, setActive] = useState(null)
  const [rowsPerSheet, setRowsPerSheet] = useState({})

  // Probe whether the backend has auth enabled
  useEffect(() => {
    AuthAPI.config()
      .then(c => setAuthConfig(c))
      .catch(() => setAuthConfig({ auth_enabled: false }))
  }, [])

  // React to forced logout from API client (401)
  useEffect(() => {
    const handler = () => { setUser(null); localStorage.removeItem('auth_token'); localStorage.removeItem('auth_user') }
    window.addEventListener('auth:logout', handler)
    return () => window.removeEventListener('auth:logout', handler)
  }, [])

  // Default active tab
  useEffect(() => {
    if (meta.sheets?.length && !active) setActive(OVERVIEW)
    if (!meta.sheets?.length) setActive(null)
  }, [meta.sheets, active])

  const onUploaded = (res) => {
    setRowsPerSheet(res.rows_per_sheet || {})
    refresh()
    setActive(OVERVIEW)
    if (res.warnings?.length) {
      // surface warnings non-blockingly
      console.warn('Schema warnings:', res.warnings)
    }
  }

  const onLogin = (res) => {
    setUser({ username: res.username, role: res.role })
    refresh()
  }

  const onLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
    setUser(null)
  }

  const hasData = !!meta.sheets?.length
  const showLogin = authConfig?.auth_enabled && !user

  if (authConfig === null) {
    return <div className="state"><div className="spinner" />Initializing…</div>
  }

  if (showLogin) return <Login onLogin={onLogin} />

  const headerTitle = active === OVERVIEW ? 'Overview' : (active || 'Dashboard')
  const canUpload = !user || user.role !== 'viewer'

  return (
    <div className="app">
      <Sidebar
        sheets={meta.sheets || []}
        active={active}
        onSelect={setActive}
        meta={meta}
        rowsPerSheet={rowsPerSheet}
        hasOverview={hasData}
        user={user}
        onLogout={authConfig?.auth_enabled ? onLogout : null}
      />
      <div className="main">
        <div className="topbar">
          <h1>{headerTitle}</h1>
          <div className="actions">
            {meta.uploaded_at && <span className="upload-meta">Last upload: {new Date(meta.uploaded_at).toLocaleString()}</span>}
            {canUpload && <UploadButton onUploaded={onUploaded} label={hasData ? 'Re-import Excel' : 'Import Excel'} />}
          </div>
        </div>
        <div className="content">
          {loading && <div className="state"><div className="spinner" />Loading…</div>}
          {error && <div className="state error">{error}</div>}
          {!loading && !error && !hasData && (
            <EmptyState
              title="No workbook loaded"
              message={canUpload
                ? "Upload an Excel file in the supported format to populate the dashboard."
                : "Ask an admin or analyst to upload a workbook."}
            >
              {canUpload && <UploadButton onUploaded={onUploaded} />}
            </EmptyState>
          )}
          {!loading && !error && hasData && active === OVERVIEW && <Overview key="overview" />}
          {!loading && !error && hasData && active && active !== OVERVIEW && <SheetView key={active} sheet={active} />}
        </div>
      </div>
      <Chatbot sheet={active === OVERVIEW ? null : active} hasData={hasData} />
    </div>
  )
}
