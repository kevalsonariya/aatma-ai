/**
 * components/ChatInput.tsx
 * Text input + send button. Disabled while loading.
 * Supports Shift+Enter for newlines, Enter to send.
 */

import { useState, useRef, type KeyboardEvent } from 'react'

interface ChatInputProps {
  onSend: (text: string) => void
  disabled: boolean
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  function handleSend() {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleInput() {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`
  }

  return (
    <div className="chat-input-bar">
      <textarea
        id="chat-input"
        ref={textareaRef}
        className="chat-textarea"
        placeholder="Ask Aatma AI anything… (Enter to send, Shift+Enter for newline)"
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onInput={handleInput}
        disabled={disabled}
        rows={1}
        aria-label="Message input"
      />
      <button
        id="chat-send-btn"
        className={`send-btn ${disabled || !value.trim() ? 'send-btn--disabled' : ''}`}
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        aria-label="Send message"
        title="Send (Enter)"
      >
        {disabled ? (
          <span className="send-spinner" aria-hidden="true" />
        ) : (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        )}
      </button>
    </div>
  )
}
