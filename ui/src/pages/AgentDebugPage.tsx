import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { getAgentList, type Agent } from '../api/agent'
import {
  debugChatStream,
  sessionResume,
  type HitlActionRequest,
  type HitlDecision,
  type HitlInterrupt,
  type HitlReviewConfig,
  type SessionStreamEvent,
} from '../api/session'
import '../styles/common.css'
import './LibraryPage.css'
import './AgentPage.css'
import './AgentDebugPage.css'

interface UiMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function formatArgs(args: Record<string, unknown>) {
  try {
    return JSON.stringify(args, null, 2)
  } catch {
    return String(args)
  }
}

function allowedForAction(
  action: HitlActionRequest,
  index: number,
  reviewConfigs: HitlReviewConfig[],
): Array<'approve' | 'reject'> {
  const byName = reviewConfigs.find((item) => item.actionName === action.name)
  const byIndex = reviewConfigs[index]
  const allowed = byName?.allowedDecisions ?? byIndex?.allowedDecisions ?? ['approve', 'reject']
  return allowed.filter((item): item is 'approve' | 'reject' => item === 'approve' || item === 'reject')
}

export default function AgentDebugPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const agentId = searchParams.get('agent_id') ?? ''
  const agentNameFromQuery = searchParams.get('agent_name')

  const [agent, setAgent] = useState<Agent | null>(null)
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [question, setQuestion] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<UiMessage[]>([])
  const [interrupt, setInterrupt] = useState<HitlInterrupt | null>(null)
  const [pendingAssistantId, setPendingAssistantId] = useState<string | null>(null)

  const listRef = useRef<HTMLDivElement>(null)

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

  const loadAgent = useCallback(async () => {
    if (!agentId) {
      return
    }

    setLoading(true)
    setError(null)
    try {
      const list = await getAgentList()
      const current = list.find((item) => item.id === agentId) ?? null
      if (!current) {
        setError('Agent 不存在或无权访问')
      }
      setAgent(current)
    } catch (err) {
      handleApiError(err, '加载 Agent 失败')
    } finally {
      setLoading(false)
    }
  }, [agentId, handleApiError])

  useEffect(() => {
    if (!agentId) {
      navigate('/admin/agent', { replace: true })
      return
    }
    void loadAgent()
  }, [agentId, loadAgent, navigate])

  useEffect(() => {
    const el = listRef.current
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  }, [messages, sending, interrupt])

  function resetChat() {
    setSessionId(null)
    setMessages([])
    setError(null)
    setQuestion('')
    setInterrupt(null)
    setPendingAssistantId(null)
  }

  async function consumeStream(
    events: AsyncGenerator<SessionStreamEvent, void, unknown>,
    assistantId: string,
  ) {
    for await (const eventItem of events) {
      if (eventItem.type === 'session') {
        setSessionId(eventItem.sessionId)
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
    if (!text || !agent || sending || interrupt) {
      return
    }

    const userMessage: UiMessage = {
      id: createMessageId(),
      role: 'user',
      content: text,
    }
    const assistantId = createMessageId()

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
        debugChatStream({
          agent_id: agent.id,
          question: text,
          session_id: sessionId ?? undefined,
        }),
        assistantId,
      )
    } catch (err) {
      setMessages((prev) => prev.filter((msg) => msg.id !== assistantId))
      handleApiError(err, '调试对话失败')
    } finally {
      setSending(false)
    }
  }

  async function handleDecision(type: 'approve' | 'reject') {
    if (!agent || !sessionId || !interrupt || sending) {
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
          agent_id: agent.id,
          decisions,
        }),
        assistantId,
      )
    } catch (err) {
      handleApiError(err, '审批失败')
    } finally {
      setSending(false)
    }
  }

  const title = agent?.name || agentNameFromQuery || 'Agent 调试'
  const canSend = !sending && !interrupt

  return (
    <div className="library-page agent-page agent-debug-page">
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
            <p className="brand-eyebrow">Agent Debug</p>
            <h1 className="library-title">{title}</h1>
            <p className="agent-config-subtitle">
              调试对话
              {sessionId ? ` · 会话 ${sessionId.slice(0, 8)}…` : ' · 发送后自动创建调试会话'}
            </p>
          </div>
        </div>
        <div className="agent-debug-header-actions">
          <Link
            to={`/agent/config?agent_id=${encodeURIComponent(agentId)}&agent_name=${encodeURIComponent(title)}`}
            className="library-action-btn library-action-btn--secondary"
          >
            去配置
          </Link>
          <button
            type="button"
            className="library-action-btn library-action-btn--secondary"
            onClick={resetChat}
            disabled={sending || (!sessionId && messages.length === 0)}
          >
            新对话
          </button>
        </div>
      </header>

      <main className="library-main agent-debug-main">
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
          <section className="agent-debug-panel">
            <div className="agent-debug-messages" ref={listRef}>
              {messages.length === 0 ? (
                <div className="agent-debug-empty">
                  <p>向「{agent.name}」发送一条消息开始调试</p>
                  <span>会创建标题为「调试会话」的会话，并按配置加载模型、工具与中间件</span>
                </div>
              ) : (
                messages.map((message) => (
                  <article
                    key={message.id}
                    className={`agent-debug-bubble agent-debug-bubble--${message.role}`}
                  >
                    <span className="agent-debug-role">
                      {message.role === 'user' ? '你' : agent.name}
                    </span>
                    <div className="agent-debug-content">
                      {message.content || (sending && !interrupt ? '思考中…' : '')}
                    </div>
                  </article>
                ))
              )}

              {interrupt && (
                <div className="agent-hitl-card">
                  <div className="agent-hitl-head">
                    <h3>工具调用待审批</h3>
                    <p>HumanInTheLoop 已拦截以下工具，请选择 approve 或 reject</p>
                  </div>
                  <div className="agent-hitl-list">
                    {interrupt.actionRequests.map((action, index) => {
                      const allowed = allowedForAction(
                        action,
                        index,
                        interrupt.reviewConfigs,
                      )
                      return (
                        <article key={`${action.name}-${index}`} className="agent-hitl-item">
                          <strong>{action.name}</strong>
                          {action.description ? <p>{action.description}</p> : null}
                          <pre>{formatArgs(action.args ?? {})}</pre>
                          <span className="agent-hitl-allowed">
                            允许：{allowed.join(' / ')}
                          </span>
                        </article>
                      )
                    })}
                  </div>
                  <div className="agent-hitl-actions">
                    <button
                      type="button"
                      className="library-action-btn library-action-btn--danger"
                      disabled={sending}
                      onClick={() => void handleDecision('reject')}
                    >
                      reject
                    </button>
                    <button
                      type="button"
                      className="library-create-btn"
                      disabled={sending}
                      onClick={() => void handleDecision('approve')}
                    >
                      {sending ? '处理中…' : 'approve'}
                    </button>
                  </div>
                </div>
              )}
            </div>

            <form className="agent-debug-composer" onSubmit={(event) => void handleSend(event)}>
              <textarea
                value={question}
                rows={3}
                placeholder={interrupt ? '请先完成工具审批…' : '输入要测试的问题…'}
                disabled={!canSend}
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
                className="library-create-btn"
                disabled={!canSend || !question.trim()}
              >
                {sending ? '回复中…' : '发送'}
              </button>
            </form>
          </section>
        )}
      </main>
    </div>
  )
}
