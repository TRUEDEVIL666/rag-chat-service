import api from './api';

export const aiModelService = {
  // Providers
  getProviders: async (options = {}) => {
    const response = await api.get('/ai-models/providers', options);
    return response.data;
  },

  createProvider: async (data, options = {}) => {
    const response = await api.post('/ai-models/providers', data, options);
    return response.data;
  },

  updateProvider: async (id, data, options = {}) => {
    const response = await api.put(`/ai-models/providers/${id}`, data, options);
    return response.data;
  },

  deleteProvider: async (id, options = {}) => {
    const response = await api.delete(`/ai-models/providers/${id}`, options);
    return response.data;
  },

  // Models
  getAllModels: async (options = {}) => {
    const response = await api.get('/ai-models/models', options);
    return response.data;
  },

  getModelsByProvider: async (providerId, modelType = null, options = {}) => {
    let url = `/ai-models/providers/${providerId}/models`;
    if (modelType) {
      url += `?model_type=${modelType}`;
    }
    const response = await api.get(url, options);
    return response.data;
  },

  getModelsByType: async (modelType, options = {}) => {
    const response = await api.get(`/ai-models/models/type/${modelType}`, options);
    return response.data;
  },

  getProviderExternalModels: async (providerId, modelType, options = {}) => {
    let url = `/ai-models/providers/${providerId}/external-models`;
    if (modelType) {
      url += `?model_type=${modelType}`;
    }
    const response = await api.get(url, options);
    return response.data;
  },

  createModel: async (data, options = {}) => {
    const response = await api.post('/ai-models/models', data, options);
    return response.data;
  },

  updateModel: async (id, data, options = {}) => {
    const response = await api.put(`/ai-models/models/${id}`, data, options);
    return response.data;
  },

  deleteModel: async (id, options = {}) => {
    const response = await api.delete(`/ai-models/models/${id}`, options);
    return response.data;
  }
};
