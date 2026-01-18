import { useState, useCallback } from 'react';
import { kbsService } from '../services/kbsService';

export const useKnowledgeBases = () => {
  const [kbs, setKbs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchKBs = useCallback(async () => {
    setLoading(true);
    try {
      const response = await kbsService.getKnowledgeBases();
      // Service returns response.data, which should be the list response structure
      // Based on kbsService.js and knowledge_base_api.py, response.data.data is the array
      setKbs(response.data || []); 
      setError(null);
    } catch (err) {
      console.error(err);
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  const createKB = useCallback(async (data) => {
    setLoading(true);
    try {
      const response = await kbsService.createKnowledgeBase(data);
      setKbs(prev => [response, ...prev]);
      setError(null);
      return response;
    } catch (err) {
      console.error(err);
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateKB = useCallback(async (id, data) => {
    setLoading(true);
    try {
      const response = await kbsService.updateKnowledgeBase(id, data);
      setKbs(prev => prev.map(kb => kb.id === id ? response : kb));
      setError(null);
      return response;
    } catch (err) {
      console.error(err);
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteKB = useCallback(async (id) => {
    setLoading(true);
    try {
      await kbsService.deleteKnowledgeBase(id);
      setKbs(prev => prev.filter(kb => kb.id !== id));
      setError(null);
    } catch (err) {
      console.error(err);
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    kbs,
    loading,
    error,
    fetchKBs,

    createKB,
    updateKB,
    deleteKB
  };
};
