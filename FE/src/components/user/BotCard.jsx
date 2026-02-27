import React from 'react';

const BotCard = ({ icon, color, title, desc, onClick }) => {
  const colorMap = {
    blue: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-600 dark:text-blue-400' },
    orange: { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-600 dark:text-orange-400' },
    emerald: { bg: 'bg-emerald-100 dark:bg-emerald-900/30', text: 'text-emerald-600 dark:text-emerald-400' },
    purple: { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-600 dark:text-purple-400' },
    pink: { bg: 'bg-pink-100 dark:bg-pink-900/30', text: 'text-pink-600 dark:text-pink-400' },
  };
  const c = colorMap[color] || colorMap.blue;

  return (
    <div
      className="bot-card bg-white/60 dark:bg-gray-800/60 p-5 rounded-2xl border border-white/50 dark:border-gray-700 cursor-pointer hover:bg-white dark:hover:bg-gray-800 flex flex-col items-center text-center"
      onClick={onClick}
    >
      <div className={`w-10 h-10 ${c.bg} ${c.text} rounded-lg flex items-center justify-center mb-3`}>
        {icon}
      </div>
      <h4 className="font-bold text-slate-700 dark:text-slate-200">{title}</h4>
      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{desc}</p>
    </div>
  );
};

export default BotCard;
