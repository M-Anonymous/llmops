import { apiRequest } from './client'

export interface Model {
  id: string
  accountId: number
  name: string
  label: string
  desc: string
  icon: string | null
  apiKey: string
  baseUrl: string
  createAt: string
  updateAt: string
}

export interface ModelCreateInput {
  name: string
  label: string
  desc: string
  api_key: string
  base_url: string
  icon?: string
}

export interface ModelUpdateInput {
  id: string
  name?: string
  label?: string
  desc?: string
  api_key?: string
  base_url?: string
  icon?: string
}

export function getModelList() {
  return apiRequest<Model[]>('/model/list')
}

export function createModel(data: ModelCreateInput) {
  return apiRequest<{ id: string }>('/model/create', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateModel(data: ModelUpdateInput) {
  return apiRequest<Model>('/model/update', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function deleteModel(id: string) {
  return apiRequest<{ status: string }>('/model/delete', {
    method: 'POST',
    body: JSON.stringify({ id }),
  })
}
