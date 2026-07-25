import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import {
  createLibrary,
  deleteLibrary,
  getLibraryList,
  updateLibrary,
  type Library,
} from '../api/library'
import '../styles/common.css'
import './LibraryPage.css'

type FormMode = 'create' | 'edit'

interface LibraryFormState {
  name: string
  desc: string
  icon: string
}

const emptyForm: LibraryFormState = {
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

export default function LibraryPage() {
  const navigate = useNavigate()
  const [libraries, setLibraries] = useState<Library[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formMode, setFormMode] = useState<FormMode | null>(null)
  const [editingLibrary, setEditingLibrary] = useState<Library | null>(null)
  const [form, setForm] = useState<LibraryFormState>(emptyForm)
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

  const loadLibraries = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getLibraryList()
      setLibraries(data)
    } catch (err) {
      handleApiError(err, '加载知识库列表失败')
    } finally {
      setLoading(false)
    }
  }, [handleApiError])

  useEffect(() => {
    void loadLibraries()
  }, [loadLibraries])

  function openCreateForm() {
    setFormMode('create')
    setEditingLibrary(null)
    setForm(emptyForm)
    setError(null)
  }

  function openEditForm(library: Library) {
    setFormMode('edit')
    setEditingLibrary(library)
    setForm({
      name: library.name,
      desc: library.desc,
      icon: library.icon ?? '',
    })
    setError(null)
  }

  function closeForm() {
    setFormMode(null)
    setEditingLibrary(null)
    setForm(emptyForm)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)

    const payload = {
      name: form.name.trim(),
      desc: form.desc.trim(),
      icon: form.icon.trim() || undefined,
    }

    try {
      if (formMode === 'create') {
        await createLibrary(payload)
      } else if (formMode === 'edit' && editingLibrary) {
        await updateLibrary({
          id: editingLibrary.id,
          ...payload,
        })
      }
      closeForm()
      await loadLibraries()
    } catch (err) {
      handleApiError(err, '保存知识库失败')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(library: Library) {
    const confirmed = window.confirm(`确定删除知识库「${library.name}」吗？此操作不可恢复。`)
    if (!confirmed) {
      return
    }

    setDeletingId(library.id)
    setError(null)

    try {
      await deleteLibrary(library.id)
      await loadLibraries()
    } catch (err) {
      handleApiError(err, '删除知识库失败')
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
          <Link to="/" className="library-back-link">
            ← 返回首页
          </Link>
          <div>
            <p className="brand-eyebrow">Knowledge Base</p>
            <h1 className="library-title">知识库管理</h1>
          </div>
        </div>
        <button type="button" className="library-create-btn" onClick={openCreateForm}>
          + 新建知识库
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
        ) : libraries.length === 0 ? (
          <div className="library-empty">
            <p>还没有知识库</p>
            <button type="button" className="library-create-btn" onClick={openCreateForm}>
              创建第一个知识库
            </button>
          </div>
        ) : (
          <section className="library-grid">
            {libraries.map((library) => (
              <article key={library.id} className="library-card">
                <div className="library-card-head">
                  {library.icon ? (
                    <img src={library.icon} alt="" className="library-card-icon" />
                  ) : (
                    <div className="library-card-icon library-card-icon--placeholder">
                      {library.name.slice(0, 1).toUpperCase()}
                    </div>
                  )}
                  <div className="library-card-meta">
                    <h2 className="library-card-title">{library.name}</h2>
                    <p className="library-card-desc">{library.desc}</p>
                  </div>
                </div>

                <dl className="library-card-info">
                  <div>
                    <dt>创建时间</dt>
                    <dd>{formatDate(library.createAt)}</dd>
                  </div>
                  <div>
                    <dt>更新时间</dt>
                    <dd>{formatDate(library.updateAt)}</dd>
                  </div>
                </dl>

                <div className="library-card-actions">
                  <Link
                    to={`/library/documents?library_id=${encodeURIComponent(library.id)}&library_name=${encodeURIComponent(library.name)}`}
                    className="library-action-btn library-action-btn--primary"
                  >
                    文档
                  </Link>
                  <button
                    type="button"
                    className="library-action-btn library-action-btn--secondary"
                    onClick={() => openEditForm(library)}
                  >
                    编辑
                  </button>
                  <button
                    type="button"
                    className="library-action-btn library-action-btn--danger"
                    onClick={() => void handleDelete(library)}
                    disabled={deletingId === library.id}
                  >
                    {deletingId === library.id ? '删除中…' : '删除'}
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
            className="library-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="library-form-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="library-modal-header">
              <h2 id="library-form-title">
                {formMode === 'create' ? '新建知识库' : '编辑知识库'}
              </h2>
              <button type="button" className="library-modal-close" onClick={closeForm}>
                ×
              </button>
            </div>

            <form className="library-form" onSubmit={(event) => void handleSubmit(event)}>
              <label className="library-field">
                <span>名称</span>
                <input
                  type="text"
                  value={form.name}
                  maxLength={100}
                  required
                  placeholder="例如：产品文档库"
                  onChange={(event) => setForm({ ...form, name: event.target.value })}
                />
              </label>

              <label className="library-field">
                <span>描述</span>
                <textarea
                  value={form.desc}
                  maxLength={50}
                  required
                  rows={3}
                  placeholder="简要描述知识库用途"
                  onChange={(event) => setForm({ ...form, desc: event.target.value })}
                />
              </label>

              <label className="library-field">
                <span>图标 URL（可选）</span>
                <input
                  type="url"
                  value={form.icon}
                  maxLength={255}
                  placeholder="https://example.com/icon.png"
                  onChange={(event) => setForm({ ...form, icon: event.target.value })}
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
                  {submitting ? '保存中…' : '保存'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
