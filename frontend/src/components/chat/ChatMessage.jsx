// One chat turn: a right-aligned user bubble or a left-aligned assistant bubble
// (with bot avatar), plus any suggested-attraction cards under the assistant's
// text. Also exports the "assistant is thinking" indicator, which reuses the
// same row layout so the pending state sits exactly where the reply will land.

import { useTranslation } from 'react-i18next'
import ChatSuggestionCard from './ChatSuggestionCard'

export function BotAvatar() {
  return (
    <div className="chat-avatar" aria-hidden="true">
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
        <path
          d="M12 3v2m0 14v2M5 8h14a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1Z"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="9" cy="12.5" r="1.15" fill="currentColor" />
        <circle cx="15" cy="12.5" r="1.15" fill="currentColor" />
      </svg>
    </div>
  )
}

export default function ChatMessage({ message, onRetry }) {
  const { t } = useTranslation()
  const isUser = message.role === 'user'

  return (
    <div className={`chat-msg ${isUser ? 'chat-msg-user' : 'chat-msg-assistant'}`}>
      {!isUser && <BotAvatar />}
      <div className="chat-msg-content">
        <div className={`chat-bubble${message.failed ? ' chat-bubble-failed' : ''}`}>
          {message.content}
        </div>

        {message.failed && (
          <button
            type="button"
            className="chat-retry"
            onClick={() => onRetry(message)}
          >
            {t('chat.retryBtn')}
          </button>
        )}

        {!isUser && message.attractions?.length > 0 && (
          <div className="chat-suggestions">
            {message.attractions.map((attraction) => (
              <ChatSuggestionCard key={attraction.id} attraction={attraction} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// Shown while a reply is in flight.
export function TypingIndicator() {
  const { t } = useTranslation()
  return (
    <div className="chat-msg chat-msg-assistant" aria-label={t('chat.typingIndicator')}>
      <BotAvatar />
      <div className="chat-msg-content">
        <div className="chat-bubble chat-typing">
          <span className="chat-typing-dot" />
          <span className="chat-typing-dot" />
          <span className="chat-typing-dot" />
        </div>
      </div>
    </div>
  )
}
