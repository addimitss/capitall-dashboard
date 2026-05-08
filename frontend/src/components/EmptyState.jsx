export default function EmptyState({ title, message, children }) {
  return (
    <div className="state">
      <div className="title">{title}</div>
      {message && <div>{message}</div>}
      {children && <div style={{ marginTop: 14 }}>{children}</div>}
    </div>
  )
}
