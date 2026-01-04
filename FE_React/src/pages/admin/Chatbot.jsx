import React, { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import ChatInterface from '../../components/chat/ChatInterface';
import api from '../../services/api';
import { SpinnerIcon } from '@phosphor-icons/react';

const Chatbot = () => {
  const { id: botId } = useParams();
  const [searchParams] = useSearchParams();
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const urlSessionId = searchParams.get('sessionId');

    if (urlSessionId) {
      setSessionId(urlSessionId);
      setLoading(false);
      return;
    }

    if (botId) {
      setLoading(true);
      api.get(`/sessions?limit=1&offset=0&bot_id=${botId}`)
        .then(res => {
          if (res.data && res.data.length > 0) {
            setSessionId(res.data[0].id);
          }
          // If no session, sessionId remains null, and we pass botIdProp to ChatInterface 
          // which interprets it as "New Chat with this Bot"
        })
        .finally(() => setLoading(false));
    }
  }, [botId, searchParams]);

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
        key={sessionId || botId}
      />
    </div>
  );
};

export default Chatbot;
