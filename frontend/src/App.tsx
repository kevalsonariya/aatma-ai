/**
 * App.tsx — Aatma AI root component
 *
 * Manages the active mode (chat | grammar) and renders the appropriate
 * feature screen. Chat functionality is fully preserved.
 */

import { useEffect, useRef, useState } from 'react'
import { useChat } from './hooks/useChat'
import { checkHealth } from './api/chat'
import { StatusBar } from './components/StatusBar'
import { EmptyState } from './components/EmptyState'
import { MessageBubble } from './components/MessageBubble'
import { TypingIndicator } from './components/TypingIndicator'
import { ChatInput } from './components/ChatInput'
import { SystemInfo } from './components/SystemInfo'
import { GrammarCorrector } from './components/GrammarCorrector'
import './index.css'

type Mode = 'chat' | 'grammar'

export default function App() {
  const [mode, setMode] = useState<Mode>('chat')
  const { messages, isLoading, sendMessage, clearMessages } = useChat()
  const [backendOnline, setBackendOnline] = useState(true)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Poll backend health every 15 s
  useEffect(() => {
    async function ping() {
      try {
        await checkHealth()
        setBackendOnline(true)
      } catch {
        setBackendOnline(false)
      }
    }
    ping()
    const id = setInterval(ping, 15_000)
    return () => clearInterval(id)
  }, [])

  // Auto-scroll to latest message (chat mode only)
  useEffect(() => {
    if (mode === 'chat') {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isLoading, mode])

  return (
    <div className="layout">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-lotus" aria-hidden="true">🪷</span>
          <div>
            <span className="brand-name">Aatma AI</span>
            <span className="brand-tagline">Intelligence that lives within.</span>
          </div>
        </div>

        {/* Mode navigation */}
        <nav className="sidebar-nav" aria-label="Features">
          <button
            id="nav-chat-btn"
            className={`nav-btn ${mode === 'chat' ? 'nav-btn--active' : ''}`}
            onClick={() => setMode('chat')}
            aria-current={mode === 'chat' ? 'page' : undefined}
          >
            <span className="nav-btn-icon">💬</span>
            Chat
          </button>
          <button
            id="nav-grammar-btn"
            className={`nav-btn ${mode === 'grammar' ? 'nav-btn--active' : ''}`}
            onClick={() => setMode('grammar')}
            aria-current={mode === 'grammar' ? 'page' : undefined}
          >
            <span className="nav-btn-icon">✏️</span>
            Grammar Correction
          </button>
        </nav>

        {/* Chat-specific: New Chat button */}
        {mode === 'chat' && (
          <div className="sidebar-action">
            <button
              className="new-chat-btn"
              onClick={clearMessages}
              title="Start a new conversation"
              id="new-chat-btn"
            >
              + New Chat
            </button>
          </div>
        )}

        <div className="sidebar-footer">
          <SystemInfo />
        </div>
      </aside>

      {/* ── Main panel ── */}
      <div className="main-panel">
        {/* Header */}
        <header className="top-bar">
          <div className="top-bar-left">
            <span className="top-bar-logo" aria-hidden="true">🪷</span>
            <h1 className="top-bar-title">
              Aatma AI
              <span className="top-bar-mode">
                {mode === 'chat' ? '· Chat' : '· Grammar Correction'}
              </span>
            </h1>
          </div>
          <StatusBar backendOnline={backendOnline} />
        </header>

        {/* ── Chat mode ── */}
        {mode === 'chat' && (
          <>
            <main className="chat-area" aria-live="polite" aria-label="Conversation">
              {messages.length === 0 && !isLoading ? (
                <EmptyState />
              ) : (
                <div className="messages-list">
                  {messages.map(msg => (
                    <MessageBubble key={msg.id} message={msg} />
                  ))}
                  {isLoading && <TypingIndicator />}
                  <div ref={bottomRef} />
                </div>
              )}
            </main>

            <footer className="input-area">
              <ChatInput onSend={sendMessage} disabled={isLoading} />
              <p className="input-disclaimer">
                Inference runs locally via Ollama · Qwen3 8B · No data leaves your device
              </p>
            </footer>
          </>
        )}

        {/* ── Grammar mode ── */}
        {mode === 'grammar' && (
          <main className="grammar-area" aria-label="Grammar Correction">
            <GrammarCorrector />
          </main>
        )}
      </div>
    </div>
  )
}
