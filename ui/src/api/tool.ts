import { apiRequest } from './client'

export interface Tool {
  id: string
  name: string
  label: string
  desc: string
  apiConfig: Record<string, unknown>
  enabled: boolean
  createAt: string
  updateAt: string
}

export interface ToolCreateInput {
  name: string
  label: string
  desc: string
  api_config: Record<string, unknown>
  enabled?: boolean
}

export interface ToolUpdateInput {
  id: string
  name?: string
  label?: string
  desc?: string
  api_config?: Record<string, unknown>
  enabled?: boolean
}

export function getToolList() {
  return apiRequest<Tool[]>('/tool/list')
}

export function createTool(data: ToolCreateInput) {
  return apiRequest<{ id: string }>('/tool/create', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateTool(data: ToolUpdateInput) {
  return apiRequest<Tool>('/tool/update', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function deleteTool(id: string) {
  return apiRequest<{ status: string }>('/tool/delete', {
    method: 'POST',
    body: JSON.stringify({ id }),
  })
}

export interface ToolInvokeInput {
  name: string
  arguments?: Record<string, unknown>
}

export interface ToolInvokeResult {
  name: string
  result: unknown
}

export function invokeTool(data: ToolInvokeInput) {
  return apiRequest<ToolInvokeResult>('/tool/invoke', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export interface ToolSchema {
  type: string
  function: {
    name: string
    description: string
    parameters: Record<string, unknown>
  }
}

export function getToolSchema(name: string) {
  return apiRequest<ToolSchema>(`/tool/schema?name=${encodeURIComponent(name)}`)
}
