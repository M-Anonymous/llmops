import { apiRequest } from './client'

/** 当前仅支持 streamable_http */
export type McpTransport = 2

export interface McpServer {
  id: string
  accountId: number
  name: string
  label: string
  desc: string
  transport: McpTransport
  config: Record<string, unknown>
  enabled: boolean
  createAt: string
  updateAt: string
}

export interface McpServerCreateInput {
  name: string
  label: string
  desc?: string
  transport: McpTransport
  config: Record<string, unknown>
  enabled?: boolean
}

export interface McpServerUpdateInput {
  id: string
  name?: string
  label?: string
  desc?: string
  transport?: McpTransport
  config?: Record<string, unknown>
  enabled?: boolean
}

export function getMcpServerList() {
  return apiRequest<McpServer[]>('/mcp/list')
}

export function createMcpServer(data: McpServerCreateInput) {
  return apiRequest<{ id: string }>('/mcp/create', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateMcpServer(data: McpServerUpdateInput) {
  return apiRequest<McpServer>('/mcp/update', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function deleteMcpServer(id: string) {
  return apiRequest<{ status: string }>('/mcp/delete', {
    method: 'POST',
    body: JSON.stringify({ id }),
  })
}

export interface McpToolInfo {
  name: string
  fullName: string
  description: string
}

export function getMcpServerTools(serverId: string) {
  return apiRequest<McpToolInfo[]>(`/mcp/tools?server_id=${encodeURIComponent(serverId)}`)
}

export interface McpTestResult {
  success: boolean
}

export function testMcpServerConnection(data: {
  name: string
  transport: McpTransport
  config: Record<string, unknown>
}) {
  return apiRequest<McpTestResult>('/mcp/test', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function listMcpToolsFromConfig(data: {
  name: string
  transport: McpTransport
  config: Record<string, unknown>
}) {
  return apiRequest<McpToolInfo[]>('/mcp/tools', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
