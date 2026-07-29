import { apiRequest } from './client'

export interface Agent {
  id: string
  accountId: number
  name: string
  desc: string
  icon: string | null
  systemPrompt: string | null
  modelId: string | null
  libraryIds: string[]
  toolIds: string[]
  middlewareIds: string[]
  createAt: string
  updateAt: string
}

export interface AgentCreateInput {
  name: string
  desc: string
  icon?: string
}

export interface AgentUpdateInput {
  id: string
  name?: string
  desc?: string
  icon?: string
  system_prompt?: string | null
  model_id?: string | null
  library_ids?: string[]
  tool_ids?: string[]
  middleware_ids?: string[]
}

export function getAgentList() {
  return apiRequest<Agent[]>('/agent/list')
}

export function createAgent(data: AgentCreateInput) {
  return apiRequest<{ id: string }>('/agent/create', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateAgent(data: AgentUpdateInput) {
  return apiRequest<Agent>('/agent/update', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function deleteAgent(id: string) {
  return apiRequest<{ status: string }>('/agent/delete', {
    method: 'POST',
    body: JSON.stringify({ id }),
  })
}
