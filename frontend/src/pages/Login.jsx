import { useState } from 'react'
import { AuthAPI } from '../api/client'

export default function Login({ onLogin }) {
  const [u, setU] = useState('admin')
  const [p, setP] = useState('admin123')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setErr(null)
    try {
      const res = await AuthAPI.login(u, p)
      localStorage.setItem('auth_token', res.token)
      localStorage.setItem('auth_user', JSON.stringify({ username: res.username, role: res.role }))
      onLogin?.(res)
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={{
      height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'linear-gradient(135deg, #023020 0%, #000 100%)',
    }}>
      <form onSubmit={submit} style={{
        background: '#fff', borderRadius: 8, padding: 32, width: 360,
        boxShadow: '0 12px 40px rgba(0,0,0,.3)', borderTop: '4px solid #CC7722',
      }}>
        <div style={{ fontSize: 18, fontWeight: 700, color: '#023020', marginBottom: 4 }}>
          CapitALL Risk Dashboard
        </div>
        <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 22 }}>Sign in to continue</div>

        <label style={{ fontSize: 11, color: '#6b7280', textTransform: 'uppercase', letterSpacing: .5 }}>
          Username
        </label>
        <input value={u} onChange={e => setU(e.target.value)} autoFocus
          style={{ width: '100%', padding: '8px 10px', border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13, marginTop: 4, marginBottom: 14 }} />

        <label style={{ fontSize: 11, color: '#6b7280', textTransform: 'uppercase', letterSpacing: .5 }}>
          Password
        </label>
        <input type="password" value={p} onChange={e => setP(e.target.value)}
          style={{ width: '100%', padding: '8px 10px', border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13, marginTop: 4, marginBottom: 18 }} />

        {err && <div style={{ color: '#b91c1c', fontSize: 12, marginBottom: 12 }}>{err}</div>}

        <button type="submit" disabled={busy} className="btn" style={{ width: '100%' }}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>

        <div style={{ marginTop: 18, fontSize: 11, color: '#6b7280', borderTop: '1px solid #f0f0f0', paddingTop: 12 }}>
          Demo accounts: <b>admin/admin123</b>, <b>analyst/analyst123</b>, <b>viewer/viewer123</b>
        </div>
      </form>
    </div>
  )
}
