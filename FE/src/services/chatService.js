import api from './api';

/**
 * Streams a chat response from the bot.
 * 
 * @param {Object} params
 * @param {string} params.botId - The ID of the bot involved in the chat.
 * @param {string} [params.sessionId] - The current session ID (if any).
 * @param {string} params.message - The user's message.
 * @param {AbortSignal} params.signal - Signal to abort the request.
 * @param {Function} params.onChunk - Callback for each text chunk received.
 * @param {Function} params.onSessionId - Callback when session ID is received/confirmed.
 * @returns {Promise<void>}
 */
export const streamChatResponse = async ({
  botId,
  sessionId,
  message,
  signal,
  onChunk,
  onSessionId,
  onStatus,
  onToolCall,
  quizMode = false,
}) => {
  const endpoint = sessionId
    ? `/bots/${botId}/ask/${sessionId}`
    : `/bots/${botId}/ask`;

  // 1. NON-STREAMING (Quiz Mode)
  if (quizMode) {
    try {
      const response = await api.post(endpoint, {
        message,
        streaming: false,
        quiz_mode: true,
      }, { 
        signal,
        timeout: 600000 // 10 minutes for long quiz generation
      });

      const data = response.data;
      if (data.session_id && onSessionId) {
        onSessionId(data.session_id);
      }
      
      const text = data.answer || data.response;
      if (text && onChunk) {
        onChunk(text);
      }
    } catch (error) {
      console.error("Non-streaming chat error details:", error.toJSON ? error.toJSON() : error);
      throw error;
    }
    return;
  }

  // 2. STREAMING (Normal Chat)
  const response = await api.post(endpoint, {
    message,
    streaming: true,
    quiz_mode: false,
  }, {
    signal,
    adapter: 'fetch',
    responseType: 'stream'
  });

  const reader = response.data.getReader();
  const decoder = new TextDecoder();
  let accumulatedResponse = "";
  let activeSessionId = sessionId;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    const lines = chunk.split('\n\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const jsonStr = line.replace('data: ', '').trim();
        if (jsonStr === '[DONE]') break;

        try {
          const data = JSON.parse(jsonStr);

          if (data.session_id && !activeSessionId) {
            activeSessionId = data.session_id;
            if (onSessionId) onSessionId(data.session_id);
          }

          if (data.response) {
            const responseText = data.response;
            
            // Handle tool call events
            if (responseText.startsWith('__TOOL_CALL__: ')) {
              const toolCallJson = responseText.replace('__TOOL_CALL__: ', '');
              try {
                const toolCallData = JSON.parse(toolCallJson);
                if (typeof onToolCall === 'function') {
                  onToolCall(toolCallData);
                }
              } catch (e) {
                console.warn("Failed to parse tool call JSON", e);
              }
            }
            // Handle status events
            else if (responseText.startsWith('__STATUS__: ')) {
              const statusJson = responseText.replace('__STATUS__: ', '');
              try {
                const statusData = JSON.parse(statusJson);
                if (statusData.text && typeof onStatus === 'function') {
                  onStatus(statusData.text);
                }
              } catch (e) {
                console.warn("Failed to parse status JSON", e);
              }
            } else {
              accumulatedResponse += responseText;
              if (onChunk) onChunk(accumulatedResponse);
            }
          }
        } catch (e) {
          console.warn("Parse error", e);
        }
      }
    }
  }
};

/**
 * Fetches the list of chat sessions.
 * @param {Object} params - Query params (limit, cursor_timestamp, bot_id)
 */
export const getSessions = async (params = {}) => {
  const response = await api.get('/sessions', { params });
  return response.data;
};

/**
 * Fetches messages for a specific session.
 * @param {string} sessionId
 * @param {Object} params - Query params (limit, cursor_timestamp, sort_desc)
 */
export const getSessionMessages = async (sessionId, params = {}) => {
  const response = await api.get(`/sessions/${sessionId}/messages`, { params });
  return response.data;
};

/**
 * Fetches details of a specific session.
 * @param {string} sessionId
 */
export const getSession = async (sessionId) => {
  const response = await api.get(`/sessions/${sessionId}`);
  return response.data;
};

/**
 * Deletes a session.
 * @param {string} sessionId 
 */
export const deleteSession = async (sessionId) => {
  const response = await api.delete(`/sessions/${sessionId}`);
  return response.data;
};

/**
 * Updates a session.
 * @param {string} sessionId
 * @param {Object} data - Fields to update (e.g. summary_text)
 */
export const updateSession = async (sessionId, data) => {
  const response = await api.patch(`/sessions/${sessionId}`, data);
  return response.data;
};

/**
 * Rates a chat message.
 * @param {string} messageId 
 * @param {string|null} rating - 'thumbs_up', 'thumbs_down', or null
 */
export const rateMessage = async (messageId, rating) => {
  const response = await api.post(`/messages/${messageId}/rate`, { rating });
  return response.data;
};
