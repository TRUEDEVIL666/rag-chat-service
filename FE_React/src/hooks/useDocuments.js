import { useState, useCallback } from 'react';
import { documentService } from '../services/documentService';
import { kbsService } from '../services/kbsService';

export const useDocuments = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDocuments = useCallback(async (kbId, options = {}) => {
    setLoading(true);
    try {
      const { data } = await documentService.getDocuments(kbId, options);
      if (options.signal?.aborted) return;
      setDocuments(data);
      setError(null);
    } catch (err) {
      if (err.code === 'ERR_CANCELED' || err.name === 'AbortError') return;
      setError(err);
      console.error("Failed to fetch documents", err);
    } finally {
      if (!options.signal?.aborted) setLoading(false);
    }
  }, []);

  const deleteDocument = useCallback(async (id) => {
    try {
      await documentService.deleteDocument(id);
      setDocuments(prev => prev.filter(doc => doc.id !== id));
    } catch (err) {
      console.error("Delete failed", err);
      throw err;
    }
  }, []);

  const batchDeleteDocuments = useCallback(async (ids) => {
    try {
      await documentService.batchDeleteDocuments(ids);
      const idSet = new Set(ids);
      setDocuments(prev => prev.filter(doc => !idSet.has(doc.id)));
    } catch (err) {
      console.error("Batch delete failed", err);
      throw err;
    }
  }, []);

  const uploadDocuments = useCallback(async (kbId, formData, onProgress) => {
    try {
      await documentService.uploadDocuments(kbId, formData, onProgress);
      // Usually user refreshes list after upload
    } catch (err) {
      console.error("Upload failed", err);
      throw err;
    }
  }, []);

  return {
    documents,
    loading,
    error,
    fetchDocuments,
    deleteDocument,
    batchDeleteDocuments,
    uploadDocuments,
    retryDocument: documentService.retryDocument
  };
};


