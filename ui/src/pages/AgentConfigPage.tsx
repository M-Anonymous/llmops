import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import {
  getAgentList,
  updateAgent,
  type Agent,
  type AgentRuntimeConfig,
  type RuntimePreset,
} from '../api/agent'
import { getLibraryList, type Library } from '../api/library'
import { getMiddlewareList, type Middleware } from '../api/middleware'
import { getMcpServerList, getMcpServerTools, type McpServer, type McpToolInfo } from '../api/mcp'
import { getModelList, type Model } from '../api/model'
import { getToolList, type Tool } from '../api/tool'
import { McpToolList } from '../components/McpToolList'
import '../styles/common.css'
import './LibraryPage.css'
import './AgentPage.css'
import './MiddlewarePage.css'
import './MiddlewarePage.css'

const RUNTIME_PRESETS: Array<{
  value: RuntimePreset
  title: string
  subtitle: string
  temperature: number
}> = [
  { value: 'creative', title: '创意', subtitle: 'temperature 1.0', temperature: 1.0 },
  { value: 'balanced', title: '平衡', subtitle: 'temperature 0.7', temperature: 0.7 },
  { value: 'precise', title: '精确', subtitle: 'temperature 0.2', temperature: 0.2 },
  { value: 'custom', title: '自定义', subtitle: '手动参数', temperature: 0.7 },
]

function middlewareTypeDesc(type: number) {
  return type === 0 ? 'Summarization' : 'HumanInTheLoop'
}

function mcpTransportDesc(_transport: number) {
  return 'streamable_http'
}

function countSelectedMcpTools(
  serverIds: string[],
  cache: Record<string, string[]>,
  toolsByServer: Record<string, McpToolInfo[]>,
) {
  let total = 0
  for (const serverId of serverIds) {
    const serverTools = toolsByServer[serverId] ?? []
    const selected = cache[serverId] ?? serverTools.map((tool) => tool.name)
    total += selected.length
  }
  return total
}

function buildRuntimeConfig(
  preset: RuntimePreset,
  custom: { temperature: string; top_p: string; max_tokens: string },
): AgentRuntimeConfig {
  const config: AgentRuntimeConfig = { preset }
  if (preset !== 'custom') {
    return config
  }
  if (custom.temperature.trim()) {
    config.temperature = Number(custom.temperature)
  }
  if (custom.top_p.trim()) {
    config.top_p = Number(custom.top_p)
  }
  if (custom.max_tokens.trim()) {
    config.max_tokens = Number(custom.max_tokens)
  }
  return config
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
  const [mcpServers, setMcpServers] = useState<McpServer[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [systemPrompt, setSystemPrompt] = useState('')
  const [modelId, setModelId] = useState('')
  const [libraryIds, setLibraryIds] = useState<string[]>([])
  const [toolIds, setToolIds] = useState<string[]>([])
  const [middlewareIds, setMiddlewareIds] = useState<string[]>([])
  const [mcpServerIds, setMcpServerIds] = useState<string[]>([])
  const [runtimePreset, setRuntimePreset] = useState<RuntimePreset>('balanced')
  const [runtimeCustom, setRuntimeCustom] = useState({
    temperature: '',
    top_p: '',
    max_tokens: '',
  })
  const [mcpToolCache, setMcpToolCache] = useState<Record<string, string[]>>({})
  const [mcpToolsByServer, setMcpToolsByServer] = useState<Record<string, McpToolInfo[]>>({})
  const [mcpToolsLoading, setMcpToolsLoading] = useState<Record<string, boolean>>({})
  const [mcpToolsExpanded, setMcpToolsExpanded] = useState<Record<string, boolean>>({})

  function isMcpToolsExpanded(serverId: string) {
    return mcpToolsExpanded[serverId] !== false
  }

  function toggleMcpToolsExpanded(serverId: string) {
    setMcpToolsExpanded((prev) => ({
      ...prev,
      [serverId]: !isMcpToolsExpanded(serverId),
    }))
  }

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

  const loadMcpToolsForServer = useCallback(
    async (serverId: string) => {
      setMcpToolsLoading((prev) => ({ ...prev, [serverId]: true }))
      try {
        const tools = await getMcpServerTools(serverId)
        setMcpToolsByServer((prev) => ({ ...prev, [serverId]: tools }))
        return tools
      } catch (err) {
        handleApiError(err, '加载 MCP 工具列表失败')
        return []
      } finally {
        setMcpToolsLoading((prev) => ({ ...prev, [serverId]: false }))
      }
    },
    [handleApiError],
  )

  const loadData = useCallback(async () => {
    if (!agentId) {
      return
    }

    setLoading(true)
    setError(null)
    try {
      const [agentList, libraryList, toolList, modelList, middlewareList, mcpList] =
        await Promise.all([
          getAgentList(),
          getLibraryList(),
          getToolList(),
          getModelList(),
          getMiddlewareList(),
          getMcpServerList(),
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
      setMcpServerIds(current.mcpServerIds ?? [])
      const rc = current.runtimeConfig ?? { preset: 'balanced' as RuntimePreset }
      setRuntimePreset(rc.preset ?? 'balanced')
      setRuntimeCustom({
        temperature: rc.temperature != null ? String(rc.temperature) : '',
        top_p: rc.top_p != null ? String(rc.top_p) : '',
        max_tokens: rc.max_tokens != null ? String(rc.max_tokens) : '',
      })
      setMcpToolCache(current.mcpToolCache ?? {})
      setLibraries(libraryList)
      setTools(toolList.filter((tool) => tool.enabled))
      setModels(modelList)
      setMiddlewares(middlewareList)
      setMcpServers(mcpList.filter((item) => item.enabled))

      const selectedMcpIds = current.mcpServerIds ?? []
      await Promise.all(
        selectedMcpIds.map(async (serverId) => {
          await loadMcpToolsForServer(serverId)
        }),
      )
      setMcpToolsExpanded((prev) => {
        const next = { ...prev }
        for (const serverId of selectedMcpIds) {
          if (next[serverId] === undefined) {
            next[serverId] = true
          }
        }
        return next
      })
    } catch (err) {
      handleApiError(err, '加载 Agent 配置失败')
    } finally {
      setLoading(false)
    }
  }, [agentId, handleApiError, loadMcpToolsForServer])

  useEffect(() => {
    if (!agentId) {
      navigate('/admin/agent', { replace: true })
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

  function toggleMcpTool(serverId: string, toolName: string, checked: boolean) {
    setMcpToolCache((prev) => {
      const current = prev[serverId] ?? mcpToolsByServer[serverId]?.map((t) => t.name) ?? []
      const next = checked
        ? current.includes(toolName)
          ? current
          : [...current, toolName]
        : current.filter((name) => name !== toolName)
      return { ...prev, [serverId]: next }
    })
  }

  function selectAllMcpTools(serverId: string) {
    const names = mcpToolsByServer[serverId]?.map((tool) => tool.name) ?? []
    setMcpToolCache((prev) => ({ ...prev, [serverId]: names }))
  }

  function clearAllMcpTools(serverId: string) {
    setMcpToolCache((prev) => ({ ...prev, [serverId]: [] }))
  }

  async function handleMcpServerToggle(serverId: string, checked: boolean) {
    setMcpServerIds((prev) => toggleId(prev, serverId, checked))
    if (!checked) {
      setMcpToolCache((prev) => {
        const next = { ...prev }
        delete next[serverId]
        return next
      })
      setMcpToolsExpanded((prev) => {
        const next = { ...prev }
        delete next[serverId]
        return next
      })
      return
    }

    setMcpToolsExpanded((prev) => ({ ...prev, [serverId]: true }))

    const tools = mcpToolsByServer[serverId] ?? (await loadMcpToolsForServer(serverId))
    if (tools.length === 0) {
      return
    }
    setMcpToolCache((prev) => {
      if (prev[serverId]?.length) {
        return prev
      }
      return { ...prev, [serverId]: tools.map((tool) => tool.name) }
    })
  }

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!agent) {
      return
    }

    setSubmitting(true)
    setError(null)

    try {
      const cacheToSave: Record<string, string[]> = {}
      for (const serverId of mcpServerIds) {
        const serverTools = mcpToolsByServer[serverId] ?? []
        if (!serverTools.length) {
          continue
        }
        const selected = mcpToolCache[serverId] ?? serverTools.map((tool) => tool.name)
        // 仅在选择部分工具时写入 cache；全选则不写 key，运行时加载全部
        if (selected.length < serverTools.length) {
          cacheToSave[serverId] = selected
        } else if (mcpToolCache[serverId]?.length) {
          cacheToSave[serverId] = selected
        }
      }

      await updateAgent({
        id: agent.id,
        system_prompt: systemPrompt.trim() || null,
        model_id: modelId.trim() || null,
        library_ids: libraryIds,
        tool_ids: toolIds,
        middleware_ids: middlewareIds,
        mcp_server_ids: mcpServerIds,
        runtime_config: buildRuntimeConfig(runtimePreset, runtimeCustom),
        mcp_tool_cache: cacheToSave,
      })
      navigate('/admin/agent')
    } catch (err) {
      handleApiError(err, '保存配置失败')
    } finally {
      setSubmitting(false)
    }
  }

  const title = agent?.name || agentNameFromQuery || 'Agent 配置'
  const selectedMcpToolCount = countSelectedMcpTools(
    mcpServerIds,
    mcpToolCache,
    mcpToolsByServer,
  )

  return (
    <div className="library-page agent-page">
      <div className="page-bg" aria-hidden="true">
        <div className="page-bg-glow page-bg-glow--left" />
        <div className="page-bg-glow page-bg-glow--right" />
        <div className="page-bg-grid" />
      </div>

      <header className="library-header">
        <div className="library-header-left">
          <Link to="/admin/agent" className="library-back-link">
            ← 返回 Agent 列表
          </Link>
          <div>
            <p className="brand-eyebrow">Agent Config</p>
            <h1 className="library-title">{title}</h1>
            <p className="agent-config-subtitle">配置系统提示词、模型、知识库、工具、中间件与 MCP</p>
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
            <Link to="/admin/agent" className="library-create-btn">
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
                  暂无模型，请先去 <Link to="/admin/model">模型管理</Link> 创建
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
              <h2>运行参数</h2>
              <p className="middleware-hint">控制模型采样风格；修改后需新开会话生效</p>
              <div className="middleware-type-tabs">
                {RUNTIME_PRESETS.map((item) => (
                  <button
                    key={item.value}
                    type="button"
                    className={`middleware-type-tab ${
                      runtimePreset === item.value ? 'middleware-type-tab--active' : ''
                    }`}
                    onClick={() => setRuntimePreset(item.value)}
                  >
                    <strong>{item.title}</strong>
                    <span>{item.subtitle}</span>
                  </button>
                ))}
              </div>
              {runtimePreset === 'custom' ? (
                <div className="middleware-condition-row">
                  <label className="library-field">
                    <span>temperature</span>
                    <input
                      value={runtimeCustom.temperature}
                      onChange={(event) =>
                        setRuntimeCustom((prev) => ({
                          ...prev,
                          temperature: event.target.value,
                        }))
                      }
                      inputMode="decimal"
                      placeholder="0.7"
                    />
                  </label>
                  <label className="library-field">
                    <span>top_p</span>
                    <input
                      value={runtimeCustom.top_p}
                      onChange={(event) =>
                        setRuntimeCustom((prev) => ({ ...prev, top_p: event.target.value }))
                      }
                      inputMode="decimal"
                      placeholder="1.0"
                    />
                  </label>
                  <label className="library-field">
                    <span>max_tokens</span>
                    <input
                      value={runtimeCustom.max_tokens}
                      onChange={(event) =>
                        setRuntimeCustom((prev) => ({
                          ...prev,
                          max_tokens: event.target.value,
                        }))
                      }
                      inputMode="numeric"
                      placeholder="4096"
                    />
                  </label>
                </div>
              ) : (
                <p className="agent-config-runtime-summary">
                  当前预设 temperature ={' '}
                  {RUNTIME_PRESETS.find((item) => item.value === runtimePreset)?.temperature ??
                    0.7}
                </p>
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
                  暂无中间件，请先去 <Link to="/admin/middleware">中间件管理</Link> 创建
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

            <section className="agent-config-section">
              <div className="agent-config-section-head">
                <h2>关联 MCP Server</h2>
                <span>
                  已选 {mcpServerIds.length} 个 Server
                  {mcpServerIds.length > 0 ? ` · ${selectedMcpToolCount} 个工具` : ''}
                </span>
              </div>
              <p className="middleware-hint">
                勾选 Server 后可选择要挂载的工具；未单独选择的 Server 将加载其全部工具
              </p>
              {mcpServers.length === 0 ? (
                <div className="agent-config-empty">
                  暂无 MCP Server，请先去 <Link to="/admin/mcp">MCP 管理</Link> 创建并启用
                </div>
              ) : (
                <div className="agent-mcp-list">
                  {mcpServers.map((item) => {
                    const checked = mcpServerIds.includes(item.id)
                    const serverTools = mcpToolsByServer[item.id] ?? []
                    const selectedTools =
                      mcpToolCache[item.id] ?? serverTools.map((tool) => tool.name)
                    const loadingTools = mcpToolsLoading[item.id]
                    const toolsExpanded = isMcpToolsExpanded(item.id)

                    return (
                      <div
                        key={item.id}
                        className={`agent-mcp-block ${checked ? 'is-checked' : ''}`}
                      >
                        <label className={`agent-option ${checked ? 'is-checked' : ''}`}>
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(event) =>
                              void handleMcpServerToggle(item.id, event.target.checked)
                            }
                          />
                          <div>
                            <strong>{item.label || item.name}</strong>
                            <p className="agent-option-name">{item.name}</p>
                            <p>{mcpTransportDesc(item.transport)}</p>
                          </div>
                        </label>

                        {checked ? (
                          <div className="agent-mcp-tools">
                            <button
                              type="button"
                              className="agent-mcp-tools-toggle"
                              aria-expanded={toolsExpanded}
                              onClick={() => toggleMcpToolsExpanded(item.id)}
                            >
                              <span className="agent-mcp-tools-toggle-label">工具列表</span>
                              <span className="agent-mcp-tools-toggle-meta">
                                {loadingTools
                                  ? '加载中…'
                                  : `${selectedTools.length} / ${serverTools.length}`}
                              </span>
                              <span
                                className={`agent-mcp-chevron ${toolsExpanded ? 'is-expanded' : ''}`}
                                aria-hidden="true"
                              >
                                ▾
                              </span>
                            </button>

                            {toolsExpanded ? (
                              loadingTools ? (
                                <p className="agent-config-empty">加载工具列表…</p>
                              ) : serverTools.length === 0 ? (
                                <p className="agent-config-empty">该 Server 暂无可用工具</p>
                              ) : (
                                <McpToolList
                                  tools={serverTools}
                                  selectable
                                  selectedNames={selectedTools}
                                  onToggle={(toolName, checked) =>
                                    toggleMcpTool(item.id, toolName, checked)
                                  }
                                  onSelectAll={() => selectAllMcpTools(item.id)}
                                  onClearAll={() => clearAllMcpTools(item.id)}
                                />
                              )
                            ) : null}
                          </div>
                        ) : null}
                      </div>
                    )
                  })}
                </div>
              )}
            </section>

            <div className="agent-config-actions">
              <Link to="/admin/agent" className="library-action-btn library-action-btn--secondary">
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
