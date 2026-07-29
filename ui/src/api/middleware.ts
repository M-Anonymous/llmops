import { apiRequest } from './client'

export type MiddlewareType = 0 | 1

export interface Middleware {
  id: string
  accountId: number
  label: string
  type: MiddlewareType
  config: Record<string, unknown>
  createAt: string
  updateAt: string
}

export interface MiddlewareCreateInput {
  label: string
  type: MiddlewareType
  config: Record<string, unknown>
}

export interface MiddlewareUpdateInput {
  id: string
  label?: string
  type?: MiddlewareType
  config?: Record<string, unknown>
}

export function getMiddlewareList() {
  return apiRequest<Middleware[]>('/middleware/list')
}

export function createMiddleware(data: MiddlewareCreateInput) {
  return apiRequest<{ id: string }>('/middleware/create', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateMiddleware(data: MiddlewareUpdateInput) {
  return apiRequest<Middleware>('/middleware/update', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function deleteMiddleware(id: string) {
  return apiRequest<{ status: string }>('/middleware/delete', {
    method: 'POST',
    body: JSON.stringify({ id }),
  })
}
