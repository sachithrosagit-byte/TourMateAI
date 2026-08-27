// Chat API calls (see backend/app/routes/chat.py for the contracts these
// mirror). The backend expands suggested attraction ids into full attraction
// objects, so everything here is ready to render.

import api from './api'

export async function fetchChatSessions() {
  const { data } = await api.get('/chat/sessions')
  return data.sessions
}

export async function createChatSession(title = 'New Chat') {
  const { data } = await api.post('/chat/sessions', { title })
  return data
}

export async function deleteChatSession(sessionId) {
  const { data } = await api.delete(`/chat/sessions/${sessionId}`)
  return data.deleted
}

export async function renameChatSession(sessionId, title) {
  const { data } = await api.patch(`/chat/sessions/${sessionId}`, { title })
  return data
}

export async function sendChatMessage(message, sessionId, conversationHistory = []) {
  const { data } = await api.post('/chat', {
    message,
    session_id: sessionId,
    conversation_history: conversationHistory,
  })
  return data
}

export async function fetchChatHistory(sessionId, { limit = 50 } = {}) {
  const { data } = await api.get(`/chat/sessions/${sessionId}/history`, { params: { limit } })
  return data.messages
}
