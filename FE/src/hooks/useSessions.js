import { useState, useCallback } from 'react';
import { sessionService } from '../services/sessionService';

export const useSessions = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchSessions = useCallback(async (limit = 10, cursorTimestamp = null) => {
    setLoading(true);
    try {
      const data = await sessionService.getSessions(limit, cursorTimestamp);
      // Backend returns array of sessions directly
      setSessions(prev => cursorTimestamp ? [...prev, ...(data || [])] : (data || []));
      setError(null);
      return data; // Return data so caller can determine next cursor
    } catch (err) {
      console.error(err);
      setError(err);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    sessions,
    loading,
    error,
    fetchSessions
  };
};
