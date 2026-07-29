const VISITOR_ID_KEY = 'llmops_visitor_id'

function createVisitorId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID().replaceAll('-', '')
  }
  return `${Date.now().toString(16)}${Math.random().toString(16).slice(2, 10)}`.slice(0, 32)
}

export function getOrCreateVisitorId(): string {
  const existing = localStorage.getItem(VISITOR_ID_KEY)
  if (existing) {
    return existing
  }
  const visitorId = createVisitorId()
  localStorage.setItem(VISITOR_ID_KEY, visitorId)
  return visitorId
}
