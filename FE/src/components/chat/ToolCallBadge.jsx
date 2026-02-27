import React from 'react';

/**
 * ToolCallBadge Component
 * 
 * Displays a badge showing what tool the agent used and with what parameters.
 * Shows inline above bot messages to provide transparency into agent decisions.
 */
const ToolCallBadge = ({ tool, input }) => {
  const getToolDisplay = () => {
    switch (tool) {
      case 'search_knowledge_base':
        const query = input?.query || input?.q || 'documents';
        return {
          icon: '🔍',
          text: `Searched for: "${query}"`,
          color: 'bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800'
        };

      case 'list_knowledge_bases':
        return {
          icon: '📋',
          text: 'Listed knowledge bases',
          color: 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800'
        };

      case 'QuizOutput':
        return {
          icon: '📝',
          text: 'Generated quiz',
          color: 'bg-pink-50 dark:bg-pink-900/20 text-pink-700 dark:text-pink-300 border-pink-200 dark:border-pink-800'
        };

      default:
        return {
          icon: '🔧',
          text: `Used ${tool}`,
          color: 'bg-gray-50 dark:bg-gray-900/20 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-800'
        };
    }
  };

  const { icon, text, color } = getToolDisplay();

  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${color}`}>
      <span className="text-sm">{icon}</span>
      <span>{text}</span>
    </div>
  );
};

export default ToolCallBadge;
