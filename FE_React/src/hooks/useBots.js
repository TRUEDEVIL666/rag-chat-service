import { useState, useCallback } from 'react';
import { botService } from '../services/botService';

export const useBots = () => {
  const [bots, setBots] = useState([]);
  const [bot, setBot] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchBots = useCallback(async () => {
    setLoading(true);
    try {
      const data = await botService.getBots();
      setBots(data);
      setError(null);
    } catch (err) {
      setError(err);
      console.error("Failed to fetch bots", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchBot = useCallback(async (id) => {
    setLoading(true);
    try {
      const data = await botService.getBot(id);
      setBot(data);
      setError(null);
      return data;
    } catch (err) {
      setError(err);
      console.error("Failed to fetch bot", err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const createBot = useCallback(async (data) => {
    setLoading(true);
    try {
      const newBot = await botService.createBot(data);
      setBots(prev => [newBot, ...prev]);
      setError(null);
      return newBot;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateBot = useCallback(async (id, data) => {
    setLoading(true);
    try {
      const updatedBot = await botService.updateBot(id, data);
      setBots(prev => prev.map(b => b.id === id ? updatedBot : b));
      setBot(updatedBot);
      setError(null);
      return updatedBot;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteBot = useCallback(async (id) => {
    setLoading(true);
    try {
      await botService.deleteBot(id);
      setBots(prev => prev.filter(b => b.id !== id));
      setError(null);
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    bots,
    bot,
    loading,
    error,
    fetchBots,
    fetchBot,
    createBot,
    updateBot,
    deleteBot
  };
};

export const useBotOptions = () => {
  const [providers, setProviders] = useState([]);
  const [models, setModels] = useState([]);
  const [rerankers, setRerankers] = useState([]);
  const [embeddingModels, setEmbeddingModels] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchProviders = useCallback(async () => {
    setLoading(true);
    try {
      const data = await botService.getProviders();
      setProviders(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchModels = useCallback(async (providerId, type = null) => {
    if (!providerId) return;
    setLoading(true);
    try {
      const data = await botService.getModels(providerId, type);
      setModels(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchRerankers = useCallback(async () => {
    try {
      const data = await botService.getModelsByType('reranker');
      setRerankers(data);
    } catch (err) {
      console.error(err);
    }
  }, []);

  const fetchEmbeddingModels = useCallback(async () => {
    try {
      const data = await botService.getModelsByType('embedding');
      setEmbeddingModels(data);
    } catch (err) {
      console.error(err);
    }
  }, []);

  return {
    providers,
    models,
    rerankers,
    embeddingModels,
    loading,
    fetchProviders,
    fetchModels,
    fetchRerankers,
    fetchEmbeddingModels
  };
};
