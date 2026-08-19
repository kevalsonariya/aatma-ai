/**
 * components/StatusBar.tsx
 * Top status badges: local model active + internet not required.
 */

interface StatusBarProps {
  backendOnline: boolean
}

export function StatusBar({ backendOnline }: StatusBarProps) {
  return (
    <div className="status-bar">
      <span className={`status-badge ${backendOnline ? 'status-ok' : 'status-err'}`}>
        <span className="status-dot" />
        {backendOnline ? 'LOCAL MODEL ACTIVE' : 'BACKEND OFFLINE'}
      </span>
      <span className="status-badge status-ok">
        <span className="status-dot" />
        INTERNET NOT REQUIRED
      </span>
    </div>
  )
}
