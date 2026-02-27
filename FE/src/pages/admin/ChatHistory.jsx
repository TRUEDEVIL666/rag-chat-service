import ChatHistoryInterface from '../../components/chat/ChatHistoryInterface';
import { useOutletContext } from 'react-router-dom';
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

const ChatHistory = () => {
  const { t } = useTranslation();
  const { setTitle } = useOutletContext() || {};

  useEffect(() => {
    if (setTitle) setTitle(t('sidebar.history', 'Chat History'));
  }, [setTitle, t]);

  return <ChatHistoryInterface basePath="/admin/chat" />;
};

export default ChatHistory;
