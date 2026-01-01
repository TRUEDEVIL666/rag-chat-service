import api from './api';

export const documentService = {
  getDocuments: async (kbId) => {
    const response = await api.get(`/knowledge_bases/${kbId}/documents`);
    return response.data;
  },

  uploadDocuments: async (kbId, formData, onUploadProgress) => {
    // Backend expects knowledge_base_id as a form field in FileUploadRequest
    if (!formData.has('knowledge_base_id')) {
      formData.append('knowledge_base_id', kbId);
    }
    const response = await api.post('/documents/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
    return response.data;
  },

  deleteDocument: async (docId) => {
    const response = await api.delete(`/documents/${docId}`);
    return response.data;
  },

  batchDeleteDocuments: async (ids) => {
    const response = await api.post('/documents/batch-delete', { ids });
    return response.data;
  },

  retryDocument: async (docId) => {
    const response = await api.post(`/documents/${docId}/retry`);
    return response.data;
  }
};
