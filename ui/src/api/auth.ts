const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

export async function getGithubAuthorizationUrl(): Promise<string> {
  const response = await fetch(`${API_BASE}/auth/authorization_url`, {
    credentials: 'include',
  })

  if (!response.ok) {
    throw new Error(`获取授权链接失败 (${response.status})`)
  }

  const contentType = response.headers.get('content-type') ?? ''

  if (contentType.includes('application/json')) {
    const data: unknown = await response.json()
    if (typeof data === 'string') {
      return data
    }
    throw new Error('授权链接格式异常')
  }

  return response.text()
}
