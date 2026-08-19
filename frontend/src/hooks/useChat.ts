/**
 * hooks/useChat.ts — Chat state management
 *
 * Manages the conversation history, loading state, and error state.
 * Calls the Aatma AI backend via the Axios client.
 */

import { useState, useCallback } from 'react'
import axios from 'axios'
import { sendChat } from '../api/chat'
import type { ChatMessage } from '../api/chat'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isError?: boolean
}

export interface UseChatReturn {
  messages: Message[]
  isLoading: boolean
  error: string | null
  sendMessage: (text: string) => Promise<void>
  clearMessages: () => void
}

function uid(): string {
  return Math.random().toString(36).slice(2, 10)
}

function toApiHistory(messages: Message[]): ChatMessage[] {
  return messages
    .filter(m => !m.isError)
    .map(m => ({ role: m.role, content: m.content }))
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return

    // Optimistically append user message
    const userMsg: Message = {
      id: uid(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMsg])
    setIsLoading(true)
    setError(null)

    try {
      const history = toApiHistory([...messages, userMsg])
      // Pass all turns except the current one as history
      const historyWithoutLast = history.slice(0, -1)

      const data = await sendChat({
        message: text.trim(),
        history: historyWithoutLast,
        temperature: 0.7,
      })

      const aiMsg: Message = {
        id: uid(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, aiMsg])
    } catch (err: unknown) {
      let userMessage = 'Something went wrong. Please try again.'

      if (axios.isAxiosError(err)) {
        if (!err.response) {
          // Network error — backend unreachable
          userMessage = 'Cannot reach the Aatma AI backend. Make sure it is running on port 8000.'
        } else if (err.response.status === 503) {
          userMessage = 'Local AI service is unavailable. Make sure Ollama is running (`ollama serve`).'
        } else if (err.response.status === 502) {
          userMessage = 'The AI model returned an unexpected error. Please try again.'
        } else {
          userMessage = `Server error (${err.response.status}). Please try again.`
        }
      }

      setError(userMessage)

      // Show error as a system message in the chat
      const errMsg: Message = {
        id: uid(),
        role: 'assistant',
        content: userMessage,
        timestamp: new Date(),
        isError: true,
      }
      setMessages(prev => [...prev, errMsg])
    } finally {
      setIsLoading(false)
    }
  }, [messages, isLoading])

  const clearMessages = useCallback(() => {
    setMessages([])
    setError(null)
  }, [])

  return { messages, isLoading, error, sendMessage, clearMessages }
}
