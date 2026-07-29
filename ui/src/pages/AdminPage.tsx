import { Link, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { getAuthMe } from '../api/auth'
import '../styles/common.css'
import './HomePage.css'

const modules = [
  {
    title: 'Agent 管理',
    desc: '创建智能助手，配置提示词、知识库与可用工具。',
    tag: 'Agent',
    href: '/agent',
  },
  {
    title: '模型管理',
    desc: '配置大模型名称、显示名与 API Key，供 Agent 调用。',
    tag: 'Model',
    href: '/model',
  },
  {
    title: '中间件管理',
    desc: '配置摘要压缩与人工审批中间件，供 Agent 挂载使用。',
    tag: 'Middleware',
    href: '/middleware',
  },
  {
    title: '知识库',
    desc: '上传文档、切分入库，构建专属知识检索能力。',
    tag: 'Library',
    href: '/library',
  },
  {
    title: 'API 工具',
    desc: '配置外部 HTTP 接口，动态注册为 Agent 可用工具。',
    tag: 'Tool',
    href: '/tool',
  },
]

export default function AdminPage() {
  const [ready, setReady] = useState(false)
  const [authenticated, setAuthenticated] = useState(false)

  useEffect(() => {
    void (async () => {
      const me = await getAuthMe()
      setAuthenticated(Boolean(me.authenticated))
      setReady(true)
    })()
  }, [])

  if (!ready) {
    return (
      <div className="home-page">
        <div className="home-main">加载中…</div>
      </div>
    )
  }

  if (!authenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <div className="home-page">
      <div className="page-bg" aria-hidden="true">
        <div className="page-bg-glow page-bg-glow--left" />
        <div className="page-bg-glow page-bg-glow--right" />
        <div className="page-bg-grid" />
      </div>

      <header className="home-header" style={{ maxWidth: 1080 }}>
        <div className="home-brand">
          <div className="brand-logo">L</div>
          <div>
            <p className="brand-eyebrow">Admin Console</p>
            <h1 className="brand-title">管理端</h1>
          </div>
        </div>
        <div className="home-header-actions">
          <Link to="/" className="home-login-link">
            返回对话
          </Link>
        </div>
      </header>

      <main className="home-main">
        <section className="home-hero">
          <p className="home-badge">已登录</p>
          <h2 className="home-heading">平台管理</h2>
          <p className="home-subtitle">配置 Agent、模型、知识库与工具，配置完成后可回到首页进行对话。</p>
        </section>

        <section className="home-grid">
          {modules.map((item) => (
            <article key={item.tag} className="home-card">
              <span className="home-card-tag">{item.tag}</span>
              <h3 className="home-card-title">{item.title}</h3>
              <p className="home-card-desc">{item.desc}</p>
              <Link to={item.href} className="home-card-link">
                进入管理
              </Link>
            </article>
          ))}
        </section>
      </main>
    </div>
  )
}
