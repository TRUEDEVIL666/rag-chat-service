import ChatHistoryInterface from '../../components/chat/ChatHistoryInterface';
import { useTranslation } from 'react-i18next';

const ChatHistory = () => {
  useTranslation();

  return <ChatHistoryInterface basePath="/admin/chat" />;
};

export default ChatHistory;
