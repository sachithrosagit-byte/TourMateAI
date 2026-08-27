import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import ChatMessage, { BotAvatar, TypingIndicator } from '../components/chat/ChatMessage'
import { scenes } from '../assets/photos'
import {
  fetchChatSessions,
  createChatSession,
  deleteChatSession,
  renameChatSession,
  fetchChatHistory,
  sendChatMessage
} from '../services/chat'
import '../styles/chat.css'

const getQuickPrompts = (t) => [
  { text: t('chat.prompts.beaches'), scene: scenes.hikkaduwaBeach },
  { text: t('chat.prompts.wildlife'), scene: scenes.leopard },
  { text: t('chat.prompts.heritage'), scene: scenes.sigiriyaGround },
  { text: t('chat.prompts.season'), scene: scenes.stiltFishing },
]

const COMPOSER_MAX_HEIGHT = 132

let nextLocalId = 0
const localId = () => `local-${nextLocalId++}`

function historyRowToTurns(row) {
  return [
    { id: `h${row.id}-user`, role: 'user', content: row.message },
    {
      id: `h${row.id}-assistant`,
      role: 'assistant',
      content: row.response,
      attractions: row.suggested_attractions,
    },
  ]
}

export default function Chat() {
  const { t } = useTranslation()
  const [sessions, setSessions] = useState([])
  const [activeSessionId, setActiveSessionId] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  
  const [messages, setMessages] = useState([])
  const [historyCount, setHistoryCount] = useState(0)
  
  const [loadingSessions, setLoadingSessions] = useState(true)
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [loadError, setLoadError] = useState(false)
  
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)

  const [editingSessionId, setEditingSessionId] = useState(null)
  const [editTitle, setEditTitle] = useState('')

  const scrollRef = useRef(null)
  const textareaRef = useRef(null)
  const restoredRef = useRef(false)
  const skipFetchRef = useRef(false)

  // Load Sessions on Mount
  useEffect(() => {
    let cancelled = false
    fetchChatSessions()
      .then((data) => {
        if (cancelled) return
        setSessions(data)
        if (data.length > 0) {
          setActiveSessionId(data[0].id)
        }
      })
      .catch(console.error)
      .finally(() => {
        if (!cancelled) setLoadingSessions(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  // Load History when activeSessionId changes
  useEffect(() => {
    if (!activeSessionId) {
      setMessages([])
      setHistoryCount(0)
      return
    }

    if (skipFetchRef.current) {
      skipFetchRef.current = false
      return
    }

    let cancelled = false
    setLoadingMessages(true)
    fetchChatHistory(activeSessionId)
      .then((rows) => {
        if (cancelled) return
        const turns = rows.flatMap(historyRowToTurns)
        setMessages(turns)
        setHistoryCount(turns.length)
        restoredRef.current = false // reset for smooth scrolling
      })
      .catch(() => {
        if (!cancelled) setLoadError(true)
      })
      .finally(() => {
        if (!cancelled) setLoadingMessages(false)
      })

    return () => {
      cancelled = true
    }
  }, [activeSessionId])

  // Scroll to bottom
  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    const behavior = restoredRef.current ? 'smooth' : 'auto'
    restoredRef.current = true
    el.scrollTo({ top: el.scrollHeight, behavior })
  }, [messages, sending, loadingMessages])

  const resetComposerHeight = () => {
    const el = textareaRef.current
    if (el) el.style.height = 'auto'
  }

  const handleInput = (event) => {
    setInput(event.target.value)
    const el = event.target
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, COMPOSER_MAX_HEIGHT)}px`
  }

  const handleNewChat = async () => {
    setActiveSessionId(null)
    setMessages([])
    setHistoryCount(0)
  }

  const handleDeleteSession = async (e, id) => {
    e.stopPropagation()
    if (!window.confirm(t('chat.confirmDelete'))) return
    try {
      await deleteChatSession(id)
      setSessions((prev) => prev.filter((s) => s.id !== id))
      if (activeSessionId === id) {
        setActiveSessionId(null)
        setMessages([])
      }
    } catch (err) {
      console.error(err)
    }
  }

  const handleStartRename = (e, session) => {
    e.stopPropagation()
    setEditingSessionId(session.id)
    setEditTitle(session.title)
  }

  const handleSaveRename = async (e, id) => {
    e.preventDefault()
    try {
      const updated = await renameChatSession(id, editTitle)
      setSessions((prev) => prev.map((s) => (s.id === id ? updated : s)))
      setEditingSessionId(null)
    } catch (err) {
      console.error(err)
    }
  }

  const send = async (raw) => {
    const text = raw.trim()
    if (!text || sending) return

    setInput('')
    resetComposerHeight()

    const history = messages
      .filter((m) => !m.failed)
      .map(({ role, content }) => ({ role, content }))

    const userMessage = { id: localId(), role: 'user', content: text }
    setMessages((prev) => [...prev, userMessage])
    setSending(true)
    
    try {
      let targetSessionId = activeSessionId
      
      // Auto-create session if this is the first message in a new chat
      if (!targetSessionId) {
        const newSession = await createChatSession()
        targetSessionId = newSession.id
        setSessions((prev) => [newSession, ...prev])
        skipFetchRef.current = true
        setActiveSessionId(targetSessionId)
      }

      const data = await sendChatMessage(text, targetSessionId, history)
      
      setMessages((prev) => [
        ...prev,
        {
          id: localId(),
          role: 'assistant',
          content: data.reply,
          attractions: data.suggested_attractions,
        },
      ])

      // If backend auto-updated the title
      if (data.session_title) {
        setSessions((prev) => prev.map((s) => (s.id === targetSessionId ? { ...s, title: data.session_title } : s)))
      }

    } catch {
      setMessages((prev) =>
        prev.map((m) => (m.id === userMessage.id ? { ...m, failed: true } : m))
      )
    } finally {
      setSending(false)
    }
  }

  const retry = (message) => {
    setMessages((prev) => prev.filter((m) => m.id !== message.id))
    send(message.content)
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    send(input)
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      send(input)
    }
  }

  const showEarlierDivider = historyCount > 0 && messages.length > historyCount

  return (
    <div className="chat-layout">
      {/* Sidebar */}
      {sidebarOpen && (
        <div className="chat-sidebar card">
          <div className="chat-sidebar-header">
            <h2 style={{ fontSize: 'var(--text-lg)' }}>{t('chat.sidebarTitle')}</h2>
            <div style={{ display: 'flex', gap: '4px' }}>
              <button type="button" className="btn btn-primary" style={{ padding: '0.4rem 0.8rem', fontSize: 'var(--text-sm)' }} onClick={handleNewChat}>
                {t('chat.newChatBtn')}
              </button>
              <button type="button" className="btn btn-ghost" style={{ padding: '0.4rem' }} onClick={() => setSidebarOpen(false)} title={t('chat.closeSidebar')}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
              </button>
            </div>
          </div>
          
          <div className="chat-sessions-list">
            {loadingSessions ? (
              <div className="spinner" style={{ alignSelf: 'center', marginTop: '1rem' }} />
            ) : sessions.length === 0 ? (
              <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-sm)', textAlign: 'center', marginTop: '1rem' }}>{t('chat.noRecentChats')}</p>
            ) : (
              sessions.map((session) => (
                <div
                  key={session.id}
                  className={`chat-session-item ${activeSessionId === session.id ? 'active' : ''}`}
                  onClick={() => setActiveSessionId(session.id)}
                >
                  {editingSessionId === session.id ? (
                    <form onSubmit={(e) => handleSaveRename(e, session.id)} style={{ display: 'flex', width: '100%', gap: '4px' }}>
                      <input 
                        type="text" 
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onClick={(e) => e.stopPropagation()}
                        autoFocus
                        style={{ flex: 1, padding: '2px 4px', fontSize: 'var(--text-sm)' }}
                      />
                      <button type="submit" className="btn btn-primary" style={{ padding: '2px 8px' }} onClick={(e) => e.stopPropagation()}>{t('chat.saveBtn')}</button>
                    </form>
                  ) : (
                    <>
                      <span className="chat-session-title" title={session.title}>{session.title}</span>
                      <div className="chat-session-actions">
                        <button className="chat-session-btn" onClick={(e) => handleStartRename(e, session)} title={t('chat.renameBtn')}>
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                        </button>
                        <button className="chat-session-btn" onClick={(e) => handleDeleteSession(e, session.id)} title={t('chat.deleteBtn')}>
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="chat-page">
        <div className="chat-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {!sidebarOpen && (
              <button type="button" className="btn btn-ghost" style={{ padding: '0.4rem', border: '1px solid var(--color-border-subtle)', background: 'var(--color-surface)' }} onClick={() => setSidebarOpen(true)} title={t('chat.openSidebar')}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
              </button>
            )}
            <div>
              <h1 className="chat-title">{t('chat.headerTitle')}</h1>
              <p className="chat-subtitle">{t('chat.headerSubtitle')}</p>
            </div>
          </div>
        </div>

        <div className="chat-panel card">
          <div className="chat-scroll" ref={scrollRef}>
            {loadingMessages ? (
              <div className="chat-state">
                <div className="spinner" />
                <p>{t('chat.loadingHistory')}</p>
              </div>
            ) : messages.length === 0 ? (
              <div className="chat-welcome">
                <div className="chat-welcome-avatar">
                  <BotAvatar />
                </div>
                <h2>{t('chat.welcomeTitle')}</h2>
                <p>
                  {t('chat.welcomeDesc')}
                </p>
                {loadError && (
                  <div className="alert alert-error chat-load-error">
                    {t('chat.loadError')}
                  </div>
                )}
                <div className="chat-prompts">
                  {getQuickPrompts(t).map(({ text, scene }) => (
                    <button
                      key={text}
                      type="button"
                      className="chat-prompt"
                      onClick={() => send(text)}
                    >
                      <img
                        className="chat-prompt-thumb"
                        src={scene.src}
                        style={{ objectPosition: scene.position }}
                        alt=""
                        aria-hidden="true"
                      />
                      {text}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((message, index) => (
                  <div key={message.id} className="chat-msg-slot">
                    {showEarlierDivider && index === historyCount && (
                      <div className="chat-divider" role="separator">
                        <span>{t('chat.newMessagesDivider')}</span>
                      </div>
                    )}
                    <ChatMessage message={message} onRetry={retry} />
                  </div>
                ))}
                {sending && <TypingIndicator />}
              </>
            )}
          </div>

          <form className="chat-composer" onSubmit={handleSubmit}>
            <textarea
              ref={textareaRef}
              className="chat-input"
              rows={1}
              placeholder={t('chat.inputPlaceholder')}
              value={input}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              maxLength={2000}
              aria-label={t('chat.inputAria')}
            />
            <button
              type="submit"
              className="chat-send"
              disabled={!input.trim() || sending}
              aria-label={t('chat.sendAria')}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path
                  d="m4.5 12 15-7.5L15 12l4.5 7.5-15-7.5Zm0 0H15"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </form>
          <p className="chat-hint">{t('chat.inputHint')}</p>
        </div>
      </div>
    </div>
  )
}
