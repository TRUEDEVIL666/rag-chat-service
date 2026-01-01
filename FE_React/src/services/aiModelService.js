import api from './api';

export const aiModelService = {
  // Providers
  getProviders: async () => {
    const response = await api.get('/ai-models/providers');
    return response.data;
  },

  createProvider: async (data) => {
    const response = await api.post('/ai-models/providers', data);
    return response.data;
  },

  updateProvider: async (id, data) => {
    const response = await api.put(`/ai-models/providers/${id}`, data);
    return response.data;
  },

  deleteProvider: async (id) => {
    const response = await api.delete(`/ai-models/providers/${id}`);
    return response.data;
  },

  // Models
  getAllModels: async () => {
    const response = await api.get('/ai-models/models');
    return response.data;
  },

  getModelsByProvider: async (providerId, modelType = null) => {
    let url = `/ai-models/providers/${providerId}/models`;
    if (modelType) {
      url += `?model_type=${modelType}`;
    }
    const response = await api.get(url);
    return response.data;
  },

  getModelsByType: async (modelType) => {
    const response = await api.get(`/ai-models/models/type/${modelType}`);
    return response.data;
  },

  createModel: async (data) => {
    const response = await api.post('/ai-models/models', data);
    return response.data;
  },

  updateModel: async (id, data) => {
    const response = await api.put(`/ai-models/models/${id}`, data);
    return response.data;
  },

  deleteModel: async (id) => {
    const response = await api.delete(`/ai-models/models/${id}`);
    return response.data;
  }
};
