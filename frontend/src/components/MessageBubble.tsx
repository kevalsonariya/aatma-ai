/**
 * components/MessageBubble.tsx
 * Renders a single chat turn — user or assistant.
 */

import type { Message } from '../hooks/useChat'

interface MessageBubbleProps {
  message: Message
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`bubble-row ${isUser ? 'bubble-row--user' : 'bubble-row--ai'}`}>
      {!isUser && (
        <div className="avatar avatar--ai" aria-hidden="true">
          🪷
        </div>
      )}

      <div className={`bubble ${isUser ? 'bubble--user' : 'bubble--ai'} ${message.isError ? 'bubble--error' : ''}`}>
        <p className="bubble-text">{message.content}</p>
        <span className="bubble-time">{formatTime(message.timestamp)}</span>
      </div>

      {isUser && (
        <div className="avatar avatar--user" aria-hidden="true">
          You
        </div>
      )}
    </div>
  )
}
