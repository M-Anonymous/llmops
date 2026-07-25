import { Link } from 'react-router-dom'
import '../styles/common.css'
import './HomePage.css'

const modules = [
  {
    title: 'Agent 对话',
    desc: '与智能助手进行多轮对话，支持工具调用与记忆。',
    tag: 'Session',
    href: null,
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

export default function HomePage() {
  return (
    <div className="home-page">
      <div className="page-bg" aria-hidden="true">
        <div className="page-bg-glow page-bg-glow--left" />
        <div className="page-bg-glow page-bg-glow--right" />
        <div className="page-bg-grid" />
      </div>

      <header className="home-header">
        <div className="home-brand">
          <div className="brand-logo">L</div>
          <div>
            <p className="brand-eyebrow">LLM Operations Platform</p>
            <h1 className="brand-title">llmops</h1>
          </div>
        </div>
        <Link to="/login" className="home-login-link">
          重新登录
        </Link>
      </header>

      <main className="home-main">
        <section className="home-hero">
          <p className="home-badge">登录成功</p>
          <h2 className="home-heading">欢迎回来</h2>
          <p className="home-subtitle">
            你已通过 GitHub 完成身份验证，可以从下方模块开始探索 llmops 平台。
          </p>
        </section>

        <section className="home-grid">
          {modules.map((item) => (
            <article key={item.tag} className="home-card">
              <span className="home-card-tag">{item.tag}</span>
              <h3 className="home-card-title">{item.title}</h3>
              <p className="home-card-desc">{item.desc}</p>
              {item.href ? (
                <Link to={item.href} className="home-card-link">
                  进入管理
                </Link>
              ) : (
                <button type="button" className="home-card-action" disabled>
                  即将开放
                </button>
              )}
            </article>
          ))}
        </section>
      </main>
    </div>
  )
}
