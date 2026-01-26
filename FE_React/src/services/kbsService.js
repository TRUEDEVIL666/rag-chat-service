import api from './api';

export const kbsService = {
  getKnowledgeBases: async (options = {}) => {
    const response = await api.get('/knowledge_bases', options);
    return response.data;
  },
  
  createKnowledgeBase: async (data, options = {}) => {
    const response = await api.post('/knowledge_bases', data, options);
    return response.data;
  },

  updateKnowledgeBase: async (id, data, options = {}) => {
    const response = await api.patch(`/knowledge_bases/${id}`, data, options);
    return response.data;
  },

  deleteKnowledgeBase: async (id, options = {}) => {
    const response = await api.delete(`/knowledge_bases/${id}`, options);
    return response.data;
  }
};
