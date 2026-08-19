/**
 * components/SystemInfo.tsx
 * Bottom-left model/inference info panel.
 */

export function SystemInfo() {
  return (
    <div className="system-info" aria-label="System information">
      <div className="sys-row">
        <span className="sys-label">Model</span>
        <span className="sys-value">Qwen3 4B</span>
      </div>
      <div className="sys-row">
        <span className="sys-label">Inference</span>
        <span className="sys-value">Local</span>
      </div>
      <div className="sys-row">
        <span className="sys-label">Internet</span>
        <span className="sys-value sys-value--ok">Not Required</span>
      </div>
    </div>
  )
}
