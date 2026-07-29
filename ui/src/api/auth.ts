import { apiRequest } from './client'

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

export interface AuthMe {
  id: number | null
  authenticated: boolean
  nickname: string | null
  avatar: string | null
}

export async function getAuthMe(): Promise<AuthMe> {
  try {
    return await apiRequest<AuthMe>('/auth/me')
  } catch {
    // 代理打错服务 / 网络异常 / 旧接口 401 等，一律按未登录，避免首页整页报错
    return {
      id: null,
      authenticated: false,
      nickname: null,
      avatar: null,
    }
  }
}

export async function logout(): Promise<void> {
  await apiRequest<{ status: string }>('/auth/logout', {
    method: 'POST',
  })
}
