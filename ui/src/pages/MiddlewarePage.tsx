import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import {
  createMiddleware,
  deleteMiddleware,
  getMiddlewareList,
  updateMiddleware,
  type Middleware,
  type MiddlewareType,
} from '../api/middleware'
import { getModelList, type Model } from '../api/model'
import { getToolList, type Tool } from '../api/tool'
import '../styles/common.css'
import './LibraryPage.css'
import './MiddlewarePage.css'

type FormMode = 'create' | 'edit'
type ThresholdKind = 'tokens' | 'messages' | 'fraction'
type TriggerMode = 'single' | 'any' | 'group'

interface ThresholdCondition {
  kind: ThresholdKind
  value: string
}

interface AndGroup {
  tokens: string
  messages: string
  fraction: string
}

interface InterruptRule {
  toolName: string
  enabled: boolean
  advanced: boolean
  allowedDecisions: string[]
}

interface FormState {
  label: string
  type: MiddlewareType
  modelId: string
  triggerMode: TriggerMode
  singleTrigger: ThresholdCondition
  anyTriggers: ThresholdCondition[]
  groupTriggers: AndGroup[]
  keep: ThresholdCondition
  descriptionPrefix: string
  interruptRules: InterruptRule[]
}

const THRESHOLD_KINDS: { value: ThresholdKind; label: string; hint: string }[] = [
  { value: 'tokens', label: 'tokens', hint: '绝对 token 数量' },
  { value: 'messages', label: 'messages', hint: '消息条数' },
  { value: 'fraction', label: 'fraction', hint: '上下文占比 0~1' },
]

const TRIGGER_MODES: { value: TriggerMode; label: string; desc: string }[] = [
  { value: 'single', label: '单一条件', desc: '满足一个阈值即触发' },
  { value: 'any', label: '多条件任一', desc: '多个条件，任一满足即触发' },
  { value: 'group', label: '条件组', desc: '组内 AND，组间 OR' },
]

const DECISION_OPTIONS = ['approve', 'reject'] as const

const emptyCondition = (kind: ThresholdKind = 'tokens', value = ''): ThresholdCondition => ({
  kind,
  value,
})

const emptyGroup = (): AndGroup => ({
  tokens: '',
  messages: '',
  fraction: '',
})

const emptyInterruptRule = (): InterruptRule => ({
  toolName: '',
  enabled: true,
  advanced: false,
  allowedDecisions: ['approve', 'reject'],
})

const emptyForm: FormState = {
  label: '',
  type: 0,
  modelId: '',
  triggerMode: 'single',
  singleTrigger: emptyCondition('tokens', '4000'),
  anyTriggers: [emptyCondition('tokens', '3000'), emptyCondition('messages', '20')],
  groupTriggers: [
    { tokens: '5000', messages: '3', fraction: '' },
    { tokens: '3000', messages: '6', fraction: '' },
  ],
  keep: emptyCondition('messages', '20'),
  descriptionPrefix: 'Tool execution pending approval',
  interruptRules: [emptyInterruptRule()],
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

function middlewareTypeDesc(type: MiddlewareType) {
  return type === 0 ? '上下文超限时自动摘要压缩' : '工具调用前人工审批中断'
}

function isThresholdKind(value: unknown): value is ThresholdKind {
  return value === 'tokens' || value === 'messages' || value === 'fraction'
}

function parseConditionValue(kind: ThresholdKind, raw: string): number {
  const value = Number(raw)
  if (!Number.isFinite(value)) {
    throw new Error(`${kind} 需要填写有效数字`)
  }
  if (kind === 'fraction') {
    if (value < 0 || value > 1) {
      throw new Error('fraction 取值范围为 0~1')
    }
    return value
  }
  if (value < 0 || !Number.isInteger(value)) {
    throw new Error(`${kind} 需要填写非负整数`)
  }
  return value
}

function serializeCondition(condition: ThresholdCondition): [ThresholdKind, number] {
  return [condition.kind, parseConditionValue(condition.kind, condition.value.trim())]
}

function serializeKeep(condition: ThresholdCondition): [ThresholdKind, number] {
  return serializeCondition(condition)
}

function serializeTrigger(form: FormState): unknown {
  if (form.triggerMode === 'single') {
    return serializeCondition(form.singleTrigger)
  }

  if (form.triggerMode === 'any') {
    if (form.anyTriggers.length === 0) {
      throw new Error('请至少添加一个 trigger 条件')
    }
    return form.anyTriggers.map((item) => serializeCondition(item))
  }

  if (form.groupTriggers.length === 0) {
    throw new Error('请至少添加一个 trigger 条件组')
  }

  return form.groupTriggers.map((group, index) => {
    const result: Record<string, number> = {}
    if (group.tokens.trim()) {
      result.tokens = parseConditionValue('tokens', group.tokens.trim())
    }
    if (group.messages.trim()) {
      result.messages = parseConditionValue('messages', group.messages.trim())
    }
    if (group.fraction.trim()) {
      result.fraction = parseConditionValue('fraction', group.fraction.trim())
    }
    if (Object.keys(result).length === 0) {
      throw new Error(`条件组 ${index + 1} 至少填写一个阈值`)
    }
    return result
  })
}

function serializeInterruptOn(rules: InterruptRule[]): Record<string, unknown> {
  const interruptOn: Record<string, unknown> = {}
  const seen = new Set<string>()

  for (const rule of rules) {
    const toolName = rule.toolName.trim()
    if (!toolName) {
      throw new Error('工具名称不能为空')
    }
    if (seen.has(toolName)) {
      throw new Error(`工具「${toolName}」重复配置`)
    }
    seen.add(toolName)

    if (!rule.enabled) {
      interruptOn[toolName] = false
      continue
    }

    if (!rule.advanced) {
      interruptOn[toolName] = true
      continue
    }

    if (rule.allowedDecisions.length === 0) {
      throw new Error(`工具「${toolName}」至少选择一个 allowed_decisions`)
    }

    interruptOn[toolName] = {
      allowed_decisions: rule.allowedDecisions,
    }
  }

  if (Object.keys(interruptOn).length === 0) {
    throw new Error('请至少配置一个 interrupt_on 工具')
  }

  return interruptOn
}

function buildConfig(form: FormState): Record<string, unknown> {
  if (form.type === 0) {
    if (!form.modelId) {
      throw new Error('请选择摘要模型')
    }
    return {
      model: form.modelId,
      trigger: serializeTrigger(form),
      keep: serializeKeep(form.keep),
    }
  }

  return {
    interrupt_on: serializeInterruptOn(form.interruptRules),
    description_prefix: form.descriptionPrefix.trim() || 'Tool execution pending approval',
  }
}

function parseConditionPair(raw: unknown): ThresholdCondition | null {
  if (!Array.isArray(raw) || raw.length !== 2 || !isThresholdKind(raw[0])) {
    return null
  }
  return {
    kind: raw[0],
    value: String(raw[1] ?? ''),
  }
}

function detectTriggerMode(trigger: unknown): TriggerMode {
  if (Array.isArray(trigger) && trigger.length === 2 && typeof trigger[0] === 'string') {
    return 'single'
  }
  if (Array.isArray(trigger) && trigger.every((item) => Array.isArray(item))) {
    return 'any'
  }
  if (
    Array.isArray(trigger) &&
    trigger.every((item) => item && typeof item === 'object' && !Array.isArray(item))
  ) {
    return 'group'
  }
  return 'single'
}

function formFromMiddleware(item: Middleware): FormState {
  const config = item.config ?? {}
  const next: FormState = {
    ...emptyForm,
    label: item.label ?? '',
    type: item.type === 1 ? 1 : 0,
  }

  if (next.type === 0) {
    next.modelId = typeof config.model === 'string' ? config.model : ''
    const keep = parseConditionPair(config.keep)
    if (keep) {
      next.keep = keep
    }

    const trigger = config.trigger
    const mode = detectTriggerMode(trigger)
    next.triggerMode = mode

    if (mode === 'single') {
      const single = parseConditionPair(trigger)
      if (single) {
        next.singleTrigger = single
      }
    } else if (mode === 'any' && Array.isArray(trigger)) {
      const pairs = trigger
        .map((item) => parseConditionPair(item))
        .filter((item): item is ThresholdCondition => Boolean(item))
      if (pairs.length > 0) {
        next.anyTriggers = pairs
      }
    } else if (mode === 'group' && Array.isArray(trigger)) {
      const groups = trigger.map((item) => {
        const record = (item ?? {}) as Record<string, unknown>
        return {
          tokens: record.tokens == null ? '' : String(record.tokens),
          messages: record.messages == null ? '' : String(record.messages),
          fraction: record.fraction == null ? '' : String(record.fraction),
        }
      })
      if (groups.length > 0) {
        next.groupTriggers = groups
      }
    }
    return next
  }

  next.descriptionPrefix =
    typeof config.description_prefix === 'string'
      ? config.description_prefix
      : emptyForm.descriptionPrefix

  const interruptOn =
    config.interrupt_on && typeof config.interrupt_on === 'object' && !Array.isArray(config.interrupt_on)
      ? (config.interrupt_on as Record<string, unknown>)
      : {}

  const rules = Object.entries(interruptOn).map(([toolName, value]) => {
    if (value === false) {
      return {
        ...emptyInterruptRule(),
        toolName,
        enabled: false,
        advanced: false,
      }
    }
    if (value === true) {
      return {
        ...emptyInterruptRule(),
        toolName,
        enabled: true,
        advanced: false,
      }
    }
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      const detail = value as Record<string, unknown>
      const decisions = Array.isArray(detail.allowed_decisions)
        ? detail.allowed_decisions.filter(
            (item): item is string =>
              typeof item === 'string' && (item === 'approve' || item === 'reject'),
          )
        : ['approve', 'reject']
      return {
        toolName,
        enabled: true,
        advanced: true,
        allowedDecisions: decisions.length > 0 ? decisions : ['approve', 'reject'],
      }
    }
    return {
      ...emptyInterruptRule(),
      toolName,
      enabled: true,
    }
  })

  next.interruptRules = rules.length > 0 ? rules : [emptyInterruptRule()]
  return next
}

function ThresholdInputs({
  condition,
  onChange,
  showRemove,
  onRemove,
}: {
  condition: ThresholdCondition
  onChange: (next: ThresholdCondition) => void
  showRemove?: boolean
  onRemove?: () => void
}) {
  const meta = THRESHOLD_KINDS.find((item) => item.value === condition.kind)
  return (
    <div className="middleware-condition-row">
      <label className="library-field">
        <span>阈值类型</span>
        <select
          value={condition.kind}
          onChange={(event) =>
            onChange({ ...condition, kind: event.target.value as ThresholdKind, value: '' })
          }
        >
          {THRESHOLD_KINDS.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </label>
      <label className="library-field">
        <span>阈值 {meta ? `（${meta.hint}）` : ''}</span>
        <input
          type="number"
          required
          min={0}
          max={condition.kind === 'fraction' ? 1 : undefined}
          step={condition.kind === 'fraction' ? '0.01' : '1'}
          value={condition.value}
          placeholder={condition.kind === 'fraction' ? '如 0.8' : '如 4000'}
          onChange={(event) => onChange({ ...condition, value: event.target.value })}
        />
      </label>
      {showRemove && (
        <button
          type="button"
          className="library-action-btn library-action-btn--danger"
          onClick={onRemove}
        >
          删除
        </button>
      )}
    </div>
  )
}

export default function MiddlewarePage() {
  const navigate = useNavigate()
  const [middlewares, setMiddlewares] = useState<Middleware[]>([])
  const [models, setModels] = useState<Model[]>([])
  const [tools, setTools] = useState<Tool[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [formMode, setFormMode] = useState<FormMode>('create')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<FormState>(emptyForm)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [previewItem, setPreviewItem] = useState<Middleware | null>(null)

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
    setLoading(true)
    setError(null)
    try {
      const [middlewareList, modelList, toolList] = await Promise.all([
        getMiddlewareList(),
        getModelList(),
        getToolList(),
      ])
      setMiddlewares(middlewareList)
      setModels(modelList)
      setTools(toolList.filter((tool) => tool.enabled))
    } catch (err) {
      handleApiError(err, '加载中间件列表失败')
    } finally {
      setLoading(false)
    }
  }, [handleApiError])

  useEffect(() => {
    void loadData()
  }, [loadData])

  function openCreateForm() {
    setFormMode('create')
    setEditingId(null)
    setForm({
      ...emptyForm,
      anyTriggers: [emptyCondition('tokens', '3000'), emptyCondition('messages', '20')],
      groupTriggers: [
        { tokens: '5000', messages: '3', fraction: '' },
        { tokens: '3000', messages: '6', fraction: '' },
      ],
      interruptRules: [emptyInterruptRule()],
    })
    setShowForm(true)
    setError(null)
  }

  function openEditForm(item: Middleware) {
    setFormMode('edit')
    setEditingId(item.id)
    setForm(formFromMiddleware(item))
    setShowForm(true)
    setError(null)
  }

  function closeForm() {
    setShowForm(false)
    setEditingId(null)
    setForm(emptyForm)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      const config = buildConfig(form)
      const label = form.label.trim()
      if (!label) {
        throw new Error('请填写显示名称')
      }
      if (formMode === 'create') {
        await createMiddleware({ label, type: form.type, config })
      } else if (editingId) {
        await updateMiddleware({ id: editingId, label, type: form.type, config })
      }
      closeForm()
      await loadData()
    } catch (err) {
      if (err instanceof Error && !(err instanceof ApiError)) {
        setError(err.message)
      } else {
        handleApiError(err, formMode === 'create' ? '创建中间件失败' : '更新中间件失败')
      }
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(item: Middleware) {
    const confirmed = window.confirm(
      `确定删除中间件「${item.label || middlewareTypeDesc(item.type)}」吗？此操作不可恢复。`,
    )
    if (!confirmed) {
      return
    }

    setDeletingId(item.id)
    setError(null)

    try {
      await deleteMiddleware(item.id)
      await loadData()
    } catch (err) {
      handleApiError(err, '删除中间件失败')
    } finally {
      setDeletingId(null)
    }
  }

  function updateInterruptRule(index: number, patch: Partial<InterruptRule>) {
    setForm((prev) => ({
      ...prev,
      interruptRules: prev.interruptRules.map((rule, i) =>
        i === index ? { ...rule, ...patch } : rule,
      ),
    }))
  }

  function toggleDecision(index: number, decision: string, checked: boolean) {
    setForm((prev) => ({
      ...prev,
      interruptRules: prev.interruptRules.map((rule, i) => {
        if (i !== index) {
          return rule
        }
        const next = checked
          ? rule.allowedDecisions.includes(decision)
            ? rule.allowedDecisions
            : [...rule.allowedDecisions, decision]
          : rule.allowedDecisions.filter((item) => item !== decision)
        return { ...rule, allowedDecisions: next }
      }),
    }))
  }

  return (
    <div className="library-page middleware-page">
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
            <p className="brand-eyebrow">Middleware</p>
            <h1 className="library-title">中间件管理</h1>
          </div>
        </div>
        <button type="button" className="library-create-btn" onClick={openCreateForm}>
          + 新建中间件
        </button>
      </header>

      <main className="library-main">
        {error && !showForm && (
          <div className="library-alert" role="alert">
            {error}
          </div>
        )}

        {loading ? (
          <div className="library-empty">加载中…</div>
        ) : middlewares.length === 0 ? (
          <div className="library-empty">
            <p>还没有中间件</p>
            <button type="button" className="library-create-btn" onClick={openCreateForm}>
              创建第一个中间件
            </button>
          </div>
        ) : (
          <section className="library-grid">
            {middlewares.map((item) => (
              <article key={item.id} className="library-card">
                <div className="library-card-head">
                  <div className="library-card-icon library-card-icon--placeholder">
                    {(item.label || 'M').slice(0, 1).toUpperCase()}
                  </div>
                  <div className="library-card-meta">
                    <h2 className="library-card-title">{item.label || '未命名中间件'}</h2>
                    <p className="library-card-desc">{middlewareTypeDesc(item.type)}</p>
                  </div>
                </div>

                <dl className="library-card-info">
                  <div>
                    <dt>更新时间</dt>
                    <dd>{formatDate(item.updateAt)}</dd>
                  </div>
                </dl>

                <div className="library-card-actions">
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
                    onClick={() => void handleDelete(item)}
                    disabled={deletingId === item.id}
                  >
                    {deletingId === item.id ? '删除中…' : '删除'}
                  </button>
                </div>
              </article>
            ))}
          </section>
        )}
      </main>

      {previewItem && (
        <div className="library-modal-overlay" onClick={() => setPreviewItem(null)}>
          <div
            className="library-modal middleware-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="middleware-json-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="library-modal-header">
              <h2 id="middleware-json-title">配置预览</h2>
              <button
                type="button"
                className="library-modal-close"
                onClick={() => setPreviewItem(null)}
              >
                ×
              </button>
            </div>

            <div className="middleware-json-meta">
              <p className="middleware-json-label">{previewItem.label || '未命名中间件'}</p>
              <p className="middleware-json-desc">{middlewareTypeDesc(previewItem.type)}</p>
            </div>

            <div className="middleware-json-result">
              <div className="middleware-json-result-head">config</div>
              <pre>{JSON.stringify(previewItem.config ?? {}, null, 2)}</pre>
            </div>

            <div className="library-form-actions">
              <button
                type="button"
                className="library-action-btn library-action-btn--secondary"
                onClick={() => setPreviewItem(null)}
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}

      {showForm && (
        <div className="library-modal-overlay" onClick={closeForm}>
          <div
            className="library-modal middleware-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="middleware-form-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="library-modal-header">
              <h2 id="middleware-form-title">
                {formMode === 'create' ? '新建中间件' : '编辑中间件'}
              </h2>
              <button type="button" className="library-modal-close" onClick={closeForm}>
                ×
              </button>
            </div>

            {error && (
              <div className="library-alert" role="alert">
                {error}
              </div>
            )}

            <form className="library-form" onSubmit={(event) => void handleSubmit(event)}>
              <label className="library-field">
                <span>显示名称</span>
                <input
                  value={form.label}
                  maxLength={255}
                  required
                  placeholder="如 默认摘要中间件"
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, label: event.target.value }))
                  }
                />
              </label>

              <div className="library-field">
                <span>中间件类型</span>
                <div className="middleware-type-tabs">
                  <button
                    type="button"
                    className={`middleware-type-tab ${form.type === 0 ? 'middleware-type-tab--active' : ''}`}
                    disabled={formMode === 'edit'}
                    onClick={() => setForm((prev) => ({ ...prev, type: 0 }))}
                  >
                    <strong>SummarizationMiddleware</strong>
                    <span>根据 trigger 触发摘要，按 keep 保留上下文</span>
                  </button>
                  <button
                    type="button"
                    className={`middleware-type-tab ${form.type === 1 ? 'middleware-type-tab--active' : ''}`}
                    disabled={formMode === 'edit'}
                    onClick={() => setForm((prev) => ({ ...prev, type: 1 }))}
                  >
                    <strong>HumanInTheLoopMiddleware</strong>
                    <span>指定工具调用前人工审批</span>
                  </button>
                </div>
              </div>

              {form.type === 0 ? (
                <>
                  <label className="library-field">
                    <span>摘要模型</span>
                    {models.length === 0 ? (
                      <p className="middleware-hint">
                        暂无模型，请先去 <Link to="/model">模型管理</Link> 创建
                      </p>
                    ) : (
                      <select
                        required
                        value={form.modelId}
                        onChange={(event) =>
                          setForm((prev) => ({ ...prev, modelId: event.target.value }))
                        }
                      >
                        <option value="">请选择模型</option>
                        {models.map((model) => (
                          <option key={model.id} value={model.id}>
                            {model.label}（{model.name}）
                          </option>
                        ))}
                      </select>
                    )}
                  </label>

                  <section className="middleware-section">
                    <div className="middleware-section-head">
                      <div>
                        <h3>Trigger（触发条件）</h3>
                        <p className="middleware-hint">
                          满足条件时触发摘要生成。支持单一条件、多条件任一满足，或条件组（组内
                          AND，组间 OR）。
                        </p>
                      </div>
                    </div>

                    <div className="middleware-mode-row">
                      {TRIGGER_MODES.map((mode) => (
                        <button
                          key={mode.value}
                          type="button"
                          className={`middleware-mode-chip ${
                            form.triggerMode === mode.value ? 'middleware-mode-chip--active' : ''
                          }`}
                          onClick={() => setForm((prev) => ({ ...prev, triggerMode: mode.value }))}
                          title={mode.desc}
                        >
                          {mode.label}
                        </button>
                      ))}
                    </div>

                    {form.triggerMode === 'single' && (
                      <ThresholdInputs
                        condition={form.singleTrigger}
                        onChange={(singleTrigger) =>
                          setForm((prev) => ({ ...prev, singleTrigger }))
                        }
                      />
                    )}

                    {form.triggerMode === 'any' && (
                      <div className="middleware-condition-list">
                        {form.anyTriggers.map((condition, index) => (
                          <div key={index} className="middleware-condition-item">
                            <div className="middleware-item-head">
                              <strong>条件 {index + 1}</strong>
                              {form.anyTriggers.length > 1 && (
                                <button
                                  type="button"
                                  className="library-action-btn library-action-btn--danger"
                                  onClick={() =>
                                    setForm((prev) => ({
                                      ...prev,
                                      anyTriggers: prev.anyTriggers.filter((_, i) => i !== index),
                                    }))
                                  }
                                >
                                  删除
                                </button>
                              )}
                            </div>
                            <ThresholdInputs
                              condition={condition}
                              onChange={(next) =>
                                setForm((prev) => ({
                                  ...prev,
                                  anyTriggers: prev.anyTriggers.map((item, i) =>
                                    i === index ? next : item,
                                  ),
                                }))
                              }
                            />
                          </div>
                        ))}
                        <button
                          type="button"
                          className="library-action-btn library-action-btn--secondary"
                          onClick={() =>
                            setForm((prev) => ({
                              ...prev,
                              anyTriggers: [...prev.anyTriggers, emptyCondition('messages', '20')],
                            }))
                          }
                        >
                          + 添加条件
                        </button>
                      </div>
                    )}

                    {form.triggerMode === 'group' && (
                      <div className="middleware-group-list">
                        {form.groupTriggers.map((group, index) => (
                          <div key={index} className="middleware-group-item">
                            <div className="middleware-item-head">
                              <strong>条件组 {index + 1}（组内同时满足）</strong>
                              {form.groupTriggers.length > 1 && (
                                <button
                                  type="button"
                                  className="library-action-btn library-action-btn--danger"
                                  onClick={() =>
                                    setForm((prev) => ({
                                      ...prev,
                                      groupTriggers: prev.groupTriggers.filter(
                                        (_, i) => i !== index,
                                      ),
                                    }))
                                  }
                                >
                                  删除
                                </button>
                              )}
                            </div>
                            <div className="middleware-group-metrics">
                              <label className="library-field">
                                <span>tokens</span>
                                <input
                                  type="number"
                                  min={0}
                                  step={1}
                                  value={group.tokens}
                                  placeholder="可选"
                                  onChange={(event) =>
                                    setForm((prev) => ({
                                      ...prev,
                                      groupTriggers: prev.groupTriggers.map((item, i) =>
                                        i === index
                                          ? { ...item, tokens: event.target.value }
                                          : item,
                                      ),
                                    }))
                                  }
                                />
                              </label>
                              <label className="library-field">
                                <span>messages</span>
                                <input
                                  type="number"
                                  min={0}
                                  step={1}
                                  value={group.messages}
                                  placeholder="可选"
                                  onChange={(event) =>
                                    setForm((prev) => ({
                                      ...prev,
                                      groupTriggers: prev.groupTriggers.map((item, i) =>
                                        i === index
                                          ? { ...item, messages: event.target.value }
                                          : item,
                                      ),
                                    }))
                                  }
                                />
                              </label>
                              <label className="library-field">
                                <span>fraction</span>
                                <input
                                  type="number"
                                  min={0}
                                  max={1}
                                  step="0.01"
                                  value={group.fraction}
                                  placeholder="可选 0~1"
                                  onChange={(event) =>
                                    setForm((prev) => ({
                                      ...prev,
                                      groupTriggers: prev.groupTriggers.map((item, i) =>
                                        i === index
                                          ? { ...item, fraction: event.target.value }
                                          : item,
                                      ),
                                    }))
                                  }
                                />
                              </label>
                            </div>
                          </div>
                        ))}
                        <button
                          type="button"
                          className="library-action-btn library-action-btn--secondary"
                          onClick={() =>
                            setForm((prev) => ({
                              ...prev,
                              groupTriggers: [...prev.groupTriggers, emptyGroup()],
                            }))
                          }
                        >
                          + 添加条件组
                        </button>
                      </div>
                    )}
                  </section>

                  <section className="middleware-section">
                    <div className="middleware-section-head">
                      <div>
                        <h3>Keep（保留上下文）</h3>
                        <p className="middleware-hint">
                          摘要生成后需要保留的上下文数量，支持 tokens / messages / fraction。
                        </p>
                      </div>
                    </div>
                    <ThresholdInputs
                      condition={form.keep}
                      onChange={(keep) => setForm((prev) => ({ ...prev, keep }))}
                    />
                  </section>
                </>
              ) : (
                <>
                  <label className="library-field">
                    <span>工具拦截提示前缀</span>
                    <input
                      value={form.descriptionPrefix}
                      maxLength={255}
                      placeholder="Tool execution pending approval"
                      onChange={(event) =>
                        setForm((prev) => ({ ...prev, descriptionPrefix: event.target.value }))
                      }
                    />
                  </label>

                  <section className="middleware-section">
                    <div className="middleware-section-head">
                      <div>
                        <h3>interrupt_on</h3>
                        <p className="middleware-hint">
                          配置需要人工审批的工具。可直接开关，或展开高级配置 allowed_decisions。
                        </p>
                      </div>
                    </div>

                    <div className="middleware-interrupt-list">
                      {form.interruptRules.map((rule, index) => (
                        <div key={index} className="middleware-interrupt-item">
                          <div className="middleware-item-head">
                            <strong>工具规则 {index + 1}</strong>
                            {form.interruptRules.length > 1 && (
                              <button
                                type="button"
                                className="library-action-btn library-action-btn--danger"
                                onClick={() =>
                                  setForm((prev) => ({
                                    ...prev,
                                    interruptRules: prev.interruptRules.filter(
                                      (_, i) => i !== index,
                                    ),
                                  }))
                                }
                              >
                                删除
                              </button>
                            )}
                          </div>

                          <label className="library-field">
                            <span>工具</span>
                            {tools.length === 0 ? (
                              <p className="middleware-hint">
                                暂无可用工具，请先去 <Link to="/tool">API 工具</Link> 创建
                              </p>
                            ) : (
                              <select
                                required
                                value={rule.toolName}
                                onChange={(event) =>
                                  updateInterruptRule(index, { toolName: event.target.value })
                                }
                              >
                                <option value="">请选择工具</option>
                                {tools.map((tool) => (
                                  <option
                                    key={tool.id}
                                    value={tool.name}
                                    disabled={form.interruptRules.some(
                                      (other, otherIndex) =>
                                        otherIndex !== index && other.toolName === tool.name,
                                    )}
                                  >
                                    {tool.label}（{tool.name}）
                                  </option>
                                ))}
                                {rule.toolName &&
                                  !tools.some((tool) => tool.name === rule.toolName) && (
                                    <option value={rule.toolName}>{rule.toolName}（已失效）</option>
                                  )}
                              </select>
                            )}
                          </label>

                          <div className="middleware-inline-checks">
                            <label>
                              <input
                                type="checkbox"
                                checked={rule.enabled}
                                onChange={(event) =>
                                  updateInterruptRule(index, { enabled: event.target.checked })
                                }
                              />
                              启用中断（false 表示跳过）
                            </label>
                            <label>
                              <input
                                type="checkbox"
                                checked={rule.advanced}
                                disabled={!rule.enabled}
                                onChange={(event) =>
                                  updateInterruptRule(index, { advanced: event.target.checked })
                                }
                              />
                              高级配置
                            </label>
                          </div>

                          {rule.enabled && rule.advanced && (
                            <div className="library-field">
                              <span>allowed_decisions</span>
                              <div className="middleware-inline-checks">
                                {DECISION_OPTIONS.map((decision) => (
                                  <label key={decision}>
                                    <input
                                      type="checkbox"
                                      checked={rule.allowedDecisions.includes(decision)}
                                      onChange={(event) =>
                                        toggleDecision(index, decision, event.target.checked)
                                      }
                                    />
                                    {decision}
                                  </label>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>

                    <button
                      type="button"
                      className="library-action-btn library-action-btn--secondary"
                      onClick={() =>
                        setForm((prev) => ({
                          ...prev,
                          interruptRules: [...prev.interruptRules, emptyInterruptRule()],
                        }))
                      }
                      disabled={tools.length === 0}
                    >
                      + 添加工具规则
                    </button>
                  </section>
                </>
              )}

              <div className="library-form-actions">
                <button
                  type="button"
                  className="library-action-btn library-action-btn--secondary"
                  onClick={closeForm}
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="library-create-btn"
                  disabled={
                    submitting ||
                    (form.type === 0 && models.length === 0) ||
                    (form.type === 1 && tools.length === 0)
                  }
                >
                  {submitting ? '提交中…' : formMode === 'create' ? '创建' : '保存'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
