import api from './api';

export const botService = {
  getBots: async (options = {}) => {
    const response = await api.get('/bots', options);
    return response.data;
  },

  getBot: async (id, options = {}) => {
    const response = await api.get(`/bots/${id}`, options);
    return response.data;
  },

  createBot: async (botData, options = {}) => {
    const response = await api.post('/bots', botData, options);
    return response.data;
  },

  updateBot: async (id, botData, options = {}) => {
    const response = await api.put(`/bots/${id}`, botData, options);
    return response.data;
  },

  deleteBot: async (id, options = {}) => {
    const response = await api.delete(`/bots/${id}`, options);
    return response.data;
  },

  // Helper endpoints often used in BotForm
  getProviders: async (options = {}) => {
    const response = await api.get('/ai-models/providers', options);
    return response.data;
  },

  getModels: async (providerId, type = null, options = {}) => {
    const response = await api.get(`/ai-models/providers/${providerId}/models`, {
      params: { model_type: type },
      ...options
    });
    return response.data;
  },

  getModelsByType: async (type, options = {}) => {
    const response = await api.get(`/ai-models/models/type/${type}`, options);
    return response.data;
  },
  
  // Knowledge Base linkage
  linkKnowledgeBase: async (botId, kbId, options = {}) => {
    // Logic depends on backend implementation, usually an update on Bot or a specific endpoint
    // Based on existing code, it might be part of updateBot
  }
};
