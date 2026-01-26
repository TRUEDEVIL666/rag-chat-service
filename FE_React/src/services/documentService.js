import api from './api';

export const documentService = {
  getDocuments: async (kbId, options = {}) => {
    const response = await api.get(`/knowledge_bases/${kbId}/documents`, options);
    return response.data;
  },

  uploadDocuments: async (kbId, formData, onUploadProgress, options = {}) => {
    // Backend expects knowledge_base_id as a form field in FileUploadRequest
    if (!formData.has('knowledge_base_id')) {
      formData.append('knowledge_base_id', kbId);
    }
    const response = await api.post('/documents/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
      ...options
    });
    return response.data;
  },

  deleteDocument: async (docId, options = {}) => {
    const response = await api.delete(`/documents/${docId}`, options);
    return response.data;
  },

  batchDeleteDocuments: async (ids, options = {}) => {
    const response = await api.post('/documents/batch-delete', { ids }, options);
    return response.data;
  },

  retryDocument: async (docId, options = {}) => {
    const response = await api.post(`/documents/${docId}/retry`, {}, options);
    return response.data;
  },

  getDocumentDownloadUrl: async (docId, options = {}) => {
    const response = await api.get(`/documents/${docId}/download`, options);
    return response.data.url;
  }
};
