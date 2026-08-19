/**
 * components/TypingIndicator.tsx
 * Animated "AI is thinking" indicator shown while inference runs.
 */

export function TypingIndicator() {
  return (
    <div className="bubble-row bubble-row--ai">
      <div className="avatar avatar--ai" aria-hidden="true">🪷</div>
      <div className="bubble bubble--ai bubble--typing" aria-label="Aatma AI is thinking">
        <span className="dot" />
        <span className="dot" />
        <span className="dot" />
      </div>
    </div>
  )
}
