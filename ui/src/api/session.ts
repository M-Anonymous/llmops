import { ApiError, apiRequest } from './client'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

export interface SessionInfo {
  id: string
  accountId: number | null
  visitorId: string | null
  agentId: string | null
  title: string | null
  createAt: string
  updateAt: string
}

export interface SessionMessage {
  role: string
  content: string
  name?: string
  toolCalls?: unknown
}

export interface HitlActionRequest {
  name: string
  args: Record<string, unknown>
  description: string
}

export interface HitlReviewConfig {
  actionName: string
  allowedDecisions: Array<'approve' | 'reject'>
}

export interface HitlInterrupt {
  actionRequests: HitlActionRequest[]
  reviewConfigs: HitlReviewConfig[]
}

export interface HitlDecision {
  type: 'approve' | 'reject'
  message?: string
}

export interface SessionStreamInput {
  agent_id: string
  question: string
  session_id?: string
  visitor_id?: string
  title?: string
}

export type SessionStreamEvent =
  | { type: 'session'; sessionId: string; agentId: string }
  | { type: 'delta'; content: string }
  | ({
      type: 'interrupt'
      sessionId: string
      agentId: string
      actionRequests: HitlActionRequest[]
      reviewConfigs: HitlReviewConfig[]
    })
  | { type: 'done'; sessionId: string; agentId: string }
  | { type: 'error'; detail: string }

export function getSessionList(params: {
  agent_id?: string
  visitor_id?: string
}) {
  const query = new URLSearchParams()
  if (params.agent_id) {
    query.set('agent_id', params.agent_id)
  }
  if (params.visitor_id) {
    query.set('visitor_id', params.visitor_id)
  }
  const suffix = query.toString() ? `?${query.toString()}` : ''
  return apiRequest<SessionInfo[]>(`/session/list${suffix}`)
}

export function getSessionMessages(params: {
  session_id: string
  visitor_id?: string
}) {
  const query = new URLSearchParams({ session_id: params.session_id })
  if (params.visitor_id) {
    query.set('visitor_id', params.visitor_id)
  }
  return apiRequest<{
    session: SessionInfo
    messages: SessionMessage[]
    interrupt: HitlInterrupt | null
  }>(`/session/messages?${query.toString()}`)
}

async function* readSseStream(
  response: Response,
): AsyncGenerator<SessionStreamEvent, void, unknown> {
  if (!response.ok) {
    let message = `请求失败 (${response.status})`
    try {
      const payload = (await response.json()) as { detail?: string }
      if (typeof payload.detail === 'string') {
        message = payload.detail
      }
    } catch {
      // ignore
    }
    throw new ApiError(message, response.status)
  }

  if (!response.body) {
    throw new ApiError('流式响应为空', 500)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) {
      break
    }

    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() ?? ''

    for (const chunk of chunks) {
      const lines = chunk.split('\n')
      for (const line of lines) {
        if (!line.startsWith('data: ')) {
          continue
        }
        const raw = line.slice(6).trim()
        if (!raw) {
          continue
        }
        try {
          yield JSON.parse(raw) as SessionStreamEvent
        } catch {
          // ignore malformed event
        }
      }
    }
  }
}

export async function* sessionStream(
  data: SessionStreamInput,
): AsyncGenerator<SessionStreamEvent, void, unknown> {
  const response = await fetch(`${API_BASE}/session/stream`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  yield* readSseStream(response)
}

export async function* sessionResume(data: {
  session_id: string
  agent_id?: string
  visitor_id?: string
  decisions: HitlDecision[]
}): AsyncGenerator<SessionStreamEvent, void, unknown> {
  const response = await fetch(`${API_BASE}/session/resume`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  yield* readSseStream(response)
}

/** @deprecated 调试页仍可使用；首页请用 sessionStream */
export async function* debugChatStream(data: {
  agent_id: string
  question: string
  session_id?: string
}) {
  const response = await fetch(`${API_BASE}/agent/debug/stream`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  yield* readSseStream(response)
}

export function debugChat(data: {
  agent_id: string
  question: string
  session_id?: string
}) {
  return apiRequest<{
    sessionId: string
    agentId: string
    answer: string
    interrupt?: HitlInterrupt | null
  }>('/agent/debug/chat', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
