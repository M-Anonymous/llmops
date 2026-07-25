const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    let message = `请求失败 (${response.status})`
    try {
      const data = (await response.json()) as { detail?: string }
      if (typeof data.detail === 'string') {
        message = data.detail
      }
    } catch {
      // ignore parse error
    }
    throw new ApiError(message, response.status)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}
