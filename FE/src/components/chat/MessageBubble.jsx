import { useState } from 'react';
import {
  RobotIcon,
  ThumbsUpIcon,
  ThumbsDownIcon,
  CopyIcon,
  CheckIcon
} from '@phosphor-icons/react';
import MarkdownRenderer from '../common/MarkdownRenderer';
import QuizRenderer from './QuizRenderer';
import ToolCallBadge from './ToolCallBadge';

const MessageBubble = ({ id, role, text, rating, senderName, botId, sessionId, onRate, toolCalls }) => {
  const isUser = role === 'user';
  const [copied, setCopied] = useState(false);

  const handleRate = (type) => {
    if (onRate) {
      // Toggle if already selected
      const newRating = rating === type ? null : type;
      onRate(id, newRating);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

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
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} group max-w-none`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-lg bg-indigo-100 dark:bg-indigo-500/10 flex items-center justify-center text-indigo-600 dark:text-indigo-400 mr-3 mt-0.5 shrink-0 border border-indigo-200 dark:border-indigo-500/20 shadow-sm">
          <RobotIcon size={20} weight="duotone" />
        </div>
      )}

      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[85%] md:max-w-[75%]`}>

        <div className="flex items-center gap-2 mb-1">
          <span className={`text-xs font-semibold ${isUser ? 'text-indigo-600 dark:text-indigo-400' : 'text-gray-900 dark:text-white'}`}>
            {senderName || (isUser ? 'You' : 'AI')}
          </span>
        </div>

        {/* Tool calls display */}
        {!isUser && toolCalls && toolCalls.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3 ml-1">
            {toolCalls.map((tc, idx) => (
              <ToolCallBadge key={idx} tool={tc.tool} input={tc.input} />
            ))}
          </div>
        )}

        <div className={`relative px-5 py-3.5 text-sm md:text-[15px] leading-relaxed shadow-sm
          ${isUser
            ? 'bg-indigo-600 text-white rounded-2xl rounded-tr-sm'
            : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 rounded-2xl rounded-tl-sm border border-gray-100 dark:border-gray-700'
          }`}
        >
          {isUser ? text : (
            quizData ? <QuizRenderer data={quizData} botId={botId} sessionId={sessionId} /> : <MarkdownRenderer content={text} />
          )}
        </div>

        {/* Feedback Actions - Only for Bot */}
        {!isUser && id && (
          <div className="flex items-center gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <button
              onClick={() => handleRate('thumbs_up')}
              className={`p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition ${rating === 'thumbs_up' ? 'text-green-600' : 'text-gray-400 hover:text-green-600'}`}
              title="Helpful"
            >
              <ThumbsUpIcon size={16} weight={rating === 'thumbs_up' ? 'fill' : 'regular'} />
            </button>
            <button
              onClick={() => handleRate('thumbs_down')}
              className={`p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition ${rating === 'thumbs_down' ? 'text-red-500' : 'text-gray-400 hover:text-red-500'}`}
              title="Not Helpful"
            >
              <ThumbsDownIcon size={16} weight={rating === 'thumbs_down' ? 'fill' : 'regular'} />
            </button>
            <button
              className="p-1.5 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition ml-2"
              title={copied ? "Copied!" : "Copy"}
              onClick={handleCopy}
            >
              {copied ? <CheckIcon size={16} className="text-green-500" /> : <CopyIcon size={16} />}
            </button>
          </div>
        )}
      </div>

      {/* User Avatar (Optional, if we have one) */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold shadow-md ml-3 mt-0.5 shrink-0">
          U
        </div>
      )}
    </div>
  );
};

export default MessageBubble;
