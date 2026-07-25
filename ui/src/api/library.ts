import { apiRequest } from './client'

export interface Library {
  id: string
  name: string
  desc: string
  icon: string | null
  createAt: string
  updateAt: string
}

export interface LibraryCreateInput {
  name: string
  desc: string
  icon?: string
}

export interface LibraryUpdateInput {
  id: string
  name?: string
  desc?: string
  icon?: string
}

export function getLibraryList() {
  return apiRequest<Library[]>('/library/list')
}

export function createLibrary(data: LibraryCreateInput) {
  return apiRequest<{ id: string }>('/library/create', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateLibrary(data: LibraryUpdateInput) {
  return apiRequest<Library>('/library/update', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function deleteLibrary(id: string) {
  return apiRequest<{ status: string }>('/library/delete', {
    method: 'POST',
    body: JSON.stringify({ id }),
  })
}

export type DocumentStatus = 0 | 1 | 2 | 3 | 4

export type SplitterType = 'default' | 'md'

export interface Document {
  id: string
  libraryId: string
  fileName: string
  fileExt: string
  desc: string
  fileKey: string
  status: DocumentStatus
  createAt: string
  updateAt: string
}

export interface DocumentParseInput {
  id: string
  splitter_type?: SplitterType
  splitter_params?: {
    chunk_size?: number
    chunk_overlap?: number
    [key: string]: unknown
  }
}

export interface DocumentParseResult {
  taskId: string
}

export interface DocumentCreateInput {
  library_id: string
  file_name: string
  file_ext: string
  desc: string
  file_key: string
}

export interface DocumentDownloadResult {
  download_url: string
  cos_key: string
  expire_seconds: number
  fileName: string
}

export function getDocumentList(libraryId: string) {
  return apiRequest<Document[]>(`/library/document/list?library_id=${encodeURIComponent(libraryId)}`)
}

export function addDocument(data: DocumentCreateInput) {
  return apiRequest<{ id: string }>('/library/document/add', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function deleteDocument(id: string) {
  return apiRequest<{ status: string }>('/library/document/delete', {
    method: 'POST',
    body: JSON.stringify({ id }),
  })
}

export function downloadDocument(id: string) {
  return apiRequest<DocumentDownloadResult>('/library/document/download', {
    method: 'POST',
    body: JSON.stringify({ id }),
  })
}

export function parseDocument(data: DocumentParseInput) {
  return apiRequest<DocumentParseResult>('/library/document/parse', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export interface Chunk {
  id: string
  documentId: string
  position: number
  content: string
  hash: string
  enabled: boolean
  createAt: string
  updateAt: string
}

export interface ChunkUpdateInput {
  id: string
  position?: number
  content?: string
  hash?: string
  enabled?: boolean
}

export function getChunkList(documentId: string) {
  return apiRequest<Chunk[]>(
    `/library/document/chunk/list?document_id=${encodeURIComponent(documentId)}`,
  )
}

export function updateChunk(data: ChunkUpdateInput) {
  return apiRequest<Chunk>('/library/document/chunk/update', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function deleteChunk(id: string) {
  return apiRequest<{ status: string }>('/library/document/chunk/delete', {
    method: 'POST',
    body: JSON.stringify({ id }),
  })
}
