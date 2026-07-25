import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import {
  createTool,
  deleteTool,
  getToolList,
  getToolSchema,
  invokeTool,
  updateTool,
  type Tool,
} from '../api/tool'
import '../styles/common.css'
import './LibraryPage.css'
import './ToolPage.css'

type FormMode = 'create' | 'edit'
type HttpMethod = 'GET' | 'POST'
type ParamType = 'string' | 'number' | 'integer' | 'boolean' | 'array' | 'object'
type ParamListKey = 'params' | 'headers' | 'body'

interface ToolParam {
  name: string
  type: ParamType
  desc: string
  required: boolean
  default_value: string
  inject_from_context: boolean
}

interface ToolFormState {
  name: string
  label: string
  desc: string
  baseUrl: string
  path: string
  method: HttpMethod
  params: ToolParam[]
  headers: ToolParam[]
  body: ToolParam[]
  enabled: boolean
}

const PARAM_TYPES: ParamType[] = ['string', 'number', 'integer', 'boolean', 'array', 'object']

const emptyParam = (): ToolParam => ({
  name: '',
  type: 'string',
  desc: '',
  required: true,
  default_value: '',
  inject_from_context: false,
})

const emptyForm: ToolFormState = {
  name: '',
  label: '',
  desc: '',
  baseUrl: 'https://api.example.com',
  path: '/',
  method: 'GET',
  params: [],
  headers: [],
  body: [],
  enabled: true,
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

function summarizeApiConfig(apiConfig: Record<string, unknown>) {
  const method = typeof apiConfig.method === 'string' ? apiConfig.method : '-'
  const baseUrl = typeof apiConfig.base_url === 'string' ? apiConfig.base_url : ''
  const path = typeof apiConfig.path === 'string' ? apiConfig.path : ''
  return `${method} ${baseUrl}${path}`.trim()
}

function getInvocableParams(tool: Tool): ToolParam[] {
  const apiConfig = tool.apiConfig ?? {}
  const params = normalizeParamList(apiConfig.params)
  const body = normalizeParamList(apiConfig.body)
  // 与后端一致：invoke arguments 来自 params + body
  return [...params, ...body].filter((param) => param.name.trim())
}

function formatInvokeResult(result: unknown) {
  if (typeof result === 'string') {
    try {
      return JSON.stringify(JSON.parse(result), null, 2)
    } catch {
      return result
    }
  }
  try {
    return JSON.stringify(result, null, 2)
  } catch {
    return String(result)
  }
}

function normalizeParam(raw: unknown): ToolParam {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
    return emptyParam()
  }
  const item = raw as Record<string, unknown>
  const type = PARAM_TYPES.includes(item.type as ParamType) ? (item.type as ParamType) : 'string'
  return {
    name: typeof item.name === 'string' ? item.name : '',
    type,
    desc: typeof item.desc === 'string' ? item.desc : '',
    required: Boolean(item.required),
    default_value: item.default_value == null ? '' : String(item.default_value),
    inject_from_context: Boolean(item.inject_from_context),
  }
}

function normalizeParamList(raw: unknown): ToolParam[] {
  if (!Array.isArray(raw)) {
    return []
  }
  return raw.map(normalizeParam)
}

function formFromTool(tool: Tool): ToolFormState {
  const apiConfig = tool.apiConfig ?? {}
  const method = apiConfig.method === 'POST' ? 'POST' : 'GET'
  return {
    name: tool.name,
    label: tool.label,
    desc: tool.desc,
    baseUrl: typeof apiConfig.base_url === 'string' ? apiConfig.base_url : '',
    path: typeof apiConfig.path === 'string' ? apiConfig.path : '/',
    method,
    params: normalizeParamList(apiConfig.params),
    headers: normalizeParamList(apiConfig.headers),
    body: normalizeParamList(apiConfig.body),
    enabled: tool.enabled,
  }
}

function serializeParams(params: ToolParam[]) {
  return params.map((param) => ({
    name: param.name.trim(),
    type: param.type,
    desc: param.desc.trim(),
    required: param.required,
    enum: null,
    default_value: param.default_value.trim() || null,
    inject_from_context: param.inject_from_context,
  }))
}

function validateParams(params: ToolParam[], label: string) {
  for (const [index, param] of params.entries()) {
    if (!param.name.trim()) {
      throw new Error(`${label}第 ${index + 1} 项：名称不能为空`)
    }
    if (!param.desc.trim()) {
      throw new Error(`${label}第 ${index + 1} 项：描述不能为空`)
    }
  }
}

export default function ToolPage() {
  const navigate = useNavigate()
  const [tools, setTools] = useState<Tool[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formMode, setFormMode] = useState<FormMode | null>(null)
  const [editingTool, setEditingTool] = useState<Tool | null>(null)
  const [form, setForm] = useState<ToolFormState>(emptyForm)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const [testingTool, setTestingTool] = useState<Tool | null>(null)
  const [testArgs, setTestArgs] = useState<Record<string, string>>({})
  const [testResult, setTestResult] = useState<string | null>(null)
  const [testError, setTestError] = useState<string | null>(null)
  const [testing, setTesting] = useState(false)

  const [schemaTool, setSchemaTool] = useState<Tool | null>(null)
  const [schemaText, setSchemaText] = useState<string | null>(null)
  const [schemaError, setSchemaError] = useState<string | null>(null)
  const [schemaLoading, setSchemaLoading] = useState(false)

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

  const loadTools = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getToolList()
      setTools(data)
    } catch (err) {
      handleApiError(err, '加载工具列表失败')
    } finally {
      setLoading(false)
    }
  }, [handleApiError])

  useEffect(() => {
    void loadTools()
  }, [loadTools])

  function openCreateForm() {
    setFormMode('create')
    setEditingTool(null)
    setForm(emptyForm)
    setError(null)
  }

  function openEditForm(tool: Tool) {
    setFormMode('edit')
    setEditingTool(tool)
    setForm(formFromTool(tool))
    setError(null)
  }

  function closeForm() {
    setFormMode(null)
    setEditingTool(null)
    setForm(emptyForm)
  }

  function updateParam(listKey: ParamListKey, index: number, patch: Partial<ToolParam>) {
    setForm((prev) => ({
      ...prev,
      [listKey]: prev[listKey].map((item, i) => (i === index ? { ...item, ...patch } : item)),
    }))
  }

  function addParam(listKey: ParamListKey) {
    setForm((prev) => ({
      ...prev,
      [listKey]: [...prev[listKey], emptyParam()],
    }))
  }

  function removeParam(listKey: ParamListKey, index: number) {
    setForm((prev) => ({
      ...prev,
      [listKey]: prev[listKey].filter((_, i) => i !== index),
    }))
  }

  function buildApiConfig() {
    if (!form.baseUrl.trim()) {
      throw new Error('base_url 不能为空')
    }
    if (!form.path.trim()) {
      throw new Error('path 不能为空')
    }
    validateParams(form.params, 'params')
    validateParams(form.headers, 'headers')
    validateParams(form.body, 'body')

    return {
      base_url: form.baseUrl.trim().replace(/\/$/, ''),
      path: form.path.trim().startsWith('/') ? form.path.trim() : `/${form.path.trim()}`,
      method: form.method,
      params: serializeParams(form.params),
      headers: serializeParams(form.headers),
      body: form.method === 'POST' ? serializeParams(form.body) : [],
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      const apiConfig = buildApiConfig()
      const payload = {
        name: form.name.trim(),
        label: form.label.trim(),
        desc: form.desc.trim(),
        api_config: apiConfig,
        enabled: form.enabled,
      }

      if (formMode === 'create') {
        await createTool(payload)
      } else if (formMode === 'edit' && editingTool) {
        await updateTool({
          id: editingTool.id,
          ...payload,
        })
      }
      closeForm()
      await loadTools()
    } catch (err) {
      handleApiError(err, '保存工具失败')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(tool: Tool) {
    const confirmed = window.confirm(`确定删除工具「${tool.label}」吗？此操作不可恢复。`)
    if (!confirmed) {
      return
    }

    setDeletingId(tool.id)
    setError(null)

    try {
      await deleteTool(tool.id)
      await loadTools()
    } catch (err) {
      handleApiError(err, '删除工具失败')
    } finally {
      setDeletingId(null)
    }
  }

  async function handleToggleEnabled(tool: Tool) {
    setError(null)
    try {
      await updateTool({
        id: tool.id,
        enabled: !tool.enabled,
      })
      await loadTools()
    } catch (err) {
      handleApiError(err, '更新工具状态失败')
    }
  }

  function openTestForm(tool: Tool) {
    if (!tool.enabled) {
      setError('请先启用工具再测试调用')
      return
    }
    const initialArgs: Record<string, string> = {}
    for (const param of getInvocableParams(tool)) {
      initialArgs[param.name] = param.default_value
    }
    setTestingTool(tool)
    setTestArgs(initialArgs)
    setTestResult(null)
    setTestError(null)
    setError(null)
  }

  function closeTestForm() {
    setTestingTool(null)
    setTestArgs({})
    setTestResult(null)
    setTestError(null)
    setTesting(false)
  }

  async function openSchemaView(tool: Tool) {
    if (!tool.enabled) {
      setError('请先启用工具再查看 Schema')
      return
    }

    setSchemaTool(tool)
    setSchemaText(null)
    setSchemaError(null)
    setSchemaLoading(true)
    setError(null)

    try {
      const schema = await getToolSchema(tool.name)
      setSchemaText(JSON.stringify(schema, null, 2))
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          navigate('/login')
          return
        }
        setSchemaError(err.message)
      } else {
        setSchemaError(err instanceof Error ? err.message : '获取 Schema 失败')
      }
    } finally {
      setSchemaLoading(false)
    }
  }

  function closeSchemaView() {
    setSchemaTool(null)
    setSchemaText(null)
    setSchemaError(null)
    setSchemaLoading(false)
  }

  async function handleTestInvoke(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!testingTool) {
      return
    }

    const argumentsPayload: Record<string, unknown> = {}
    for (const param of getInvocableParams(testingTool)) {
      const value = (testArgs[param.name] ?? '').trim()
      if (!value) {
        if (param.required && !param.inject_from_context) {
          setTestError(`参数「${param.name}」为必填项`)
          return
        }
        continue
      }
      argumentsPayload[param.name] = value
    }

    setTesting(true)
    setTestError(null)
    setTestResult(null)

    try {
      const response = await invokeTool({
        name: testingTool.name,
        arguments: argumentsPayload,
      })
      setTestResult(formatInvokeResult(response.result))
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          navigate('/login')
          return
        }
        setTestError(err.message)
      } else {
        setTestError(err instanceof Error ? err.message : '调用工具失败')
      }
    } finally {
      setTesting(false)
    }
  }

  function renderParamList(listKey: ParamListKey, title: string, hint: string) {
    const items = form[listKey]
    return (
      <section className="tool-param-section">
        <div className="tool-param-section-head">
          <div>
            <h3>{title}</h3>
            <p>{hint}</p>
          </div>
          <button
            type="button"
            className="library-action-btn library-action-btn--secondary"
            onClick={() => addParam(listKey)}
          >
            + 添加
          </button>
        </div>

        {items.length === 0 ? (
          <div className="tool-param-empty">暂无参数，可点击添加</div>
        ) : (
          <div className="tool-param-list">
            {items.map((param, index) => (
              <div key={`${listKey}-${index}`} className="tool-param-item">
                <div className="tool-param-item-head">
                  <span>#{index + 1}</span>
                  <button
                    type="button"
                    className="library-action-btn library-action-btn--danger"
                    onClick={() => removeParam(listKey, index)}
                  >
                    删除
                  </button>
                </div>

                <div className="tool-param-grid">
                  <label className="library-field">
                    <span>名称</span>
                    <input
                      value={param.name}
                      required
                      placeholder="如 city"
                      onChange={(event) =>
                        updateParam(listKey, index, { name: event.target.value })
                      }
                    />
                  </label>

                  <label className="library-field">
                    <span>类型</span>
                    <select
                      value={param.type}
                      onChange={(event) =>
                        updateParam(listKey, index, { type: event.target.value as ParamType })
                      }
                    >
                      {PARAM_TYPES.map((type) => (
                        <option key={type} value={type}>
                          {type}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="library-field tool-param-desc">
                    <span>描述</span>
                    <input
                      value={param.desc}
                      required
                      placeholder="给大模型看的参数说明"
                      onChange={(event) =>
                        updateParam(listKey, index, { desc: event.target.value })
                      }
                    />
                  </label>

                  <label className="library-field">
                    <span>默认值</span>
                    <input
                      value={param.default_value}
                      placeholder="可选"
                      onChange={(event) =>
                        updateParam(listKey, index, { default_value: event.target.value })
                      }
                    />
                  </label>
                </div>

                <div className="tool-param-checks">
                  <label className="tool-enabled-field">
                    <input
                      type="checkbox"
                      checked={param.required}
                      onChange={(event) =>
                        updateParam(listKey, index, { required: event.target.checked })
                      }
                    />
                    <span>必填</span>
                  </label>
                  <label className="tool-enabled-field">
                    <input
                      type="checkbox"
                      checked={param.inject_from_context}
                      onChange={(event) =>
                        updateParam(listKey, index, {
                          inject_from_context: event.target.checked,
                        })
                      }
                    />
                    <span>从上下文注入</span>
                  </label>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    )
  }

  return (
    <div className="library-page tool-page">
      <div className="page-bg" aria-hidden="true">
        <div className="page-bg-glow page-bg-glow--left" />
        <div className="page-bg-glow page-bg-glow--right" />
        <div className="page-bg-grid" />
      </div>

      <header className="library-header">
        <div className="library-header-left">
          <Link to="/" className="library-back-link">
            ← 返回首页
          </Link>
          <div>
            <p className="brand-eyebrow">API Tools</p>
            <h1 className="library-title">API 工具管理</h1>
          </div>
        </div>
        <button type="button" className="library-create-btn" onClick={openCreateForm}>
          + 新建工具
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
        ) : tools.length === 0 ? (
          <div className="library-empty">
            <p>还没有 API 工具</p>
            <button type="button" className="library-create-btn" onClick={openCreateForm}>
              创建第一个工具
            </button>
          </div>
        ) : (
          <section className="library-grid">
            {tools.map((tool) => (
              <article key={tool.id} className="library-card">
                <div className="library-card-head">
                  <div className="library-card-icon library-card-icon--placeholder">
                    {tool.label.slice(0, 1).toUpperCase()}
                  </div>
                  <div className="library-card-meta">
                    <div className="tool-card-title-row">
                      <h2 className="library-card-title">{tool.label}</h2>
                      <span className={`tool-enabled ${tool.enabled ? 'tool-enabled--on' : 'tool-enabled--off'}`}>
                        {tool.enabled ? '已启用' : '已禁用'}
                      </span>
                    </div>
                    <p className="tool-name">{tool.name}</p>
                    <p className="library-card-desc">{tool.desc}</p>
                  </div>
                </div>

                <dl className="library-card-info">
                  <div>
                    <dt>接口</dt>
                    <dd className="tool-api-summary">{summarizeApiConfig(tool.apiConfig)}</dd>
                  </div>
                  <div>
                    <dt>更新时间</dt>
                    <dd>{formatDate(tool.updateAt)}</dd>
                  </div>
                </dl>

                <div className="library-card-actions">
                  <button
                    type="button"
                    className="library-action-btn library-action-btn--primary"
                    onClick={() => openTestForm(tool)}
                    disabled={!tool.enabled}
                    title={tool.enabled ? '测试调用' : '请先启用工具'}
                  >
                    测试
                  </button>
                  <button
                    type="button"
                    className="library-action-btn library-action-btn--secondary"
                    onClick={() => void openSchemaView(tool)}
                    disabled={!tool.enabled}
                    title={tool.enabled ? '查看 Schema' : '请先启用工具'}
                  >
                    Schema
                  </button>
                  <button
                    type="button"
                    className="library-action-btn library-action-btn--secondary"
                    onClick={() => void handleToggleEnabled(tool)}
                  >
                    {tool.enabled ? '禁用' : '启用'}
                  </button>
                  <button
                    type="button"
                    className="library-action-btn library-action-btn--secondary"
                    onClick={() => openEditForm(tool)}
                  >
                    编辑
                  </button>
                  <button
                    type="button"
                    className="library-action-btn library-action-btn--danger"
                    onClick={() => void handleDelete(tool)}
                    disabled={deletingId === tool.id}
                  >
                    {deletingId === tool.id ? '删除中…' : '删除'}
                  </button>
                </div>
              </article>
            ))}
          </section>
        )}
      </main>

      {formMode && (
        <div className="library-modal-overlay" onClick={closeForm}>
          <div
            className="library-modal tool-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="tool-form-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="library-modal-header">
              <h2 id="tool-form-title">{formMode === 'create' ? '新建工具' : '编辑工具'}</h2>
              <button type="button" className="library-modal-close" onClick={closeForm}>
                ×
              </button>
            </div>

            <form className="library-form" onSubmit={(event) => void handleSubmit(event)}>
              <label className="library-field">
                <span>调用名 name</span>
                <input
                  value={form.name}
                  maxLength={100}
                  required
                  placeholder="如 get_weather"
                  onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
                />
              </label>

              <label className="library-field">
                <span>显示名 label</span>
                <input
                  value={form.label}
                  maxLength={100}
                  required
                  placeholder="如 获取天气"
                  onChange={(event) => setForm((prev) => ({ ...prev, label: event.target.value }))}
                />
              </label>

              <label className="library-field">
                <span>描述 desc</span>
                <textarea
                  value={form.desc}
                  required
                  rows={3}
                  placeholder="给大模型看的工具说明"
                  onChange={(event) => setForm((prev) => ({ ...prev, desc: event.target.value }))}
                />
              </label>

              <section className="tool-api-section">
                <h3>API 基础配置</h3>
                <div className="tool-api-grid">
                  <label className="library-field">
                    <span>base_url</span>
                    <input
                      value={form.baseUrl}
                      required
                      placeholder="https://api.example.com"
                      onChange={(event) =>
                        setForm((prev) => ({ ...prev, baseUrl: event.target.value }))
                      }
                    />
                  </label>

                  <label className="library-field">
                    <span>method</span>
                    <select
                      value={form.method}
                      onChange={(event) =>
                        setForm((prev) => ({
                          ...prev,
                          method: event.target.value as HttpMethod,
                        }))
                      }
                    >
                      <option value="GET">GET</option>
                      <option value="POST">POST</option>
                    </select>
                  </label>

                  <label className="library-field tool-path-field">
                    <span>path</span>
                    <input
                      value={form.path}
                      required
                      placeholder="/get_weather"
                      onChange={(event) =>
                        setForm((prev) => ({ ...prev, path: event.target.value }))
                      }
                    />
                  </label>
                </div>
              </section>

              {renderParamList('headers', 'Headers', '如 Authorization，可勾选从上下文注入')}
              {renderParamList('params', 'Query Params', '通常用于 GET 查询参数')}
              {form.method === 'POST' &&
                renderParamList('body', 'Body', 'POST 请求体字段')}

              <label className="tool-enabled-field">
                <input
                  type="checkbox"
                  checked={form.enabled}
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, enabled: event.target.checked }))
                  }
                />
                <span>启用该工具</span>
              </label>

              <div className="library-form-actions">
                <button
                  type="button"
                  className="library-action-btn library-action-btn--secondary"
                  onClick={closeForm}
                >
                  取消
                </button>
                <button type="submit" className="library-create-btn" disabled={submitting}>
                  {submitting ? '保存中…' : '保存'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {schemaTool && (
        <div className="library-modal-overlay" onClick={closeSchemaView}>
          <div
            className="library-modal tool-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="tool-schema-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="library-modal-header">
              <h2 id="tool-schema-title">工具 Schema</h2>
              <button type="button" className="library-modal-close" onClick={closeSchemaView}>
                ×
              </button>
            </div>

            <div className="library-form">
              <div className="tool-test-meta">
                <p className="tool-test-label">{schemaTool.label}</p>
                <p className="tool-name">{schemaTool.name}</p>
              </div>

              {schemaLoading && <div className="tool-param-empty">加载中…</div>}

              {schemaError && (
                <div className="library-alert" role="alert">
                  {schemaError}
                </div>
              )}

              {schemaText && (
                <div className="tool-test-result tool-schema-result">
                  <div className="tool-test-result-head">OpenAI Function Schema</div>
                  <pre>{schemaText}</pre>
                </div>
              )}

              <div className="library-form-actions">
                <button
                  type="button"
                  className="library-action-btn library-action-btn--secondary"
                  onClick={closeSchemaView}
                >
                  关闭
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {testingTool && (
        <div className="library-modal-overlay" onClick={closeTestForm}>
          <div
            className="library-modal tool-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="tool-test-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="library-modal-header">
              <h2 id="tool-test-title">测试工具</h2>
              <button type="button" className="library-modal-close" onClick={closeTestForm}>
                ×
              </button>
            </div>

            <form className="library-form" onSubmit={(event) => void handleTestInvoke(event)}>
              <div className="tool-test-meta">
                <p className="tool-test-label">{testingTool.label}</p>
                <p className="tool-name">{testingTool.name}</p>
                <p className="tool-api-summary">{summarizeApiConfig(testingTool.apiConfig)}</p>
              </div>

              {getInvocableParams(testingTool).length === 0 ? (
                <div className="tool-param-empty">该工具无需入参，可直接调用</div>
              ) : (
                getInvocableParams(testingTool).map((param) => (
                  <label key={param.name} className="library-field">
                    <span>
                      {param.name}
                      {param.required ? ' *' : ''}
                      <em className="tool-test-param-desc">{param.desc}</em>
                    </span>
                    <input
                      value={testArgs[param.name] ?? ''}
                      required={param.required && !param.inject_from_context}
                      placeholder={param.default_value || param.desc || param.name}
                      onChange={(event) =>
                        setTestArgs((prev) => ({
                          ...prev,
                          [param.name]: event.target.value,
                        }))
                      }
                    />
                  </label>
                ))
              )}

              {testError && (
                <div className="library-alert" role="alert">
                  {testError}
                </div>
              )}

              {testResult !== null && (
                <div className="tool-test-result">
                  <div className="tool-test-result-head">调用结果</div>
                  <pre>{testResult}</pre>
                </div>
              )}

              <div className="library-form-actions">
                <button
                  type="button"
                  className="library-action-btn library-action-btn--secondary"
                  onClick={closeTestForm}
                >
                  关闭
                </button>
                <button type="submit" className="library-create-btn" disabled={testing}>
                  {testing ? '调用中…' : '开始测试'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
