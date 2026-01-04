import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MagnifyingGlassIcon,
  StudentIcon,
  FilesIcon,
  BooksIcon,
  RobotIcon
} from '@phosphor-icons/react';
import { useTranslation, Trans } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import { useChat } from '../../context/ChatContext';
import BotCard from '../../components/user/BotCard';
import { botService } from '../../services/botService';

const UserHome = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { setActiveSession } = useChat();
  const navigate = useNavigate();

  const [inputValue, setInputValue] = useState('');
  const [availableBots, setAvailableBots] = useState([]);
  const [isSearchFocused, setIsSearchFocused] = useState(false);

  const isSearchActive = isSearchFocused || inputValue.trim().length > 0;

  useEffect(() => {
    const fetchBots = async () => {
      try {
        const bots = await botService.getBots();
        setAvailableBots(bots);
      } catch (error) {
        console.error("Failed to fetch bots", error);
      }
    };
    fetchBots();
  }, []);

  const getBotVisuals = (bot) => {
    const name = bot.name.toLowerCase();
    if (name.includes('academic') || name.includes('student') || name.includes('sinh viên')) return { icon: <StudentIcon weight="fill" className="text-xl" />, color: 'blue' };
    if (name.includes('admin') || name.includes('staff')) return { icon: <FilesIcon weight="fill" className="text-xl" />, color: 'orange' };
    if (name.includes('library') || name.includes('thư viện')) return { icon: <BooksIcon weight="fill" className="text-xl" />, color: 'emerald' };
    return { icon: <RobotIcon weight="fill" className="text-xl" />, color: 'indigo' };
  };

  const filteredBots = availableBots.filter(b => b.name.toLowerCase().includes(inputValue.toLowerCase()));

  const handleStartChat = (queryOrBot, isBotObj = false) => {
    if (isBotObj) {
      // Starting chat via clicking a bot card
      const bot = queryOrBot;

      // Update Context
      setActiveSession({ botId: bot.id, botName: bot.name, title: "New Chat", isExisting: false });

      // Navigate to /user/chat with bot state
      navigate('/user/chat', { state: { bot } });
      return;
    }

    // Starting chat via search bar (query)
    const query = typeof queryOrBot === 'string' ? queryOrBot : inputValue;
    if (!query.trim()) return;

    if (filteredBots.length > 0) {
      const targetBot = filteredBots[0];
      setActiveSession({ botId: targetBot.id, botName: targetBot.name, title: "New Chat", isExisting: false });
      // Navigate to /user/chat with bot state
      navigate('/user/chat', { state: { bot: targetBot } });
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleStartChat(inputValue);
    }
  };

  return (
    <>
      {/* CONTENT AREA */}
      <main className="flex-1 overflow-hidden relative flex flex-col">
        <div className="flex-1 flex flex-col items-center justify-start p-4 transition-all duration-500 ease-in-out">
          {/* Animated Spacer for smooth search transition */}
          <div className={`transition-all duration-500 ease-in-out shrink-0 ${isSearchActive ? 'h-4' : 'h-[30vh]'}`}></div>

          <div className="w-full max-w-3xl space-y-8 text-center">
            <div className={`transition-all duration-500 ease-in-out ${isSearchActive ? 'opacity-0 max-h-0 overflow-hidden' : 'opacity-100 max-h-40'}`}>
              <h1 className="text-3xl md:text-4xl font-bold text-slate-800 dark:text-white mb-2">
                <Trans i18nKey="home.welcome_user" values={{ name: user?.username || 'Sinh viên' }}>
                  Xin chào, <span className="text-indigo-600 dark:text-indigo-400">Sinh viên</span> 👋
                </Trans>
              </h1>
              <p className="text-slate-400 dark:text-slate-500 text-lg">{t('home.subtitle')}</p>
            </div>

            {/* Search Bar */}
            <div className="relative w-full group max-w-2xl mx-auto">
              <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-2xl blur opacity-20 dark:opacity-40 group-hover:opacity-30 dark:group-hover:opacity-50 transition duration-500"></div>
              <div className="relative bg-white dark:bg-gray-800 rounded-2xl search-bar-shadow p-2 flex items-center">
                <MagnifyingGlassIcon className="text-xl text-slate-400 dark:text-slate-500 ml-3" />
                <input
                  type="text"
                  className="flex-1 bg-transparent border-none outline-none text-lg py-3 px-4 placeholder:text-slate-300 dark:placeholder:text-slate-600 dark:text-slate-200"
                  placeholder={t('home.search_placeholder')}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  onFocus={() => setIsSearchFocused(true)}
                  onBlur={() => setTimeout(() => setIsSearchFocused(false), 200)}
                />
                <button
                  onClick={() => handleStartChat(inputValue)}
                  className="p-2 bg-indigo-600 text-white rounded-xl shadow-md hover:bg-indigo-700 transition"
                >
                  <MagnifyingGlassIcon weight="bold" className="text-xl" />
                </button>
              </div>
            </div>

            {/* Specialized Bots / Grid */}
            <div className={`transition-all duration-500 ease-in-out ${isSearchActive ? 'opacity-100 translate-y-0 max-h-[70vh] overflow-y-auto custom-scrollbar' : 'opacity-0 translate-y-10 max-h-0 overflow-hidden'}`}>
              <div className="text-left text-sm font-semibold text-slate-400 mb-4">{t('home.suggestions.available_bots')}</div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pb-4">
                {filteredBots.map(bot => {
                  const visuals = getBotVisuals(bot);
                  return (
                    <BotCard
                      key={bot.id}
                      icon={visuals.icon}
                      color={visuals.color}
                      title={bot.name}
                      desc={bot.description}
                      onClick={() => handleStartChat(bot, true)}
                    />
                  );
                })}
              </div>
            </div>

          </div>
        </div>
      </main>
    </>
  );
};

export default UserHome;
