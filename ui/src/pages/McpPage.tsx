import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import {
  createMcpServer,
  deleteMcpServer,
  getMcpServerList,
  getMcpServerTools,
  listMcpToolsFromConfig,
  testMcpServerConnection,
  updateMcpServer,
  type McpServer,
  type McpToolInfo,
} from '../api/mcp'
import { McpToolList } from '../components/McpToolList'
import '../styles/common.css'
import './LibraryPage.css'
import './MiddlewarePage.css'

type FormMode = 'create' | 'edit'

/** 当前仅支持 streamable_http */
const STREAMABLE_HTTP_TRANSPORT = 2 as const

interface McpFormState {
  name: string
  label: string
  desc: string
  enabled: boolean
  url: string
  headersText: string
  timeout: string
  sseReadTimeout: string
  terminateOnClose: boolean
}

const emptyForm: McpFormState = {
  name: '',
  label: '',
  desc: '',
  enabled: true,
  url: '',
  headersText: '',
  timeout: '',
  sseReadTimeout: '',
  terminateOnClose: true,
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

function parseJsonObject(text: string, field: string): Record<string, string> {
  const trimmed = text.trim()
  if (!trimmed) {
    return {}
  }
  let parsed: unknown
  try {
    parsed = JSON.parse(trimmed)
  } catch {
    throw new Error(`${field} 不是合法 JSON`)
  }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error(`${field} 必须是 JSON 对象`)
  }
  const result: Record<string, string> = {}
  for (const [key, value] of Object.entries(parsed as Record<string, unknown>)) {
    result[key] = String(value)
  }
  return result
}

function configFromForm(form: McpFormState): Record<string, unknown> {
  const config: Record<string, unknown> = {
    url: form.url.trim(),
    terminate_on_close: form.terminateOnClose,
  }
  const headers = parseJsonObject(form.headersText, 'headers')
  if (Object.keys(headers).length > 0) {
    config.headers = headers
  }
  if (form.timeout.trim()) {
    config.timeout = Number(form.timeout)
  }
  if (form.sseReadTimeout.trim()) {
    config.sse_read_timeout = Number(form.sseReadTimeout)
  }
  return config
}

function formFromServer(server: McpServer): McpFormState {
  const config = server.config || {}
  return {
    name: server.name,
    label: server.label,
    desc: server.desc || '',
    enabled: server.enabled,
    url: typeof config.url === 'string' ? config.url : '',
    headersText:
      config.headers && typeof config.headers === 'object'
        ? JSON.stringify(config.headers, null, 2)
        : '',
    timeout: config.timeout != null ? String(config.timeout) : '',
    sseReadTimeout: config.sse_read_timeout != null ? String(config.sse_read_timeout) : '',
    terminateOnClose: config.terminate_on_close !== false,
  }
}

export default function McpPage() {
  const navigate = useNavigate()
  const [servers, setServers] = useState<McpServer[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [formMode, setFormMode] = useState<FormMode>('create')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<McpFormState>(emptyForm)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [previewItem, setPreviewItem] = useState<McpServer | null>(null)
  const [testing, setTesting] = useState(false)
  const [testSuccess, setTestSuccess] = useState(false)
  const [testError, setTestError] = useState<string | null>(null)
  const [toolsModalOpen, setToolsModalOpen] = useState(false)
  const [toolsLoading, setToolsLoading] = useState(false)
  const [toolsError, setToolsError] = useState<string | null>(null)
  const [toolsList, setToolsList] = useState<McpToolInfo[]>([])
  const [toolsTitle, setToolsTitle] = useState('')

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

  const loadServers = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setServers(await getMcpServerList())
    } catch (err) {
      handleApiError(err, '加载 MCP Server 列表失败')
    } finally {
      setLoading(false)
    }
  }, [handleApiError])

  useEffect(() => {
    void loadServers()
  }, [loadServers])

  function openCreateForm() {
    setFormMode('create')
    setEditingId(null)
    setForm(emptyForm)
    setShowForm(true)
    setError(null)
    setTestSuccess(false)
    setTestError(null)
    setToolsModalOpen(false)
  }

  function openEditForm(server: McpServer) {
    setFormMode('edit')
    setEditingId(server.id)
    setForm(formFromServer(server))
    setShowForm(true)
    setError(null)
    setTestSuccess(false)
    setTestError(null)
    setToolsModalOpen(false)
  }

  function closeForm() {
    setShowForm(false)
    setEditingId(null)
    setForm(emptyForm)
    setTestSuccess(false)
    setTestError(null)
    setToolsModalOpen(false)
  }

  function validateFormConnectionFields() {
    if (!form.name.trim()) {
      throw new Error('请先填写内部名称')
    }
    if (!form.url.trim()) {
      throw new Error('请先填写 url')
    }
  }

  async function handleTestConnection() {
    setTesting(true)
    setTestError(null)
    setTestSuccess(false)
    setError(null)

    try {
      validateFormConnectionFields()
      const config = configFromForm(form)
      await testMcpServerConnection({
        name: form.name.trim(),
        transport: STREAMABLE_HTTP_TRANSPORT,
        config,
      })
      setTestSuccess(true)
    } catch (err) {
      setTestSuccess(false)
      if (err instanceof ApiError) {
        setTestError(err.message)
      } else if (err instanceof Error) {
        setTestError(err.message)
      } else {
        setTestError('连接测试失败')
      }
    } finally {
      setTesting(false)
    }
  }

  async function handleViewTools(fromForm = true, server?: McpServer) {
    setToolsModalOpen(true)
    setToolsLoading(true)
    setToolsError(null)
    setToolsList([])
    setToolsTitle(server?.label || server?.name || form.label || form.name || 'MCP 工具')

    try {
      if (fromForm) {
        validateFormConnectionFields()
        const config = configFromForm(form)
        const tools = await listMcpToolsFromConfig({
          name: form.name.trim(),
          transport: STREAMABLE_HTTP_TRANSPORT,
          config,
        })
        setToolsList(tools)
      } else if (server) {
        const tools = await getMcpServerTools(server.id)
        setToolsList(tools)
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setToolsError(err.message)
      } else if (err instanceof Error) {
        setToolsError(err.message)
      } else {
        setToolsError('加载工具列表失败')
      }
    } finally {
      setToolsLoading(false)
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      const config = configFromForm(form)
      const payload = {
        name: form.name.trim(),
        label: form.label.trim(),
        desc: form.desc.trim(),
        transport: STREAMABLE_HTTP_TRANSPORT,
        config,
        enabled: form.enabled,
      }
      if (formMode === 'create') {
        await createMcpServer(payload)
      } else if (editingId) {
        await updateMcpServer({ id: editingId, ...payload })
      }
      closeForm()
      await loadServers()
    } catch (err) {
      handleApiError(err, formMode === 'create' ? '创建 MCP Server 失败' : '更新 MCP Server 失败')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(server: McpServer) {
    const confirmed = window.confirm(
      `确定删除 MCP Server「${server.label || server.name}」吗？此操作不可恢复。`,
    )
    if (!confirmed) {
      return
    }

    setDeletingId(server.id)
    setError(null)
    try {
      await deleteMcpServer(server.id)
      await loadServers()
    } catch (err) {
      handleApiError(err, '删除 MCP Server 失败')
    } finally {
      setDeletingId(null)
    }
  }

  const previewJson = useMemo(
    () => (previewItem ? JSON.stringify(previewItem.config, null, 2) : ''),
    [previewItem],
  )

  return (
    <div className="admin-panel middleware-page">
      <header className="library-header">
        <div className="library-header-left">
          <div>
            <p className="brand-eyebrow">MCP</p>
            <h1 className="library-title">MCP Server 管理</h1>
          </div>
        </div>
        <button type="button" className="library-create-btn" onClick={openCreateForm}>
          + 新建 MCP Server
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
        ) : servers.length === 0 ? (
          <div className="library-empty">
            暂无 MCP Server，点击右上角新建。创建后可在 Agent 配置中挂载。
          </div>
        ) : (
          <div className="library-grid">
            {servers.map((item) => (
              <article key={item.id} className="library-card">
                <div className="library-card-top">
                  <div className="library-card-meta">
                    <div className="middleware-card-title-row">
                      <h2 className="library-card-title">{item.label || item.name}</h2>
                      <span
                        className={`middleware-type-badge ${
                          item.enabled ? 'middleware-type-badge--summary' : 'middleware-type-badge--hitl'
                        }`}
                      >
                        {item.enabled ? '已启用' : '已停用'}
                      </span>
                    </div>
                    <p className="library-card-desc">Streamable HTTP</p>
                    <p className="agent-option-name">{item.name}</p>
                    {item.desc ? <p className="library-card-desc">{item.desc}</p> : null}
                  </div>
                </div>

                <dl className="library-card-info">
                  <div>
                    <dt>传输</dt>
                    <dd>streamable_http</dd>
                  </div>
                  <div>
                    <dt>更新时间</dt>
                    <dd>{formatDate(item.updateAt)}</dd>
                  </div>
                </dl>

                <div className="library-card-actions">
                  <button
                    type="button"
                    className="library-action-btn library-action-btn--secondary"
                    onClick={() => void handleViewTools(false, item)}
                  >
                    工具
                  </button>
                  <button
                    type="button"
                    className="library-action-btn library-action-btn--secondary"
                    onClick={() => setPreviewItem(item)}
                  >
                    预览
                  </button>
                  <button
                    type="button"
                    className="library-action-btn library-action-btn--primary"
                    onClick={() => openEditForm(item)}
                  >
                    编辑
                  </button>
                  <button
                    type="button"
                    className="library-action-btn library-action-btn--danger"
                    disabled={deletingId === item.id}
                    onClick={() => void handleDelete(item)}
                  >
                    {deletingId === item.id ? '删除中…' : '删除'}
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </main>

      {previewItem && (
        <div className="library-modal-overlay" role="presentation" onClick={() => setPreviewItem(null)}>
          <div
            className="library-modal middleware-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="mcp-json-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="library-modal-header">
              <h2 id="mcp-json-title">配置预览</h2>
              <button type="button" className="library-modal-close" onClick={() => setPreviewItem(null)}>
                ×
              </button>
            </div>
            <div className="middleware-json-meta">
              <p className="middleware-json-label">{previewItem.label || previewItem.name}</p>
              <p className="middleware-json-desc">Streamable HTTP</p>
            </div>
            <div className="middleware-json-result">
              <div className="middleware-json-result-head">config</div>
              <pre>{previewJson}</pre>
            </div>
          </div>
        </div>
      )}

      {showForm && (
        <div className="library-modal-overlay" role="presentation" onClick={closeForm}>
          <div
            className="library-modal middleware-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="mcp-form-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="library-modal-header">
              <h2 id="mcp-form-title">{formMode === 'create' ? '新建 MCP Server' : '编辑 MCP Server'}</h2>
              <button type="button" className="library-modal-close" onClick={closeForm}>
                ×
              </button>
            </div>

            <form className="library-form" onSubmit={(event) => void handleSubmit(event)}>
              <label className="library-field">
                <span>显示名称</span>
                <input
                  value={form.label}
                  onChange={(event) => setForm((prev) => ({ ...prev, label: event.target.value }))}
                  required
                  maxLength={255}
                  placeholder="例如：文件系统 MCP"
                />
              </label>

              <label className="library-field">
                <span>内部名称</span>
                <input
                  value={form.name}
                  onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
                  required
                  maxLength={100}
                  placeholder="连接键，如 filesystem"
                  disabled={formMode === 'edit'}
                />
              </label>

              <label className="library-field">
                <span>描述</span>
                <textarea
                  value={form.desc}
                  onChange={(event) => setForm((prev) => ({ ...prev, desc: event.target.value }))}
                  rows={2}
                  placeholder="可选说明"
                />
              </label>

              <label className="library-field">
                <span>传输方式</span>
                <input value="streamable_http" disabled readOnly />
                <p className="middleware-hint">当前仅支持 Streamable HTTP</p>
              </label>

              <label className="library-field">
                <span className="middleware-inline-checks">
                  <input
                    type="checkbox"
                    checked={form.enabled}
                    onChange={(event) =>
                      setForm((prev) => ({ ...prev, enabled: event.target.checked }))
                    }
                  />
                  启用该 Server
                </span>
              </label>

              <label className="library-field">
                <span>url</span>
                <input
                  value={form.url}
                  onChange={(event) => setForm((prev) => ({ ...prev, url: event.target.value }))}
                  required
                  placeholder="http://localhost:8000/mcp"
                />
              </label>
              <label className="library-field">
                <span>headers JSON（可选）</span>
                <textarea
                  value={form.headersText}
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, headersText: event.target.value }))
                  }
                  rows={3}
                  placeholder='{"Authorization":"Bearer xxx"}'
                />
              </label>
              <div className="middleware-condition-row">
                <label className="library-field">
                  <span>timeout（秒，可选）</span>
                  <input
                    value={form.timeout}
                    onChange={(event) =>
                      setForm((prev) => ({ ...prev, timeout: event.target.value }))
                    }
                    inputMode="decimal"
                    placeholder="30"
                  />
                </label>
                <label className="library-field">
                  <span>sse_read_timeout（秒，可选）</span>
                  <input
                    value={form.sseReadTimeout}
                    onChange={(event) =>
                      setForm((prev) => ({ ...prev, sseReadTimeout: event.target.value }))
                    }
                    inputMode="decimal"
                    placeholder="300"
                  />
                </label>
              </div>
              <label className="library-field">
                <span className="middleware-inline-checks">
                  <input
                    type="checkbox"
                    checked={form.terminateOnClose}
                    onChange={(event) =>
                      setForm((prev) => ({
                        ...prev,
                        terminateOnClose: event.target.checked,
                      }))
                    }
                  />
                  terminate_on_close
                </span>
              </label>

              {(testError || testSuccess) && (
                <div
                  className={`library-alert ${testSuccess ? 'library-alert--success' : ''}`}
                  role="status"
                >
                  {testError ?? '连接成功'}
                </div>
              )}

              <div className="library-form-actions mcp-form-actions">
                <button
                  type="button"
                  className="library-action-btn library-action-btn--secondary"
                  disabled={testing || submitting || toolsLoading}
                  onClick={() => void handleTestConnection()}
                >
                  {testing ? '测试中…' : '测试连接'}
                </button>
                <button
                  type="button"
                  className="library-action-btn library-action-btn--secondary"
                  disabled={testing || submitting || toolsLoading}
                  onClick={() => void handleViewTools(true)}
                >
                  {toolsLoading ? '加载中…' : '工具'}
                </button>
                <button
                  type="button"
                  className="library-action-btn library-action-btn--secondary"
                  onClick={closeForm}
                >
                  取消
                </button>
                <button type="submit" className="library-create-btn" disabled={submitting || testing}>
                  {submitting ? '保存中…' : '保存'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {toolsModalOpen && (
        <div
          className="library-modal-overlay"
          role="presentation"
          onClick={() => setToolsModalOpen(false)}
        >
          <div
            className="library-modal middleware-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="mcp-tools-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="library-modal-header">
              <h2 id="mcp-tools-title">工具 — {toolsTitle}</h2>
              <button
                type="button"
                className="library-modal-close"
                onClick={() => setToolsModalOpen(false)}
              >
                ×
              </button>
            </div>
            {toolsLoading ? (
              <p className="agent-config-empty">加载中…</p>
            ) : toolsError ? (
              <div className="library-alert" role="alert">
                {toolsError}
              </div>
            ) : toolsList.length === 0 ? (
              <p className="agent-config-empty">暂无可用工具</p>
            ) : (
              <McpToolList tools={toolsList} variant="modal" />
            )}
          </div>
        </div>
      )}
    </div>
  )
}
