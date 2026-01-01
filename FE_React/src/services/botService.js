import api from './api';

export const botService = {
  getBots: async () => {
    const response = await api.get('/bots');
    return response.data;
  },

  getBot: async (id) => {
    const response = await api.get(`/bots/${id}`);
    return response.data;
  },

  createBot: async (botData) => {
    const response = await api.post('/bots', botData);
    return response.data;
  },

  updateBot: async (id, botData) => {
    const response = await api.patch(`/bots/${id}/config`, botData);
    return response.data;
  },

  deleteBot: async (id) => {
    const response = await api.delete(`/bots/${id}`);
    return response.data;
  },

  // Helper endpoints often used in BotForm
  getProviders: async () => {
    const response = await api.get('/ai-models/providers');
    return response.data;
  },

  getModels: async (providerId, type = null) => {
    const response = await api.get(`/ai-models/providers/${providerId}/models`, {
      params: { model_type: type }
    });
    return response.data;
  },

  getModelsByType: async (type) => {
    const response = await api.get(`/ai-models/models/type/${type}`);
    return response.data;
  },
  
  // Knowledge Base linkage
  linkKnowledgeBase: async (botId, kbId) => {
    // Logic depends on backend implementation, usually an update on Bot or a specific endpoint
    // Based on existing code, it might be part of updateBot
  }
};
