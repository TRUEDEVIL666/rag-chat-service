import api from './api';

export const kbsService = {
  getKnowledgeBases: async () => {
    const response = await api.get('/knowledge_bases');
    return response.data;
  },
  
  createKnowledgeBase: async (data) => {
    const response = await api.post('/knowledge_bases', data);
    return response.data;
  },

  updateKnowledgeBase: async (id, data) => {
    const response = await api.patch(`/knowledge_bases/${id}`, data);
    return response.data;
  },

  deleteKnowledgeBase: async (id) => {
    const response = await api.delete(`/knowledge_bases/${id}`);
    return response.data;
  }
};
