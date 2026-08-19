/**
 * components/GrammarCorrector.tsx
 * Grammar Correction feature screen.
 *
 * - Large textarea for input
 * - "Correct Grammar" button with loading spinner
 * - Results: original, corrected, explanation + copy button
 */

import { useState, useRef } from 'react'
import { useGrammar } from '../hooks/useGrammar'

export function GrammarCorrector() {
  const [inputText, setInputText] = useState('')
  const [copied, setCopied] = useState(false)
  const { result, isLoading, error, correct, reset } = useGrammar()
  const inputRef = useRef<HTMLTextAreaElement>(null)

  function handleSubmit() {
    if (!inputText.trim() || isLoading) return
    correct(inputText)
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      handleSubmit()
    }
  }

  function handleCopy() {
    if (!result) return
    navigator.clipboard.writeText(result.corrected_text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  function handleReset() {
    setInputText('')
    reset()
    inputRef.current?.focus()
  }

  return (
    <div className="grammar-page">
      {/* Input section */}
      <section className="grammar-section">
        <label className="grammar-label" htmlFor="grammar-input">
          Input Text
        </label>
        <textarea
          id="grammar-input"
          ref={inputRef}
          className="grammar-textarea"
          placeholder="Enter text to correct..."
          value={inputText}
          onChange={e => {
            setInputText(e.target.value)
            if (result || error) reset()
          }}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={7}
          aria-label="Text to correct"
        />
        <div className="grammar-actions">
          <span className="grammar-hint">Ctrl + Enter to correct</span>
          <div className="grammar-btn-row">
            {(result || error) && (
              <button
                className="grammar-btn grammar-btn--ghost"
                onClick={handleReset}
                disabled={isLoading}
                id="grammar-reset-btn"
              >
                Clear
              </button>
            )}
            <button
              id="grammar-submit-btn"
              className={`grammar-btn grammar-btn--primary ${isLoading || !inputText.trim() ? 'grammar-btn--disabled' : ''}`}
              onClick={handleSubmit}
              disabled={isLoading || !inputText.trim()}
            >
              {isLoading ? (
                <>
                  <span className="grammar-spinner" aria-hidden="true" />
                  Correcting…
                </>
              ) : (
                '✏️ Correct Grammar'
              )}
            </button>
          </div>
        </div>
      </section>

      {/* Error */}
      {error && (
        <div className="grammar-error" role="alert">
          <span className="grammar-error-icon">⚠️</span>
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="grammar-results">
          {/* Corrected text */}
          <section className="grammar-section">
            <div className="grammar-result-header">
              <label className="grammar-label">Corrected Text</label>
              <button
                id="grammar-copy-btn"
                className={`copy-btn ${copied ? 'copy-btn--done' : ''}`}
                onClick={handleCopy}
                title="Copy corrected text"
              >
                {copied ? '✓ Copied!' : '📋 Copy'}
              </button>
            </div>
            <div className="grammar-output grammar-output--corrected">
              {result.corrected_text}
            </div>
          </section>

          {/* Original */}
          <section className="grammar-section">
            <label className="grammar-label grammar-label--muted">Original Text</label>
            <div className="grammar-output grammar-output--original">
              {result.original_text}
            </div>
          </section>

          {/* Explanation */}
          {result.explanation && (
            <section className="grammar-section">
              <label className="grammar-label">Explanation</label>
              <div className="grammar-explanation">
                <span className="grammar-explanation-icon" aria-hidden="true">💡</span>
                <p>{result.explanation}</p>
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  )
}
