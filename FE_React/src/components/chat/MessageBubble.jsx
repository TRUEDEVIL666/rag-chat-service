import {
  RobotIcon,
  ThumbsUpIcon,
  ThumbsDownIcon,
  CopyIcon
} from '@phosphor-icons/react';
import MarkdownRenderer from '../common/MarkdownRenderer';
import QuizRenderer from './QuizRenderer';

const MessageBubble = ({ role, text, senderName, botId, sessionId }) => {
  const isUser = role === 'user';

  // Try to parse quiz data
  let quizData = null;
  if (!isUser) {
    try {
      const content = text.trim();

      if (content.startsWith('[') && content.endsWith(']')) {
        const parsed = JSON.parse(content);
        if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].question && parsed[0].options) {
          quizData = parsed;
        }
      }
    } catch (e) {
      // Not JSON
    }
  }
  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} fade-in msg-container group`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center text-indigo-600 dark:text-indigo-400 mr-3 mt-1 shrink-0">
          <RobotIcon weight="fill" />
        </div>
      )}

      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[85%] md:max-w-[75%]`}>

        {senderName && (
          <span className={`text-sm font-medium text-slate-400 dark:text-slate-500 mb-1 ${isUser ? 'mr-1' : 'ml-1'}`}>
            {senderName}
          </span>
        )}

        <div className="flex items-start">
          <div className={`${isUser ? 'msg-user' : 'msg-bot'} p-4 text-sm md:text-base leading-relaxed`}>
            {isUser ? text : (
              quizData ? <QuizRenderer data={quizData} botId={botId} sessionId={sessionId} /> : <MarkdownRenderer content={text} />
            )}
          </div>
        </div>

        {!isUser && (
          <div className="flex items-center gap-2 mt-2 ml-2 feedback-actions">
            <button className="p-1.5 text-slate-400 dark:text-slate-500 hover:text-green-600 dark:hover:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/30 rounded-lg transition" title="Hữu ích">
              <ThumbsUpIcon />
            </button>
            <button className="p-1.5 text-slate-400 dark:text-slate-500 hover:text-red-500 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition" title="Không hữu ích">
              <ThumbsDownIcon />
            </button>
            <button
              className="p-1.5 text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition ml-auto"
              title="Sao chép"
              onClick={() => { navigator.clipboard.writeText(text); }}
            >
              <CopyIcon />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
