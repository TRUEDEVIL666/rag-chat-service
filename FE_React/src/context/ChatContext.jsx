import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getSessions, deleteSession, updateSession } from '../services/chatService';
import { useAuth } from './AuthContext';

const ChatContext = createContext(null);

export const ChatProvider = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [activeSession, setActiveSession] = useState(null); // { id: string, botId: string, botName: string, title?: string }
  const [sessions, setSessions] = useState([]);
  const [loadingSessions, setLoadingSessions] = useState(false);

  const fetchSessions = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      setLoadingSessions(true);
      const data = await getSessions({ limit: 20 }); // Increased limit
      setSessions(data);
    } catch (error) {
      console.error("Failed to fetch sessions", error);
    } finally {
      setLoadingSessions(false);
    }
  }, [isAuthenticated]);

  // Initial fetch
  useEffect(() => {
    if (isAuthenticated) {
      fetchSessions();
    }
  }, [isAuthenticated, fetchSessions]);

  const loadSession = useCallback((session) => {
    if (!session) {
      setActiveSession(null);
      return;
    }
    setActiveSession({
      id: session.id || session.session_id,
      botId: session.bot_id,
      botName: session.bot_name || session.bots?.name,
      title: session.summary_text || session.title,
      isExisting: true
    });
  }, []);

  const createNewSession = useCallback(() => {
    setActiveSession(null);
  }, []);

  const deleteSessionContext = async (sessionId) => {
    try {
      await deleteSession(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (activeSession?.id === sessionId) {
        setActiveSession(null);
      }
    } catch (error) {
      console.error("Failed to delete session", error);
    }
  };

  const updateSessionTitle = async (sessionId, title) => {
    try {
      await updateSession(sessionId, { summary_text: title });
      setSessions(prev => prev.map(s =>
        s.id === sessionId ? { ...s, summary_text: title, title: title } : s
      ));
      if (activeSession?.id === sessionId) {
        setActiveSession(prev => ({ ...prev, title }));
      }
    } catch (error) {
      console.error("Failed to update session title", error);
    }
  };

  return (
    <ChatContext.Provider value={{
      activeSession,
      setActiveSession,
      sessions,
      fetchSessions,
      loadSession,
      loadingSessions,
      createNewSession,
      deleteSession: deleteSessionContext,
      updateSessionTitle
    }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};
