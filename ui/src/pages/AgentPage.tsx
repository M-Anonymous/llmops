import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import {
  createAgent,
  deleteAgent,
  getAgentList,
  type Agent,
} from '../api/agent'
import '../styles/common.css'
import './LibraryPage.css'
import './AgentPage.css'

interface CreateFormState {
  name: string
  desc: string
  icon: string
}

const emptyForm: CreateFormState = {
  name: '',
  desc: '',
  icon: '',
}

function formatDate(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function AgentPage() {
  const navigate = useNavigate()
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [form, setForm] = useState<CreateFormState>(emptyForm)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleApiError = useCallback(
    (err: unknown, fallback: string) => {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          navigate('/login')
          return
        }
        setError(err.message)
        return
      }
      setError(err instanceof Error ? err.message : fallback)
    },
    [navigate],
  )

  const loadAgents = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getAgentList()
      setAgents(data)
    } catch (err) {
      handleApiError(err, '加载 Agent 列表失败')
    } finally {
      setLoading(false)
    }
  }, [handleApiError])

  useEffect(() => {
    void loadAgents()
  }, [loadAgents])

  function openCreateForm() {
    setShowCreateForm(true)
    setForm(emptyForm)
    setError(null)
  }

  function closeCreateForm() {
    setShowCreateForm(false)
    setForm(emptyForm)
  }

  function goConfig(agent: Agent) {
    navigate(
      `/agent/config?agent_id=${encodeURIComponent(agent.id)}&agent_name=${encodeURIComponent(agent.name)}`,
    )
  }

  function goDebug(agent: Agent) {
    navigate(
      `/agent/debug?agent_id=${encodeURIComponent(agent.id)}&agent_name=${encodeURIComponent(agent.name)}`,
    )
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      const result = await createAgent({
        name: form.name.trim(),
        desc: form.desc.trim(),
        icon: form.icon.trim() || undefined,
      })
      closeCreateForm()
      navigate(
        `/agent/config?agent_id=${encodeURIComponent(result.id)}&agent_name=${encodeURIComponent(form.name.trim())}`,
      )
    } catch (err) {
      handleApiError(err, '创建 Agent 失败')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(agent: Agent) {
    const confirmed = window.confirm(`确定删除 Agent「${agent.name}」吗？此操作不可恢复。`)
    if (!confirmed) {
      return
    }

    setDeletingId(agent.id)
    setError(null)

    try {
      await deleteAgent(agent.id)
      await loadAgents()
    } catch (err) {
      handleApiError(err, '删除 Agent 失败')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="library-page agent-page">
      <div className="page-bg" aria-hidden="true">
        <div className="page-bg-glow page-bg-glow--left" />
        <div className="page-bg-glow page-bg-glow--right" />
        <div className="page-bg-grid" />
      </div>

      <header className="library-header">
        <div className="library-header-left">
          <Link to="/admin" className="library-back-link">
            ← 返回管理端
          </Link>
          <div>
            <p className="brand-eyebrow">Agents</p>
            <h1 className="library-title">Agent 管理</h1>
          </div>
        </div>
        <button type="button" className="library-create-btn" onClick={openCreateForm}>
          + 新建 Agent
        </button>
      </header>

      <main className="library-main">
        {error && (
          <div className="library-alert" role="alert">
            {error}
          </div>
        )}

        {loading ? (
          <div className="library-empty">加载中…</div>
        ) : agents.length === 0 ? (
          <div className="library-empty">
            <p>还没有 Agent</p>
            <button type="button" className="library-create-btn" onClick={openCreateForm}>
              创建第一个 Agent
            </button>
          </div>
        ) : (
          <section className="library-grid">
            {agents.map((agent) => (
              <article key={agent.id} className="library-card">
                <div className="library-card-head">
                  {agent.icon ? (
                    <img src={agent.icon} alt="" className="library-card-icon" />
                  ) : (
                    <div className="library-card-icon library-card-icon--placeholder">
                      {agent.name.slice(0, 1).toUpperCase()}
                    </div>
                  )}
                  <div className="library-card-meta">
                    <h2 className="library-card-title">{agent.name}</h2>
                    <p className="library-card-desc">{agent.desc}</p>
                  </div>
                </div>

                <dl className="library-card-info">
                  <div>
                    <dt>知识库</dt>
                    <dd>{agent.libraryIds?.length ?? 0} 个</dd>
                  </div>
                  <div>
                    <dt>工具</dt>
                    <dd>{agent.toolIds?.length ?? 0} 个</dd>
                  </div>
                  <div>
                    <dt>中间件</dt>
                    <dd>{agent.middlewareIds?.length ?? 0} 个</dd>
                  </div>
                  <div>
                    <dt>更新时间</dt>
                    <dd>{formatDate(agent.updateAt)}</dd>
                  </div>
                </dl>

                <div className="library-card-actions">
                  <button
                    type="button"
                    className="library-action-btn library-action-btn--primary"
                    onClick={() => goDebug(agent)}
                  >
                    调试
                  </button>
                  <button
                    type="button"
                    className="library-action-btn library-action-btn--secondary"
                    onClick={() => goConfig(agent)}
                  >
                    配置
                  </button>
                  <button
                    type="button"
                    className="library-action-btn library-action-btn--danger"
                    onClick={() => void handleDelete(agent)}
                    disabled={deletingId === agent.id}
                  >
                    {deletingId === agent.id ? '删除中…' : '删除'}
                  </button>
                </div>
              </article>
            ))}
          </section>
        )}
      </main>

      {showCreateForm && (
        <div className="library-modal-overlay" onClick={closeCreateForm}>
          <div
            className="library-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="agent-create-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="library-modal-header">
              <h2 id="agent-create-title">新建 Agent</h2>
              <button type="button" className="library-modal-close" onClick={closeCreateForm}>
                ×
              </button>
            </div>

            <p className="agent-step-hint">第一步：填写基础信息，完成后进入配置页</p>

            <form className="library-form" onSubmit={(event) => void handleCreate(event)}>
              <label className="library-field">
                <span>Agent 名称</span>
                <input
                  value={form.name}
                  maxLength={100}
                  required
                  placeholder="如 客服助手"
                  onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
                />
              </label>

              <label className="library-field">
                <span>图标 URL</span>
                <input
                  value={form.icon}
                  maxLength={255}
                  placeholder="可选，图片地址"
                  onChange={(event) => setForm((prev) => ({ ...prev, icon: event.target.value }))}
                />
              </label>

              <label className="library-field">
                <span>描述</span>
                <textarea
                  value={form.desc}
                  maxLength={255}
                  required
                  rows={3}
                  placeholder="简要描述这个 Agent 的用途"
                  onChange={(event) => setForm((prev) => ({ ...prev, desc: event.target.value }))}
                />
              </label>

              <div className="library-form-actions">
                <button
                  type="button"
                  className="library-action-btn library-action-btn--secondary"
                  onClick={closeCreateForm}
                >
                  取消
                </button>
                <button type="submit" className="library-create-btn" disabled={submitting}>
                  {submitting ? '创建中…' : '下一步：配置'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
