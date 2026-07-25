import { useState } from 'react'
import { getGithubAuthorizationUrl } from '../api/auth'
import '../styles/common.css'
import './LoginPage.css'

function GithubIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="github-icon">
      <path
        fill="currentColor"
        d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-1.125-.195-2.805-.63-2.805-2.475 0-1.125.405-2.04 1.065-2.76-.105-.255-.465-1.29.105-2.685 0 0 .87-.27 2.85 1.05A9.78 9.78 0 0 1 12 5.85c.855.005 1.71.12 2.52.345 1.98-1.32 2.85-1.05 2.85-1.05.57 1.395.21 2.43.105 2.685.66.72 1.065 1.635 1.065 2.76 0 1.875-1.695 2.28-3.315 2.475.195.165.465.48.465 1.005 0 .735-.015 1.335-.015 1.515 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12Z"
      />
    </svg>
  )
}

export default function LoginPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleGithubLogin() {
    setLoading(true)
    setError(null)

    try {
      const authorizationUrl = await getGithubAuthorizationUrl()
      window.location.href = authorizationUrl
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败，请稍后重试')
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="page-bg" aria-hidden="true">
        <div className="page-bg-glow page-bg-glow--left" />
        <div className="page-bg-glow page-bg-glow--right" />
        <div className="page-bg-grid" />
      </div>

      <main className="login-card">
        <div className="login-brand">
          <div className="brand-logo">L</div>
          <div>
            <p className="brand-eyebrow">LLM Operations Platform</p>
            <h1 className="brand-title">llmops</h1>
          </div>
        </div>

        <p className="login-desc">
          使用 GitHub 账号登录，管理 Agent、知识库与 API 工具。
        </p>

        {error && (
          <div className="login-error" role="alert">
            {error}
          </div>
        )}

        <button
          type="button"
          className="login-button"
          onClick={handleGithubLogin}
          disabled={loading}
        >
          <GithubIcon />
          {loading ? '正在跳转 GitHub…' : '使用 GitHub 登录'}
        </button>

        <p className="login-hint">
          登录即表示你同意使用 GitHub OAuth 进行身份验证。
        </p>
      </main>
    </div>
  )
}
