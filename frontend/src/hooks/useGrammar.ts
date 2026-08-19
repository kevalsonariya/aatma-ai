/**
 * hooks/useGrammar.ts — Grammar correction state management
 */

import { useState, useCallback } from 'react'
import axios from 'axios'
import { correctGrammar } from '../api/grammar'
import type { GrammarResponse } from '../api/grammar'

export interface UseGrammarReturn {
  result: GrammarResponse | null
  isLoading: boolean
  error: string | null
  correct: (text: string) => Promise<void>
  reset: () => void
}

export function useGrammar(): UseGrammarReturn {
  const [result, setResult] = useState<GrammarResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const correct = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return
    setIsLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await correctGrammar({ text: text.trim() })
      setResult(data)
    } catch (err: unknown) {
      let msg = 'Something went wrong. Please try again.'
      if (axios.isAxiosError(err)) {
        if (!err.response) {
          msg = 'Cannot reach the Aatma AI backend. Make sure it is running on port 8000.'
        } else if (err.response.status === 503) {
          msg = 'Local AI service is unavailable. Make sure Ollama is running (`ollama serve`).'
        } else if (err.response.status === 502) {
          msg = 'The AI model returned an unexpected error. Please try again.'
        } else {
          msg = `Server error (${err.response.status}). Please try again.`
        }
      }
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }, [isLoading])

  const reset = useCallback(() => {
    setResult(null)
    setError(null)
  }, [])

  return { result, isLoading, error, correct, reset }
}
