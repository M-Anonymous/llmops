import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { getAgentList, updateAgent, type Agent } from '../api/agent'
import { getLibraryList, type Library } from '../api/library'
import { getMiddlewareList, type Middleware } from '../api/middleware'
import { getModelList, type Model } from '../api/model'
import { getToolList, type Tool } from '../api/tool'
import '../styles/common.css'
import './LibraryPage.css'
import './AgentPage.css'

function middlewareTypeDesc(type: number) {
  return type === 0 ? 'Summarization' : 'HumanInTheLoop'
}

export default function AgentConfigPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const agentId = searchParams.get('agent_id') ?? ''
  const agentNameFromQuery = searchParams.get('agent_name')

  const [agent, setAgent] = useState<Agent | null>(null)
  const [libraries, setLibraries] = useState<Library[]>([])
  const [tools, setTools] = useState<Tool[]>([])
  const [models, setModels] = useState<Model[]>([])
  const [middlewares, setMiddlewares] = useState<Middleware[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [systemPrompt, setSystemPrompt] = useState('')
  const [modelId, setModelId] = useState('')
  const [libraryIds, setLibraryIds] = useState<string[]>([])
  const [toolIds, setToolIds] = useState<string[]>([])
  const [middlewareIds, setMiddlewareIds] = useState<string[]>([])

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

  const loadData = useCallback(async () => {
    if (!agentId) {
      return
    }

    setLoading(true)
    setError(null)
    try {
      const [agentList, libraryList, toolList, modelList, middlewareList] = await Promise.all([
        getAgentList(),
        getLibraryList(),
        getToolList(),
        getModelList(),
        getMiddlewareList(),
      ])
      const current = agentList.find((item) => item.id === agentId)
      if (!current) {
        setError('Agent 不存在或无权访问')
        setAgent(null)
        return
      }
      setAgent(current)
      setSystemPrompt(current.systemPrompt ?? '')
      setModelId(current.modelId ?? '')
      setLibraryIds(current.libraryIds ?? [])
      setToolIds(current.toolIds ?? [])
      setMiddlewareIds(current.middlewareIds ?? [])
      setLibraries(libraryList)
      setTools(toolList.filter((tool) => tool.enabled))
      setModels(modelList)
      setMiddlewares(middlewareList)
    } catch (err) {
      handleApiError(err, '加载 Agent 配置失败')
    } finally {
      setLoading(false)
    }
  }, [agentId, handleApiError])

  useEffect(() => {
    if (!agentId) {
      navigate('/agent', { replace: true })
      return
    }
    void loadData()
  }, [agentId, loadData, navigate])

  function toggleId(list: string[], id: string, checked: boolean) {
    if (checked) {
      return list.includes(id) ? list : [...list, id]
    }
    return list.filter((item) => item !== id)
  }

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!agent) {
      return
    }

    setSubmitting(true)
    setError(null)

    try {
      await updateAgent({
        id: agent.id,
        system_prompt: systemPrompt.trim() || null,
        model_id: modelId.trim() || null,
        library_ids: libraryIds,
        tool_ids: toolIds,
        middleware_ids: middlewareIds,
      })
      navigate('/agent')
    } catch (err) {
      handleApiError(err, '保存配置失败')
    } finally {
      setSubmitting(false)
    }
  }

  const title = agent?.name || agentNameFromQuery || 'Agent 配置'

  return (
    <div className="library-page agent-page">
      <div className="page-bg" aria-hidden="true">
        <div className="page-bg-glow page-bg-glow--left" />
        <div className="page-bg-glow page-bg-glow--right" />
        <div className="page-bg-grid" />
      </div>

      <header className="library-header">
        <div className="library-header-left">
          <Link to="/agent" className="library-back-link">
            ← 返回 Agent 列表
          </Link>
          <div>
            <p className="brand-eyebrow">Agent Config</p>
            <h1 className="library-title">{title}</h1>
            <p className="agent-config-subtitle">配置系统提示词、模型、知识库、工具与中间件</p>
          </div>
        </div>
      </header>

      <main className="library-main">
        {error && (
          <div className="library-alert" role="alert">
            {error}
          </div>
        )}

        {loading ? (
          <div className="library-empty">加载中…</div>
        ) : !agent ? (
          <div className="library-empty">
            <p>未找到 Agent</p>
            <Link to="/agent" className="library-create-btn">
              返回列表
            </Link>
          </div>
        ) : (
          <form className="agent-config-panel" onSubmit={(event) => void handleSave(event)}>
            <section className="agent-config-section">
              <h2>基础信息</h2>
              <div className="agent-config-basic">
                {agent.icon ? (
                  <img src={agent.icon} alt="" className="library-card-icon" />
                ) : (
                  <div className="library-card-icon library-card-icon--placeholder">
                    {agent.name.slice(0, 1).toUpperCase()}
                  </div>
                )}
                <div>
                  <p className="agent-config-name">{agent.name}</p>
                  <p className="agent-config-desc">{agent.desc}</p>
                </div>
              </div>
            </section>

            <section className="agent-config-section">
              <h2>模型</h2>
              {models.length === 0 ? (
                <div className="agent-config-empty">
                  暂无模型，请先去 <Link to="/model">模型管理</Link> 创建
                </div>
              ) : (
                <label className="library-field">
                  <span>选择模型</span>
                  <select
                    value={modelId}
                    onChange={(event) => setModelId(event.target.value)}
                  >
                    <option value="">不关联模型</option>
                    {models.map((model) => (
                      <option key={model.id} value={model.id}>
                        {model.label}（{model.name}）
                      </option>
                    ))}
                  </select>
                </label>
              )}
            </section>

            <section className="agent-config-section">
              <h2>系统提示词</h2>
              <label className="library-field">
                <span>system prompt</span>
                <textarea
                  className="agent-prompt-editor"
                  value={systemPrompt}
                  rows={10}
                  placeholder="定义 Agent 的角色、能力与回答风格"
                  onChange={(event) => setSystemPrompt(event.target.value)}
                />
              </label>
            </section>

            <section className="agent-config-section">
              <div className="agent-config-section-head">
                <h2>关联知识库</h2>
                <span>已选 {libraryIds.length} 个</span>
              </div>
              {libraries.length === 0 ? (
                <div className="agent-config-empty">暂无知识库，请先去知识库模块创建</div>
              ) : (
                <div className="agent-option-list">
                  {libraries.map((library) => {
                    const checked = libraryIds.includes(library.id)
                    return (
                      <label key={library.id} className={`agent-option ${checked ? 'is-checked' : ''}`}>
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(event) =>
                            setLibraryIds((prev) => toggleId(prev, library.id, event.target.checked))
                          }
                        />
                        <div>
                          <strong>{library.name}</strong>
                          <p>{library.desc}</p>
                        </div>
                      </label>
                    )
                  })}
                </div>
              )}
            </section>

            <section className="agent-config-section">
              <div className="agent-config-section-head">
                <h2>关联工具</h2>
                <span>已选 {toolIds.length} 个（仅展示已启用工具）</span>
              </div>
              {tools.length === 0 ? (
                <div className="agent-config-empty">暂无可用工具，请先去工具模块创建并启用</div>
              ) : (
                <div className="agent-option-list">
                  {tools.map((tool) => {
                    const checked = toolIds.includes(tool.id)
                    return (
                      <label key={tool.id} className={`agent-option ${checked ? 'is-checked' : ''}`}>
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(event) =>
                            setToolIds((prev) => toggleId(prev, tool.id, event.target.checked))
                          }
                        />
                        <div>
                          <strong>{tool.label}</strong>
                          <p className="agent-option-name">{tool.name}</p>
                          <p>{tool.desc}</p>
                        </div>
                      </label>
                    )
                  })}
                </div>
              )}
            </section>

            <section className="agent-config-section">
              <div className="agent-config-section-head">
                <h2>关联中间件</h2>
                <span>已选 {middlewareIds.length} 个</span>
              </div>
              {middlewares.length === 0 ? (
                <div className="agent-config-empty">
                  暂无中间件，请先去 <Link to="/middleware">中间件管理</Link> 创建
                </div>
              ) : (
                <div className="agent-option-list">
                  {middlewares.map((item) => {
                    const checked = middlewareIds.includes(item.id)
                    return (
                      <label key={item.id} className={`agent-option ${checked ? 'is-checked' : ''}`}>
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(event) =>
                            setMiddlewareIds((prev) =>
                              toggleId(prev, item.id, event.target.checked),
                            )
                          }
                        />
                        <div>
                          <strong>{item.label || '未命名中间件'}</strong>
                          <p>{middlewareTypeDesc(item.type)}</p>
                        </div>
                      </label>
                    )
                  })}
                </div>
              )}
            </section>

            <div className="agent-config-actions">
              <Link to="/agent" className="library-action-btn library-action-btn--secondary">
                返回列表
              </Link>
              <button type="submit" className="library-create-btn" disabled={submitting}>
                {submitting ? '保存中…' : '保存配置'}
              </button>
            </div>
          </form>
        )}
      </main>
    </div>
  )
}
