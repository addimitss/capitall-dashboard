import { useRef, useState } from 'react'
import { ExcelAPI } from '../api/client'

export default function UploadButton({ onUploaded, label = 'Import Excel' }) {
  const ref = useRef(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)

  const onChange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setBusy(true); setErr(null)
    try {
      const res = await ExcelAPI.upload(file)
      onUploaded?.(res)
    } catch (ex) {
      setErr(ex?.response?.data?.detail || ex.message || 'Upload failed')
    } finally {
      setBusy(false)
      if (ref.current) ref.current.value = ''
    }
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <button className="btn bronze" disabled={busy} onClick={() => ref.current?.click()}>
        {busy ? 'Uploading…' : label}
      </button>
      <input ref={ref} type="file" accept=".xlsx,.xlsm" className="upload-input" onChange={onChange} />
      {err && <span style={{ color: '#b91c1c', fontSize: 12 }}>{err}</span>}
    </div>
  )
}
