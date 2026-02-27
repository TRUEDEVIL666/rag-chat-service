import React from 'react';

/**
 * AgentStatusIndicator Component
 * 
 * Displays visual status indicators for agent activities with icons and colors.
 * Shows what the agent is currently doing (thinking, searching, verifying, etc.)
 */
const AgentStatusIndicator = ({ status }) => {
  // Map status messages to visual configurations
  const statusConfig = {
    "🤔 Thinking...": {
      icon: "🤔",
      color: "text-blue-600 dark:text-blue-400",
      bg: "bg-blue-50 dark:bg-blue-900/20",
      border: "border-blue-200 dark:border-blue-800"
    },
    "🔍 Searching knowledge bases...": {
      icon: "🔍",
      color: "text-purple-600 dark:text-purple-400",
      bg: "bg-purple-50 dark:bg-purple-900/20",
      border: "border-purple-200 dark:border-purple-800"
    },
    "📚 Searching documents...": {
      icon: "📚",
      color: "text-indigo-600 dark:text-indigo-400",
      bg: "bg-indigo-50 dark:bg-indigo-900/20",
      border: "border-indigo-200 dark:border-indigo-800"
    },
    "✓ Verifying response...": {
      icon: "✓",
      color: "text-green-600 dark:text-green-400",
      bg: "bg-green-50 dark:bg-green-900/20",
      border: "border-green-200 dark:border-green-800"
    },
    "📋 Listing knowledge bases...": {
      icon: "📋",
      color: "text-amber-600 dark:text-amber-400",
      bg: "bg-amber-50 dark:bg-amber-900/20",
      border: "border-amber-200 dark:border-amber-800"
    },
    "📝 Generating quiz...": {
      icon: "📝",
      color: "text-pink-600 dark:text-pink-400",
      bg: "bg-pink-50 dark:bg-pink-900/20",
      border: "border-pink-200 dark:border-pink-800"
    }
  };

  // Default configuration for unknown statuses
  const config = statusConfig[status] || {
    icon: "⏳",
    color: "text-gray-600 dark:text-gray-400",
    bg: "bg-gray-50 dark:bg-gray-900/20",
    border: "border-gray-200 dark:border-gray-800"
  };

  return (
    <div className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border ${config.bg} ${config.border} shadow-sm`}>
      <span className="text-lg animate-pulse">{config.icon}</span>
      <span className={`text-sm font-medium ${config.color}`}>{status}</span>
    </div>
  );
};

export default AgentStatusIndicator;
