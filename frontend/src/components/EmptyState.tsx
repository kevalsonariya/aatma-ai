/**
 * components/EmptyState.tsx
 * Shown before the first message is sent.
 */

export function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-lotus" aria-hidden="true">🪷</div>
      <h2 className="empty-title">Welcome to Aatma AI</h2>
      <p className="empty-subtitle">
        Ask anything. Your conversation stays on your device.
      </p>
      <div className="empty-hints">
        <span className="hint-chip">Summarise a topic</span>
        <span className="hint-chip">Explain a concept</span>
        <span className="hint-chip">Write or debug code</span>
      </div>
    </div>
  )
}
