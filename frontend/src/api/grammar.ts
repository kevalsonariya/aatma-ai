/**
 * api/grammar.ts — Axios client for POST /api/grammar
 */

import axios from 'axios'

export interface GrammarRequest {
  text: string
}

export interface GrammarResponse {
  original_text: string
  corrected_text: string
  explanation: string
}

const api = axios.create({
  baseURL: '/',
  timeout: 120_000,
  headers: { 'Content-Type': 'application/json' },
})

export async function correctGrammar(payload: GrammarRequest): Promise<GrammarResponse> {
  const { data } = await api.post<GrammarResponse>('/api/grammar', payload)
  return data
}
