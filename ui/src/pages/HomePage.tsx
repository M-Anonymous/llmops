import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getAuthMe, logout } from '../api/auth'
import { ApiError } from '../api/client'
import {
  deleteSession,
  getSessionList,
  getSessionMessages,
  sessionResume,
  sessionStream,
  type HitlDecision,
  type HitlInterrupt,
  type SessionInfo,
  type SessionStreamEvent,
} from '../api/session'
import { getOrCreateVisitorId } from '../utils/visitor'
import '../styles/common.css'
import './HomePage.css'

interface UiMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}

/** 首页对话固定使用 system_agent */
const SYSTEM_AGENT_ID = 'system_agent'

const GUEST_AVATAR =
  'data:image/svg+xml,' +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
      <rect width="64" height="64" rx="32" fill="#1e2430"/>
      <circle cx="32" cy="24" r="12" fill="#64748b"/>
      <path d="M12 54c4-12 14-18 20-18s16 6 20 18" fill="#64748b"/>
    </svg>`,
  )

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function titleFromQuestion(text: string) {
  const normalized = text.trim().replace(/\s+/g, ' ')
  return normalized.length > 40 ? `${normalized.slice(0, 40)}…` : normalized
}

export default function HomePage() {
  const navigate = useNavigate()
  const [authenticated, setAuthenticated] = useState(false)
  const [nickname, setNickname] = useState<string | null>(null)
  const [avatar, setAvatar] = useState<string | null>(null)
  const [authChecking, setAuthChecking] = useState(true)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [sessions, setSessions] = useState<SessionInfo[]>([])
  const [sessionsLoading, setSessionsLoading] = useState(false)
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null)
  const [sending, setSending] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [question, setQuestion] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<UiMessage[]>([])
  const [visitorId] = useState(() => getOrCreateVisitorId())
  const [interrupt, setInterrupt] = useState<HitlInterrupt | null>(null)
  const [pendingAssistantId, setPendingAssistantId] = useState<string | null>(null)

  const listRef = useRef<HTMLDivElement>(null)
  const userMenuRef = useRef<HTMLDivElement>(null)

  const displayName = authenticated ? nickname || '用户' : '访客模式'
  const displayAvatar = authenticated && avatar ? avatar : GUEST_AVATAR

  const refreshSessions = useCallback(async () => {
    setSessionsLoading(true)
    try {
      const list = await getSessionList({
        agent_id: SYSTEM_AGENT_ID,
        visitor_id: authenticated ? undefined : visitorId,
      })
      setSessions(list)
    } catch {
      setSessions([])
    } finally {
      setSessionsLoading(false)
    }
  }, [authenticated, visitorId])

  const bootstrap = useCallback(async () => {
    setAuthChecking(true)
    setError(null)
    try {
      const me = await getAuthMe()
      setAuthenticated(Boolean(me.authenticated))
      setNickname(me.nickname)
      setAvatar(me.avatar)
    } catch (err) {
      setError(err instanceof Error ? err.message : '初始化失败')
    } finally {
      setAuthChecking(false)
    }
  }, [])

  useEffect(() => {
    void bootstrap()
  }, [bootstrap])

  useEffect(() => {
    if (authChecking) {
      return
    }
    void refreshSessions()
  }, [authChecking, refreshSessions])

  useEffect(() => {
    const el = listRef.current
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  }, [messages, sending])

  useEffect(() => {
    if (!userMenuOpen) {
      return
    }
    function handlePointerDown(event: MouseEvent) {
      const root = userMenuRef.current
      if (root && !root.contains(event.target as Node)) {
        setUserMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handlePointerDown)
    return () => document.removeEventListener('mousedown', handlePointerDown)
  }, [userMenuOpen])

  function resetChat() {
    setSessionId(null)
    setMessages([])
    setError(null)
    setQuestion('')
    setInterrupt(null)
    setPendingAssistantId(null)
  }

  async function handleLogout() {
    setUserMenuOpen(false)
    try {
      await logout()
    } catch {
      // ignore network error; still clear local auth state
    }
    setAuthenticated(false)
    setNickname(null)
    setAvatar(null)
    resetChat()
    setSessionsLoading(true)
    try {
      const list = await getSessionList({
        agent_id: SYSTEM_AGENT_ID,
        visitor_id: visitorId,
      })
      setSessions(list)
    } catch {
      setSessions([])
    } finally {
      setSessionsLoading(false)
    }
  }

  async function handleSelectSession(id: string) {
    if (sending || id === sessionId) {
      return
    }
    setLoadingHistory(true)
    setError(null)
    try {
      const data = await getSessionMessages({
        session_id: id,
        visitor_id: authenticated ? undefined : visitorId,
      })
      setSessionId(id)
      setInterrupt(data.interrupt ?? null)
      setPendingAssistantId(null)
      setMessages(
        data.messages
          .filter((item) => item.role === 'user' || item.role === 'assistant')
          .map((item) => ({
            id: createMessageId(),
            role: item.role as 'user' | 'assistant',
            content: item.content || '',
          })),
      )
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError(err instanceof Error ? err.message : '加载会话失败')
      }
    } finally {
      setLoadingHistory(false)
    }
  }

  async function handleDeleteSession(item: SessionInfo) {
    if (sending || deletingSessionId) {
      return
    }
    const title = item.title || '新会话'
    const confirmed = window.confirm(`确定删除会话「${title}」吗？此操作不可恢复。`)
    if (!confirmed) {
      return
    }

    setDeletingSessionId(item.id)
    setError(null)
    try {
      await deleteSession({
        session_id: item.id,
        visitor_id: authenticated ? undefined : visitorId,
      })
      setSessions((prev) => prev.filter((session) => session.id !== item.id))
      if (sessionId === item.id) {
        resetChat()
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError(err instanceof Error ? err.message : '删除会话失败')
      }
    } finally {
      setDeletingSessionId(null)
    }
  }

  async function consumeStream(
    events: AsyncGenerator<SessionStreamEvent, void, unknown>,
    assistantId: string,
    options?: { isNewSession?: boolean; titleText?: string },
  ) {
    for await (const eventItem of events) {
      if (eventItem.type === 'session') {
        setSessionId(eventItem.sessionId)
        if (options?.isNewSession) {
          setSessions((prev) => {
            const exists = prev.some((item) => item.id === eventItem.sessionId)
            if (exists) {
              return prev
            }
            const now = new Date().toISOString()
            return [
              {
                id: eventItem.sessionId,
                accountId: null,
                visitorId: authenticated ? null : visitorId,
                agentId: SYSTEM_AGENT_ID,
                title: titleFromQuestion(options.titleText ?? ''),
                createAt: now,
                updateAt: now,
              },
              ...prev,
            ]
          })
        }
        continue
      }
      if (eventItem.type === 'delta') {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId
              ? { ...msg, content: msg.content + eventItem.content }
              : msg,
          ),
        )
        continue
      }
      if (eventItem.type === 'interrupt') {
        setSessionId(eventItem.sessionId)
        setInterrupt({
          actionRequests: eventItem.actionRequests,
          reviewConfigs: eventItem.reviewConfigs,
        })
        setPendingAssistantId(assistantId)
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId && !msg.content.trim()
              ? { ...msg, content: '等待人工审批工具调用…' }
              : msg,
          ),
        )
        continue
      }
      if (eventItem.type === 'error') {
        throw new Error(eventItem.detail)
      }
      if (eventItem.type === 'done') {
        setSessionId(eventItem.sessionId)
        setInterrupt(null)
        setPendingAssistantId(null)
      }
    }

    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === assistantId && !msg.content.trim()
          ? { ...msg, content: '（无回复内容）' }
          : msg,
      ),
    )
  }

  async function handleSend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const text = question.trim()
    if (!text || sending || interrupt) {
      return
    }

    const userMessage: UiMessage = {
      id: createMessageId(),
      role: 'user',
      content: text,
    }
    const assistantId = createMessageId()
    const isNewSession = !sessionId

    setMessages((prev) => [
      ...prev,
      userMessage,
      { id: assistantId, role: 'assistant', content: '' },
    ])
    setQuestion('')
    setSending(true)
    setError(null)
    setInterrupt(null)

    try {
      await consumeStream(
        sessionStream({
          agent_id: SYSTEM_AGENT_ID,
          question: text,
          session_id: sessionId ?? undefined,
          visitor_id: authenticated ? undefined : visitorId,
        }),
        assistantId,
        { isNewSession, titleText: text },
      )
      void refreshSessions()
    } catch (err) {
      setMessages((prev) => prev.filter((msg) => msg.id !== assistantId))
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError(err instanceof Error ? err.message : '发送失败')
      }
    } finally {
      setSending(false)
    }
  }

  async function handleDecision(type: 'approve' | 'reject') {
    if (!sessionId || !interrupt || sending) {
      return
    }

    const decisions: HitlDecision[] = interrupt.actionRequests.map(() => ({ type }))
    const assistantId = pendingAssistantId ?? createMessageId()

    if (!pendingAssistantId) {
      setMessages((prev) => [
        ...prev,
        { id: assistantId, role: 'assistant', content: '' },
      ])
    } else {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantId
            ? {
                ...msg,
                content: msg.content.replace(/等待人工审批工具调用…$/, '') + '\n',
              }
            : msg,
        ),
      )
    }

    setSending(true)
    setError(null)
    setInterrupt(null)

    try {
      await consumeStream(
        sessionResume({
          session_id: sessionId,
          agent_id: SYSTEM_AGENT_ID,
          visitor_id: authenticated ? undefined : visitorId,
          decisions,
        }),
        assistantId,
      )
      void refreshSessions()
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError(err instanceof Error ? err.message : '审批失败')
      }
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="chat-shell">
      <div className="page-bg" aria-hidden="true">
        <div className="page-bg-glow page-bg-glow--left" />
        <div className="page-bg-glow page-bg-glow--right" />
        <div className="page-bg-grid" />
        <div className="page-bg-sea">
          <svg className="page-bg-sea-layer page-bg-sea-layer--back" viewBox="0 0 1440 320" preserveAspectRatio="none">
            <path d="M0,160 C180,220 360,80 540,140 C720,200 900,60 1080,120 C1260,180 1350,100 1440,140 L1440,320 L0,320 Z" />
          </svg>
          <svg className="page-bg-sea-layer page-bg-sea-layer--mid" viewBox="0 0 1440 320" preserveAspectRatio="none">
            <path d="M0,190 C160,130 320,250 480,180 C640,110 800,230 960,170 C1120,110 1280,210 1440,160 L1440,320 L0,320 Z" />
          </svg>
          <svg className="page-bg-sea-layer page-bg-sea-layer--front" viewBox="0 0 1440 320" preserveAspectRatio="none">
            <path d="M0,220 C200,180 280,260 480,210 C680,160 760,250 960,200 C1160,150 1280,240 1440,200 L1440,320 L0,320 Z" />
          </svg>
        </div>
      </div>

      <aside className="chat-sidebar">
        <div className="chat-sidebar-top">
          <h1 className="chat-sidebar-brand">LLMOPS</h1>
          <button
            type="button"
            className="chat-new-btn"
            onClick={resetChat}
            disabled={sending}
          >
            <span className="chat-new-btn-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.7">
                <path d="M5 7.5A2.5 2.5 0 0 1 7.5 5h9A2.5 2.5 0 0 1 19 7.5v6A2.5 2.5 0 0 1 16.5 16H12l-3.5 3v-3H7.5A2.5 2.5 0 0 1 5 13.5v-6Z" />
                <path d="M12 9v4M10 11h4" strokeLinecap="round" />
              </svg>
            </span>
            新建对话
          </button>
        </div>

        <div className="chat-history">
          <p className="chat-history-label">历史对话</p>
          <div className="chat-history-list">
            {sessionsLoading ? (
              <p className="chat-history-empty">加载中…</p>
            ) : sessions.length === 0 ? (
              <p className="chat-history-empty">暂无会话</p>
            ) : (
              sessions.map((item) => (
                <div
                  key={item.id}
                  className={`chat-history-row${sessionId === item.id ? ' is-active' : ''}`}
                >
                  <button
                    type="button"
                    className="chat-history-item"
                    onClick={() => void handleSelectSession(item.id)}
                    disabled={sending || loadingHistory || deletingSessionId === item.id}
                    title={item.title || '新会话'}
                  >
                    {item.title || '新会话'}
                  </button>
                  <button
                    type="button"
                    className="chat-history-delete"
                    aria-label={`删除会话 ${item.title || '新会话'}`}
                    title="删除会话"
                    disabled={sending || loadingHistory || deletingSessionId === item.id}
                    onClick={(event) => {
                      event.stopPropagation()
                      void handleDeleteSession(item)
                    }}
                  >
                    {deletingSessionId === item.id ? '…' : '×'}
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="chat-user" ref={userMenuRef}>
          {authenticated ? (
            <>
              <button
                type="button"
                className="chat-user-card chat-user-card--button"
                onClick={() => setUserMenuOpen((open) => !open)}
                aria-expanded={userMenuOpen}
                aria-haspopup="menu"
              >
                <img className="chat-user-avatar" src={displayAvatar} alt="" />
                <span className="chat-user-name">{displayName}</span>
              </button>
              {userMenuOpen && (
                <div className="chat-user-menu" role="menu">
                  <button type="button" className="chat-user-menu-item is-disabled" disabled role="menuitem">
                    个人信息
                  </button>
                  <button
                    type="button"
                    className="chat-user-menu-item"
                    role="menuitem"
                    onClick={() => {
                      setUserMenuOpen(false)
                      navigate('/admin')
                    }}
                  >
                    我的空间
                  </button>
                  <button
                    type="button"
                    className="chat-user-menu-item chat-user-menu-item--danger"
                    role="menuitem"
                    onClick={() => void handleLogout()}
                  >
                    退出登录
                  </button>
                </div>
              )}
            </>
          ) : (
            <Link to="/login" className="chat-user-card chat-user-card--link">
              <img className="chat-user-avatar" src={displayAvatar} alt="" />
              <span className="chat-user-name">{displayName}</span>
            </Link>
          )}
        </div>
      </aside>

      <main className="chat-main">
        {error && (
          <div className="chat-alert" role="alert">
            {error}
          </div>
        )}

        <section className="chat-panel">
          <div className="chat-messages" ref={listRef}>
            {authChecking || loadingHistory ? (
              <div className="chat-empty">加载中…</div>
            ) : messages.length === 0 ? (
              <div className="chat-empty">
                <h2 className="chat-empty-brand">LLMOPS</h2>
                <p>向「客服助手」发送一条消息开始对话</p>
                <span>会创建标题为「新会话」的会话，并按配置加载模型、工具与提示词</span>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <article
                    key={message.id}
                    className={`chat-bubble chat-bubble--${message.role}`}
                  >
                    <span className="chat-role">
                      {message.role === 'user' ? '你' : '客服助手'}
                    </span>
                    <div className="chat-content">
                      {message.content || (sending && !interrupt ? '思考中…' : '')}
                    </div>
                  </article>
                ))}

                {interrupt && (
                  <div className="chat-hitl-card">
                    <div className="chat-hitl-head">
                      <h3>工具调用待审批</h3>
                      <p>请选择 approve 或 reject 后继续对话</p>
                    </div>
                    <div className="chat-hitl-list">
                      {interrupt.actionRequests.map((action, index) => (
                        <article key={`${action.name}-${index}`} className="chat-hitl-item">
                          <strong>{action.name}</strong>
                          {action.description ? <p>{action.description}</p> : null}
                          <pre>{JSON.stringify(action.args ?? {}, null, 2)}</pre>
                        </article>
                      ))}
                    </div>
                    <div className="chat-hitl-actions">
                      <button
                        type="button"
                        className="chat-hitl-btn chat-hitl-btn--reject"
                        disabled={sending}
                        onClick={() => void handleDecision('reject')}
                      >
                        reject
                      </button>
                      <button
                        type="button"
                        className="chat-hitl-btn chat-hitl-btn--approve"
                        disabled={sending}
                        onClick={() => void handleDecision('approve')}
                      >
                        {sending ? '处理中…' : 'approve'}
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          <form className="chat-composer" onSubmit={(event) => void handleSend(event)}>
            <textarea
              value={question}
              rows={3}
              placeholder={interrupt ? '请先完成工具审批…' : '输入你的问题…'}
              disabled={sending || authChecking || Boolean(interrupt)}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault()
                  event.currentTarget.form?.requestSubmit()
                }
              }}
            />
            <button
              type="submit"
              className="chat-send"
              disabled={sending || authChecking || Boolean(interrupt) || !question.trim()}
            >
              {sending ? '回复中…' : '发送'}
            </button>
          </form>
        </section>
      </main>
    </div>
  )
}
