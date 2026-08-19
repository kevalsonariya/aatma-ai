/**
 * api/chat.ts — Axios client for the Aatma AI backend
 *
 * All requests go through the Vite proxy (/api → http://localhost:8000)
 * so no direct cross-origin request is made from the browser.
 */

import axios from 'axios'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface ChatRequest {
  message: string
  history?: ChatMessage[]
  temperature?: number
  system_prompt?: string
}

export interface ChatResponse {
  response: string
  model: string
  prompt_tokens?: number
  completion_tokens?: number
  done: boolean
}

export interface HealthResponse {
  status: string
}

// ── Axios instance ────────────────────────────────────────────────────────────

const api = axios.create({
  baseURL: '/',          // relative → goes through Vite proxy
  timeout: 120_000,      // 2 min — local inference can be slow
  headers: { 'Content-Type': 'application/json' },
})

// ── API calls ─────────────────────────────────────────────────────────────────

/** Send a message and return the model's reply. */
export async function sendChat(payload: ChatRequest): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>('/api/chat', payload)
  return data
}

/** Check whether the backend is reachable. */
export async function checkHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>('/health')
  return data
}
