export default function Sidebar({ sheets, active, onSelect, meta, rowsPerSheet, hasOverview, user, onLogout }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand"><span className="dot" /> Risk Dashboard</div>
        {meta?.filename && (
          <div className="meta">
            File: {meta.filename}
            {meta.uploaded_at && <><br />Uploaded: {new Date(meta.uploaded_at).toLocaleString()}</>}
          </div>
        )}
      </div>
      <nav className="sidebar-nav">
        {hasOverview && (
          <button className={`nav-item ${active === '__overview__' ? 'active' : ''}`} onClick={() => onSelect('__overview__')}>
            <span>📊 Overview</span>
          </button>
        )}
        {sheets.length === 0 && !hasOverview && (
          <div style={{ padding: '14px 18px', fontSize: 12, color: '#9fb3ad' }}>
            No workbook loaded. Use “Import Excel”.
          </div>
        )}
        {sheets.map((s) => (
          <button key={s} className={`nav-item ${active === s ? 'active' : ''}`} onClick={() => onSelect(s)}>
            <span>{s}</span>
            {rowsPerSheet?.[s] != null && <span className="count">{rowsPerSheet[s]}</span>}
          </button>
        ))}
      </nav>
      <div className="sidebar-footer">
        {user && (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span>{user.username} · <span style={{ color: '#CC7722' }}>{user.role}</span></span>
            {onLogout && <button onClick={onLogout} style={{ background: 'transparent', border: 0, color: '#9fb3ad', fontSize: 11, cursor: 'pointer' }}>Sign out</button>}
          </div>
        )}
        <div>v1.0 · Enterprise</div>
      </div>
    </aside>
  )
}
