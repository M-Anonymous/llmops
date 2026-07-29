import { useEffect, useState } from 'react'
import { Link, NavLink, Navigate, Outlet } from 'react-router-dom'
import { getAuthMe } from '../api/auth'
import '../styles/common.css'
import './AdminLayout.css'

export const adminNavItems = [
  {
    key: 'agent',
    path: '/admin/agent',
    label: 'Agent 管理',
    desc: '智能助手与配置',
    tag: 'Agent',
  },
  {
    key: 'model',
    path: '/admin/model',
    label: '模型管理',
    desc: '大模型与 API Key',
    tag: 'Model',
  },
  {
    key: 'middleware',
    path: '/admin/middleware',
    label: '中间件管理',
    desc: '摘要压缩与人工审批',
    tag: 'Middleware',
  },
  {
    key: 'mcp',
    path: '/admin/mcp',
    label: 'MCP Server',
    desc: '外部 MCP 工具接入',
    tag: 'MCP',
  },
  {
    key: 'library',
    path: '/admin/library',
    label: '知识库',
    desc: '文档切分与检索',
    tag: 'Library',
  },
  {
    key: 'tool',
    path: '/admin/tool',
    label: 'API 工具',
    desc: 'HTTP 接口注册',
    tag: 'Tool',
  },
] as const

export default function AdminLayout() {
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
      <div className="admin-layout">
        <div className="admin-content admin-content--loading">加载中…</div>
      </div>
    )
  }

  if (!authenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <div className="admin-layout">
      <div className="page-bg" aria-hidden="true">
        <div className="page-bg-glow page-bg-glow--left" />
        <div className="page-bg-glow page-bg-glow--right" />
        <div className="page-bg-grid" />
      </div>

      <aside className="admin-sidebar">
        <div className="admin-sidebar-brand">
          <div className="brand-logo">L</div>
          <div>
            <p className="brand-eyebrow">Admin Console</p>
            <h1 className="admin-sidebar-title">管理端</h1>
          </div>
        </div>

        <nav className="admin-nav" aria-label="管理功能">
          {adminNavItems.map((item) => (
            <NavLink
              key={item.key}
              to={item.path}
              className={({ isActive }) =>
                `admin-nav-item${isActive ? ' is-active' : ''}`
              }
            >
              <span className="admin-nav-tag">{item.tag}</span>
              <span className="admin-nav-label">{item.label}</span>
              <span className="admin-nav-desc">{item.desc}</span>
            </NavLink>
          ))}
        </nav>

        <div className="admin-sidebar-footer">
          <Link to="/" className="admin-back-link">
            返回对话
          </Link>
        </div>
      </aside>

      <div className="admin-main">
        <Outlet />
      </div>
    </div>
  )
}
