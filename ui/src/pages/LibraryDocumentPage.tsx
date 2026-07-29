import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { uploadFileToCos } from '../api/file'
import { ApiError } from '../api/client'
import {
  addDocument,
  deleteChunk,
  deleteDocument,
  downloadDocument,
  getChunkList,
  getDocumentList,
  parseDocument,
  updateChunk,
  type Chunk,
  type Document,
  type DocumentStatus,
  type SplitterType,
} from '../api/library'
import '../styles/common.css'
import './LibraryDocumentPage.css'

const ALLOWED_EXTENSIONS = ['pdf', 'doc', 'docx', 'txt', 'md']

const DOCUMENT_STATUS_LABEL: Record<DocumentStatus, string> = {
  0: '未处理',
  1: '加载中',
  2: '清洗中',
  3: '分割中',
  4: '已完成',
}

const DEFAULT_CHUNK_SIZE = 1000
const DEFAULT_CHUNK_OVERLAP = 200

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

function getDisplayFileName(document: Document) {
  return `${document.fileName}.${document.fileExt}`
}

function resolveDefaultSplitter(fileExt: string): SplitterType {
  const ext = fileExt.replace(/^\./, '').toLowerCase()
  return ext === 'md' || ext === 'markdown' ? 'md' : 'default'
}

async function sha256Hex(content: string) {
  const data = new TextEncoder().encode(content)
  const digest = await crypto.subtle.digest('SHA-256', data)
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('')
}

function previewContent(content: string, max = 120) {
  const normalized = content.replace(/\s+/g, ' ').trim()
  if (normalized.length <= max) {
    return normalized
  }
  return `${normalized.slice(0, max)}…`
}

export default function LibraryDocumentPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const libraryId = searchParams.get('library_id') ?? ''
  const libraryName = searchParams.get('library_name')

  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [showUploadForm, setShowUploadForm] = useState(false)
  const [desc, setDesc] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [downloadingId, setDownloadingId] = useState<string | null>(null)

  const [parsingDocument, setParsingDocument] = useState<Document | null>(null)
  const [splitterType, setSplitterType] = useState<SplitterType>('default')
  const [chunkSize, setChunkSize] = useState(String(DEFAULT_CHUNK_SIZE))
  const [chunkOverlap, setChunkOverlap] = useState(String(DEFAULT_CHUNK_OVERLAP))
  const [parsing, setParsing] = useState(false)

  const [chunkDocument, setChunkDocument] = useState<Document | null>(null)
  const [chunks, setChunks] = useState<Chunk[]>([])
  const [chunksLoading, setChunksLoading] = useState(false)
  const [chunkError, setChunkError] = useState<string | null>(null)
  const [editingChunk, setEditingChunk] = useState<Chunk | null>(null)
  const [editContent, setEditContent] = useState('')
  const [chunkSaving, setChunkSaving] = useState(false)
  const [chunkActionId, setChunkActionId] = useState<string | null>(null)

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

  const handleChunkApiError = useCallback(
    (err: unknown, fallback: string) => {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          navigate('/login')
          return
        }
        setChunkError(err.message)
        return
      }
      setChunkError(err instanceof Error ? err.message : fallback)
    },
    [navigate],
  )

  const loadDocuments = useCallback(async () => {
    if (!libraryId) {
      return
    }

    setLoading(true)
    setError(null)
    try {
      const data = await getDocumentList(libraryId)
      setDocuments(data)
    } catch (err) {
      handleApiError(err, '加载文档列表失败')
    } finally {
      setLoading(false)
    }
  }, [handleApiError, libraryId])

  const loadChunks = useCallback(
    async (documentId: string) => {
      setChunksLoading(true)
      setChunkError(null)
      try {
        const data = await getChunkList(documentId)
        setChunks(data)
      } catch (err) {
        handleChunkApiError(err, '加载分片列表失败')
      } finally {
        setChunksLoading(false)
      }
    },
    [handleChunkApiError],
  )

  useEffect(() => {
    if (!libraryId) {
      navigate('/admin/library', { replace: true })
      return
    }
    void loadDocuments()
  }, [libraryId, loadDocuments, navigate])

  function openUploadForm() {
    setShowUploadForm(true)
    setDesc('')
    setSelectedFile(null)
    setError(null)
    setSuccess(null)
  }

  function closeUploadForm() {
    setShowUploadForm(false)
    setDesc('')
    setSelectedFile(null)
  }

  function openParseForm(document: Document) {
    setParsingDocument(document)
    setSplitterType(resolveDefaultSplitter(document.fileExt))
    setChunkSize(String(DEFAULT_CHUNK_SIZE))
    setChunkOverlap(String(DEFAULT_CHUNK_OVERLAP))
    setError(null)
    setSuccess(null)
  }

  function closeParseForm() {
    setParsingDocument(null)
    setParsing(false)
  }

  function openChunkPanel(document: Document) {
    setChunkDocument(document)
    setChunks([])
    setEditingChunk(null)
    setEditContent('')
    setChunkError(null)
    setError(null)
    setSuccess(null)
    void loadChunks(document.id)
  }

  function closeChunkPanel() {
    setChunkDocument(null)
    setChunks([])
    setEditingChunk(null)
    setEditContent('')
    setChunkError(null)
    setChunkActionId(null)
  }

  function openEditChunk(chunk: Chunk) {
    setEditingChunk(chunk)
    setEditContent(chunk.content)
    setChunkError(null)
  }

  function closeEditChunk() {
    setEditingChunk(null)
    setEditContent('')
  }

  function handleFileChange(file: File | null) {
    if (!file) {
      setSelectedFile(null)
      return
    }

    const dotIndex = file.name.lastIndexOf('.')
    const ext = dotIndex > 0 ? file.name.slice(dotIndex + 1).toLowerCase() : ''
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setError(`不支持的文件格式，允许：${ALLOWED_EXTENSIONS.join('、')}`)
      setSelectedFile(null)
      return
    }

    setError(null)
    setSelectedFile(file)
    if (!desc.trim()) {
      setDesc(file.name)
    }
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!libraryId || !selectedFile) {
      return
    }

    setSubmitting(true)
    setError(null)
    setSuccess(null)

    try {
      const uploaded = await uploadFileToCos(selectedFile)
      await addDocument({
        library_id: libraryId,
        file_name: uploaded.file_name,
        file_ext: uploaded.file_ext,
        desc: desc.trim(),
        file_key: uploaded.cos_key,
      })
      closeUploadForm()
      await loadDocuments()
    } catch (err) {
      handleApiError(err, '上传文档失败')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(document: Document) {
    const confirmed = window.confirm(`确定删除文档「${getDisplayFileName(document)}」吗？`)
    if (!confirmed) {
      return
    }

    setDeletingId(document.id)
    setError(null)
    setSuccess(null)

    try {
      await deleteDocument(document.id)
      if (chunkDocument?.id === document.id) {
        closeChunkPanel()
      }
      await loadDocuments()
    } catch (err) {
      handleApiError(err, '删除文档失败')
    } finally {
      setDeletingId(null)
    }
  }

  async function handleDownload(doc: Document) {
    setDownloadingId(doc.id)
    setError(null)

    try {
      const result = await downloadDocument(doc.id)
      const link = window.document.createElement('a')
      link.href = result.download_url
      link.download = result.fileName || getDisplayFileName(doc)
      link.rel = 'noopener'
      link.style.display = 'none'
      window.document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      handleApiError(err, '获取下载链接失败')
    } finally {
      setDownloadingId(null)
    }
  }

  async function handleParse(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!parsingDocument) {
      return
    }

    const size = Number(chunkSize)
    const overlap = Number(chunkOverlap)
    if (!Number.isInteger(size) || size <= 0) {
      setError('分块大小必须是正整数')
      return
    }
    if (!Number.isInteger(overlap) || overlap < 0) {
      setError('重叠长度必须是非负整数')
      return
    }
    if (overlap >= size) {
      setError('重叠长度必须小于分块大小')
      return
    }

    setParsing(true)
    setError(null)
    setSuccess(null)

    try {
      const result = await parseDocument({
        id: parsingDocument.id,
        splitter_type: splitterType,
        splitter_params: {
          chunk_size: size,
          chunk_overlap: overlap,
        },
      })
      closeParseForm()
      setSuccess(`已提交解析任务（${result.taskId}）`)
      await loadDocuments()
    } catch (err) {
      handleApiError(err, '提交解析任务失败')
    } finally {
      setParsing(false)
    }
  }

  async function handleToggleChunk(chunk: Chunk) {
    setChunkActionId(chunk.id)
    setChunkError(null)
    try {
      const updated = await updateChunk({
        id: chunk.id,
        enabled: !chunk.enabled,
      })
      setChunks((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
    } catch (err) {
      handleChunkApiError(err, '更新分片状态失败')
    } finally {
      setChunkActionId(null)
    }
  }

  async function handleDeleteChunk(chunk: Chunk) {
    const confirmed = window.confirm(`确定删除分片 #${chunk.position} 吗？`)
    if (!confirmed) {
      return
    }

    setChunkActionId(chunk.id)
    setChunkError(null)
    try {
      await deleteChunk(chunk.id)
      setChunks((prev) => prev.filter((item) => item.id !== chunk.id))
      if (editingChunk?.id === chunk.id) {
        closeEditChunk()
      }
    } catch (err) {
      handleChunkApiError(err, '删除分片失败')
    } finally {
      setChunkActionId(null)
    }
  }

  async function handleSaveChunk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!editingChunk) {
      return
    }

    const content = editContent.trim()
    if (!content) {
      setChunkError('分片内容不能为空')
      return
    }

    setChunkSaving(true)
    setChunkError(null)
    try {
      const hash = await sha256Hex(content)
      const updated = await updateChunk({
        id: editingChunk.id,
        content,
        hash,
      })
      setChunks((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
      closeEditChunk()
    } catch (err) {
      handleChunkApiError(err, '保存分片失败')
    } finally {
      setChunkSaving(false)
    }
  }

  return (
    <div className="library-page document-page">
      <div className="page-bg" aria-hidden="true">
        <div className="page-bg-glow page-bg-glow--left" />
        <div className="page-bg-glow page-bg-glow--right" />
        <div className="page-bg-grid" />
      </div>

      <header className="library-header">
        <div className="library-header-left">
          <Link to="/admin/library" className="library-back-link">
            ← 返回知识库
          </Link>
          <div>
            <p className="brand-eyebrow">Documents</p>
            <h1 className="library-title">{libraryName ?? '知识库文档'}</h1>
            {libraryName && <p className="document-subtitle">管理该知识库下的文档</p>}
          </div>
        </div>
        <button type="button" className="library-create-btn" onClick={openUploadForm}>
          + 上传文档
        </button>
      </header>

      <main className="library-main">
        {error && (
          <div className="library-alert" role="alert">
            {error}
          </div>
        )}
        {success && (
          <div className="library-alert library-alert--success" role="status">
            {success}
          </div>
        )}

        {loading ? (
          <div className="library-empty">加载中…</div>
        ) : documents.length === 0 ? (
          <div className="library-empty">
            <p>还没有文档</p>
            <button type="button" className="library-create-btn" onClick={openUploadForm}>
              上传第一个文档
            </button>
          </div>
        ) : (
          <section className="document-table-wrap">
            <table className="document-table">
              <thead>
                <tr>
                  <th>文件名</th>
                  <th>描述</th>
                  <th>状态</th>
                  <th>上传时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((document) => {
                  const status = (document.status ?? 0) as DocumentStatus
                  return (
                    <tr key={document.id}>
                      <td>
                        <div className="document-file-cell">
                          <span className="document-file-ext">{document.fileExt.toUpperCase()}</span>
                          <span>{getDisplayFileName(document)}</span>
                        </div>
                      </td>
                      <td className="document-desc-cell">{document.desc}</td>
                      <td>
                        <span className={`document-status document-status--${status}`}>
                          {DOCUMENT_STATUS_LABEL[status] ?? '未知'}
                        </span>
                      </td>
                      <td>{formatDate(document.createAt)}</td>
                      <td>
                        <div className="document-row-actions">
                          <button
                            type="button"
                            className="library-action-btn"
                            onClick={() => openParseForm(document)}
                            disabled={status > 0 && status < 4}
                          >
                            {status === 4 ? '重新解析' : '解析'}
                          </button>
                          <button
                            type="button"
                            className="library-action-btn library-action-btn--secondary"
                            onClick={() => openChunkPanel(document)}
                          >
                            分片
                          </button>
                          <button
                            type="button"
                            className="library-action-btn library-action-btn--secondary"
                            onClick={() => void handleDownload(document)}
                            disabled={downloadingId === document.id}
                          >
                            {downloadingId === document.id ? '获取中…' : '下载'}
                          </button>
                          <button
                            type="button"
                            className="library-action-btn library-action-btn--danger"
                            onClick={() => void handleDelete(document)}
                            disabled={deletingId === document.id}
                          >
                            {deletingId === document.id ? '删除中…' : '删除'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </section>
        )}
      </main>

      {showUploadForm && (
        <div className="library-modal-overlay" onClick={closeUploadForm}>
          <div
            className="library-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="document-upload-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="library-modal-header">
              <h2 id="document-upload-title">上传文档</h2>
              <button type="button" className="library-modal-close" onClick={closeUploadForm}>
                ×
              </button>
            </div>

            <form className="library-form" onSubmit={(event) => void handleUpload(event)}>
              <label className="library-field">
                <span>选择文件</span>
                <input
                  type="file"
                  accept=".pdf,.doc,.docx,.txt,.md"
                  required
                  onChange={(event) => handleFileChange(event.target.files?.[0] ?? null)}
                />
                <p className="document-upload-hint">
                  支持 pdf、doc、docx、txt、md
                </p>
              </label>

              <label className="library-field">
                <span>描述</span>
                <textarea
                  value={desc}
                  maxLength={255}
                  required
                  rows={3}
                  placeholder="简要描述文档内容"
                  onChange={(event) => setDesc(event.target.value)}
                />
              </label>

              <div className="library-form-actions">
                <button
                  type="button"
                  className="library-action-btn library-action-btn--secondary"
                  onClick={closeUploadForm}
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="library-create-btn"
                  disabled={submitting || !selectedFile}
                >
                  {submitting ? '上传中…' : '确认上传'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {parsingDocument && (
        <div className="library-modal-overlay" onClick={closeParseForm}>
          <div
            className="library-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="document-parse-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="library-modal-header">
              <h2 id="document-parse-title">解析文档</h2>
              <button type="button" className="library-modal-close" onClick={closeParseForm}>
                ×
              </button>
            </div>

            <form className="library-form" onSubmit={(event) => void handleParse(event)}>
              <p className="document-parse-file">
                文件：{getDisplayFileName(parsingDocument)}
              </p>

              <label className="library-field">
                <span>分割器类型</span>
                <select
                  value={splitterType}
                  onChange={(event) => setSplitterType(event.target.value as SplitterType)}
                >
                  <option value="default">默认（Recursive）</option>
                  <option value="md">Markdown</option>
                </select>
              </label>

              <div className="document-parse-params">
                <label className="library-field">
                  <span>分块大小（chunk_size）</span>
                  <input
                    type="number"
                    min={1}
                    step={1}
                    required
                    value={chunkSize}
                    onChange={(event) => setChunkSize(event.target.value)}
                  />
                </label>

                <label className="library-field">
                  <span>重叠长度（chunk_overlap）</span>
                  <input
                    type="number"
                    min={0}
                    step={1}
                    required
                    value={chunkOverlap}
                    onChange={(event) => setChunkOverlap(event.target.value)}
                  />
                </label>
              </div>

              <p className="document-upload-hint">
                提交后将由后台任务异步处理：加载 → 清洗 → 分割 → 入库
              </p>

              <div className="library-form-actions">
                <button
                  type="button"
                  className="library-action-btn library-action-btn--secondary"
                  onClick={closeParseForm}
                >
                  取消
                </button>
                <button type="submit" className="library-create-btn" disabled={parsing}>
                  {parsing ? '提交中…' : '开始解析'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {chunkDocument && (
        <div className="chunk-drawer-overlay" onClick={closeChunkPanel}>
          <aside
            className="chunk-drawer"
            role="dialog"
            aria-modal="true"
            aria-labelledby="document-chunk-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="chunk-drawer-header">
              <div>
                <h2 id="document-chunk-title">文档分片</h2>
                <p className="chunk-drawer-subtitle">{getDisplayFileName(chunkDocument)}</p>
              </div>
              <button type="button" className="library-modal-close" onClick={closeChunkPanel}>
                ×
              </button>
            </div>

            {chunkError && (
              <div className="library-alert" role="alert">
                {chunkError}
              </div>
            )}

            <div className="chunk-drawer-body">
              {editingChunk ? (
                <form className="library-form chunk-inline-edit" onSubmit={(event) => void handleSaveChunk(event)}>
                  <div className="chunk-inline-edit-head">
                    <h3>编辑分片 #{editingChunk.position}</h3>
                    <button type="button" className="library-action-btn library-action-btn--secondary" onClick={closeEditChunk}>
                      返回列表
                    </button>
                  </div>
                  <label className="library-field">
                    <span>分片内容</span>
                    <textarea
                      value={editContent}
                      required
                      rows={14}
                      placeholder="输入分片内容"
                      autoFocus
                      onChange={(event) => setEditContent(event.target.value)}
                    />
                  </label>
                  <div className="library-form-actions">
                    <button
                      type="button"
                      className="library-action-btn library-action-btn--secondary"
                      onClick={closeEditChunk}
                    >
                      取消
                    </button>
                    <button type="submit" className="library-create-btn" disabled={chunkSaving}>
                      {chunkSaving ? '保存中…' : '保存'}
                    </button>
                  </div>
                </form>
              ) : chunksLoading ? (
                <div className="chunk-empty">加载中…</div>
              ) : chunks.length === 0 ? (
                <div className="chunk-empty">暂无分片，请先完成文档解析</div>
              ) : (
                <ul className="chunk-list">
                  {chunks.map((chunk) => (
                    <li key={chunk.id} className="chunk-item">
                      <div className="chunk-item-head">
                        <div className="chunk-item-meta">
                          <span className="chunk-position">#{chunk.position}</span>
                          <span
                            className={`chunk-enabled ${chunk.enabled ? 'chunk-enabled--on' : 'chunk-enabled--off'}`}
                          >
                            {chunk.enabled ? '已启用' : '已禁用'}
                          </span>
                        </div>
                        <div className="chunk-item-actions">
                          <button
                            type="button"
                            className="library-action-btn library-action-btn--secondary"
                            onClick={() => openEditChunk(chunk)}
                            disabled={chunkActionId === chunk.id}
                          >
                            编辑
                          </button>
                          <button
                            type="button"
                            className="library-action-btn library-action-btn--secondary"
                            onClick={() => void handleToggleChunk(chunk)}
                            disabled={chunkActionId === chunk.id}
                          >
                            {chunk.enabled ? '禁用' : '启用'}
                          </button>
                          <button
                            type="button"
                            className="library-action-btn library-action-btn--danger"
                            onClick={() => void handleDeleteChunk(chunk)}
                            disabled={chunkActionId === chunk.id}
                          >
                            {chunkActionId === chunk.id ? '处理中…' : '删除'}
                          </button>
                        </div>
                      </div>
                      <p className="chunk-content-preview">{previewContent(chunk.content)}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </aside>
        </div>
      )}
    </div>
  )
}
