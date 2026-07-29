import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import {
  createModel,
  deleteModel,
  getModelList,
  updateModel,
  type Model,
} from '../api/model'
import '../styles/common.css'
import './LibraryPage.css'

type FormMode = 'create' | 'edit'

interface ModelFormState {
  name: string
  label: string
  desc: string
  apiKey: string
  baseUrl: string
  icon: string
}

const emptyForm: ModelFormState = {
  name: '',
  label: '',
  desc: '',
  apiKey: '',
  baseUrl: '',
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

export default function ModelPage() {
  const navigate = useNavigate()
  const [models, setModels] = useState<Model[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [formMode, setFormMode] = useState<FormMode>('create')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<ModelFormState>(emptyForm)
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

  const loadModels = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getModelList()
      setModels(data)
    } catch (err) {
      handleApiError(err, '加载模型列表失败')
    } finally {
      setLoading(false)
    }
  }, [handleApiError])

  useEffect(() => {
    void loadModels()
  }, [loadModels])

  function openCreateForm() {
    setFormMode('create')
    setEditingId(null)
    setForm(emptyForm)
    setShowForm(true)
    setError(null)
  }

  function openEditForm(model: Model) {
    setFormMode('edit')
    setEditingId(model.id)
    setForm({
      name: model.name,
      label: model.label,
      desc: model.desc,
      apiKey: model.apiKey,
      baseUrl: model.baseUrl,
      icon: model.icon ?? '',
    })
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
      if (formMode === 'create') {
        await createModel({
          name: form.name.trim(),
          label: form.label.trim(),
          desc: form.desc.trim(),
          api_key: form.apiKey.trim(),
          base_url: form.baseUrl.trim(),
          icon: form.icon.trim() || undefined,
        })
      } else if (editingId) {
        await updateModel({
          id: editingId,
          name: form.name.trim(),
          label: form.label.trim(),
          desc: form.desc.trim(),
          api_key: form.apiKey.trim(),
          base_url: form.baseUrl.trim(),
          icon: form.icon.trim() || undefined,
        })
      }
      closeForm()
      await loadModels()
    } catch (err) {
      handleApiError(err, formMode === 'create' ? '创建模型失败' : '更新模型失败')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(model: Model) {
    const confirmed = window.confirm(`确定删除模型「${model.label}」吗？此操作不可恢复。`)
    if (!confirmed) {
      return
    }

    setDeletingId(model.id)
    setError(null)

    try {
      await deleteModel(model.id)
      await loadModels()
    } catch (err) {
      handleApiError(err, '删除模型失败')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="library-page">
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
            <p className="brand-eyebrow">Models</p>
            <h1 className="library-title">模型管理</h1>
          </div>
        </div>
        <button type="button" className="library-create-btn" onClick={openCreateForm}>
          + 新建模型
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
        ) : models.length === 0 ? (
          <div className="library-empty">
            <p>还没有模型</p>
            <button type="button" className="library-create-btn" onClick={openCreateForm}>
              创建第一个模型
            </button>
          </div>
        ) : (
          <section className="library-grid">
            {models.map((model) => (
              <article key={model.id} className="library-card">
                <div className="library-card-head">
                  {model.icon ? (
                    <img src={model.icon} alt="" className="library-card-icon" />
                  ) : (
                    <div className="library-card-icon library-card-icon--placeholder">
                      {model.label.slice(0, 1).toUpperCase()}
                    </div>
                  )}
                  <div className="library-card-meta">
                    <h2 className="library-card-title">{model.label}</h2>
                    <p className="library-card-desc">{model.desc}</p>
                  </div>
                </div>

                <dl className="library-card-info">
                  <div>
                    <dt>模型名称</dt>
                    <dd>{model.name}</dd>
                  </div>
                  <div>
                    <dt>更新时间</dt>
                    <dd>{formatDate(model.updateAt)}</dd>
                  </div>
                </dl>

                <div className="library-card-actions">
                  <button
                    type="button"
                    className="library-action-btn library-action-btn--primary"
                    onClick={() => openEditForm(model)}
                  >
                    编辑
                  </button>
                  <button
                    type="button"
                    className="library-action-btn library-action-btn--danger"
                    onClick={() => void handleDelete(model)}
                    disabled={deletingId === model.id}
                  >
                    {deletingId === model.id ? '删除中…' : '删除'}
                  </button>
                </div>
              </article>
            ))}
          </section>
        )}
      </main>

      {showForm && (
        <div className="library-modal-overlay" onClick={closeForm}>
          <div
            className="library-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="model-form-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="library-modal-header">
              <h2 id="model-form-title">{formMode === 'create' ? '新建模型' : '编辑模型'}</h2>
              <button type="button" className="library-modal-close" onClick={closeForm}>
                ×
              </button>
            </div>

            <form className="library-form" onSubmit={(event) => void handleSubmit(event)}>
              <label className="library-field">
                <span>显示名称</span>
                <input
                  value={form.label}
                  maxLength={100}
                  required
                  placeholder="如 GPT-4o"
                  onChange={(event) => setForm((prev) => ({ ...prev, label: event.target.value }))}
                />
              </label>

              <label className="library-field">
                <span>模型名称</span>
                <input
                  value={form.name}
                  maxLength={100}
                  required
                  placeholder="如 gpt-4o"
                  onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
                />
              </label>

              <label className="library-field">
                <span>调用地址</span>
                <input
                  value={form.baseUrl}
                  maxLength={255}
                  required
                  placeholder="如 https://api.openai.com/v1"
                  onChange={(event) => setForm((prev) => ({ ...prev, baseUrl: event.target.value }))}
                />
              </label>

              <label className="library-field">
                <span>API Key</span>
                <input
                  value={form.apiKey}
                  maxLength={512}
                  required
                  type="password"
                  autoComplete="off"
                  placeholder="模型服务的 API Key"
                  onChange={(event) => setForm((prev) => ({ ...prev, apiKey: event.target.value }))}
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
                  placeholder="简要描述这个模型"
                  onChange={(event) => setForm((prev) => ({ ...prev, desc: event.target.value }))}
                />
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
