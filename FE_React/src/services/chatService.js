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
}) => {
  const endpoint = sessionId
    ? `/bots/${botId}/ask/${sessionId}`
    : `/bots/${botId}/ask`;

  // Use Axios with fetch adapter to leverage interceptors while supporting streaming
  const response = await api.post(endpoint, {
    message,
    streaming: true
  }, {
    signal,
    adapter: 'fetch', // Available in Axios v1.7.0+
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
    // The API returns "data: {json}\n\n" format
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
            accumulatedResponse += data.response;
            if (onChunk) onChunk(accumulatedResponse);
          }
        } catch (e) {
          console.warn("Parse error", e);
        }
      }
    }
  }
};
