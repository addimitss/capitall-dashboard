import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { ChatAPI } from '../api/client'

export default function Chatbot({ sheet, hasData }) {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const bodyRef = useRef(null)

  useEffect(() => {
    if (open && bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight
  }, [messages, open])

  const send = async () => {
    const text = input.trim()
    if (!text || busy) return
    if (!hasData) {
      setMessages(m => [...m, { role: 'system', content: 'Upload a workbook first to enable analysis.' }])
      return
    }
    const next = [...messages, { role: 'user', content: text }]
    setMessages(next); setInput(''); setBusy(true)
    try {
      const history = next.slice(-8).map(m => ({ role: m.role, content: m.content }))
      const res = await ChatAPI.send(text, sheet, history)
      setMessages(m => [...m, { role: 'assistant', content: res.answer }])
    } catch (e) {
      setMessages(m => [...m, { role: 'system', content: e?.response?.data?.detail || e.message || 'Chat failed.' }])
    } finally {
      setBusy(false)
    }
  }

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <>
      <button className="chat-fab" title="Ask AI" onClick={() => setOpen(o => !o)}>{open ? '×' : '✦'}</button>
      {open && (
        <div className="chat-drawer">
          <div className="chat-header">
            <h3>AI Insights {sheet && <span className="chat-context-pill">{sheet}</span>}</h3>
            <button onClick={() => setOpen(false)}>×</button>
          </div>
          <div className="chat-body" ref={bodyRef}>
            {messages.length === 0 && (
              <div className="msg system">
                Try: “Summarise this sheet”, “Which customers are highest risk?”,
                “Explain the mismatch between Risk Rating Summary and Aggregation Check”.
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`msg ${m.role}`}>
                {m.role === 'assistant' ? (
                  <ReactMarkdown>{m.content}</ReactMarkdown>
                ) : (
                  m.content
                )}
              </div>
            ))}
            {busy && <div className="msg assistant">Thinking…</div>}
          </div>
          <div className="chat-input">
            <textarea
              placeholder="Ask about the data…"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={onKey}
            />
            <button className="btn" disabled={busy || !input.trim()} onClick={send}>Send</button>
          </div>
        </div>
      )}
    </>
  )
}
