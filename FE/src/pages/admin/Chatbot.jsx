import { useEffect, useState } from 'react';
import { useParams, useSearchParams, useLocation } from 'react-router-dom';
import ChatInterface from '../../components/chat/ChatInterface';
import { getSessions } from '../../services/chatService';
import { SpinnerIcon } from '@phosphor-icons/react';

/**
 * Chatbot Page Component (Admin)
 * 
 * Handles reading route parameters to determine which chat session to load.
 * - If `sessionId` is provided in URL or state, it loads that specific session.
 * - If `new=true` param is present, it initializes a fresh chat context.
 * - Otherwise, it fetches the most recent session for the given `botId`.
 */
const Chatbot = () => {
  const { botId } = useParams();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const [sessionId, setSessionId] = useState(null);
  // State defaults to FALSE to prevent infinite loading if logic fails
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Robustly get params
    const params = new URLSearchParams(location.search);
    const isNewChat = searchParams.get('new') === 'true' || params.get('new') === 'true';
    const urlSessionId = searchParams.get('sessionId') || location.state?.sessionId;

    if (urlSessionId) {
      setSessionId(urlSessionId);
      return;
    }

    if (botId) {
      if (isNewChat) {
        setSessionId(null);
        // No need to set loading false here because it defaults to false
        return;
      }

      setLoading(true);
      getSessions({ limit: 1, offset: 0, bot_id: botId })
        .then(data => {
          const sessions = Array.isArray(data) ? data : (data.items || []);
          if (sessions.length > 0) {
            setSessionId(sessions[0].id);
          }
        })
        .catch(err => {
          console.error("Failed to fetch initial session", err);
        })
        .finally(() => setLoading(false));
    }
  }, [botId, searchParams, location.search, location.state]);

  if (loading) {
    return <div className="h-full flex items-center justify-center text-gray-400"><SpinnerIcon className="animate-spin text-2xl" /></div>;
  }

  // If we found a session, use it. If not, pass botId so ChatInterface knows who we are talking to.
  // We use key={sessionId || botId} to force re-mount if switching contexts.
  return (
    <div className="h-full">
      <ChatInterface
        basePath="/admin/chat"
        homePath="/admin/bots"
        sessionIdProp={sessionId}
        botIdProp={botId}
        key={botId}
      />
    </div>
  );
};

export default Chatbot;
