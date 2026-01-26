import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ROUTES } from '../../routes';
import {
  MagnifyingGlassIcon,
  StudentIcon,
  FilesIcon,
  BooksIcon,
  RobotIcon,
  ClockCounterClockwiseIcon,
  CaretRightIcon,
  ChatCircleDotsIcon,
  SparkleIcon
} from '@phosphor-icons/react';
import { useTranslation, Trans } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import { useChat } from '../../context/ChatContext';
import courseService from '../../services/courseService';
import BotCard from '../../components/user/BotCard';
import Skeleton from '../../components/common/Skeleton';



const UserHome = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { setActiveSession, sessions } = useChat(); // Added sessions
  const navigate = useNavigate();

  const [inputValue, setInputValue] = useState('');
  const [availableBots, setAvailableBots] = useState([]);
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const isSearchActive = isSearchFocused || inputValue.trim().length > 0;

  useEffect(() => {
    const controller = new AbortController();
    const fetchBots = async () => {
      try {
        setIsLoading(true);
        const bots = await courseService.getMyClassBots({ signal: controller.signal });
        if (controller.signal.aborted) return;
        setAvailableBots(bots);
      } catch (error) {
        if (error.code === 'ERR_CANCELED' || error.name === 'AbortError') return;
        console.error("Failed to fetch bots", error);
      } finally {
        if (!controller.signal.aborted) setIsLoading(false);
      }
    };
    fetchBots();
    return () => controller.abort();
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
      const bot = queryOrBot;
      setActiveSession({ botId: bot.id, botName: bot.name, title: "New Chat", isExisting: false });
      navigate(ROUTES.USER.CHAT(bot.id), { state: { bot } });
      return;
    }

    const query = typeof queryOrBot === 'string' ? queryOrBot : inputValue;
    if (!query.trim()) return;

    if (filteredBots.length > 0) {
      const targetBot = filteredBots[0];
      setActiveSession({ botId: targetBot.id, botName: targetBot.name, title: "New Chat", isExisting: false });
      navigate(ROUTES.USER.CHAT(targetBot.id), { state: { bot: targetBot } });
    }
  };

  const handleResumeSession = (session) => {
    setActiveSession(session);
    navigate(ROUTES.USER.CHAT(session.id));
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleStartChat(inputValue);
    }
  };

  // Get recent 3 sessions
  const recentSessions = sessions?.slice(0, 3) || [];

  return (
    <>
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-6 py-12 space-y-16">

          {/* 1. Hero Section (Greeting & Search) */}
          <div className="text-center space-y-0 mt-4 md:mt-12 transition-all duration-700 ease-in-out">
            <div className={`transition-all duration-700 ease-in-out overflow-hidden transform ${isSearchActive ? 'max-h-0 opacity-0 -translate-y-10 mb-0' : 'max-h-[300px] opacity-100 translate-y-0 mb-8'}`}>
              <h1 className="text-4xl md:text-6xl font-extrabold text-white mb-6 tracking-tight drop-shadow-lg">
                <Trans i18nKey="home.welcome_user" values={{ name: user?.username || 'Student' }}>
                  Hello, <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 via-blue-400 to-purple-400">Student</span> 👋
                </Trans>
              </h1>
              <p className="text-slate-500 dark:text-slate-400 text-xl font-light max-w-2xl mx-auto">
                {t('home.subtitle', 'What would you like to learn or explore today?')}
              </p>
            </div>

            {/* Glassmorphism Search Bar */}
            <div className="relative w-full max-w-2xl mx-auto group z-20">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-500"></div>
              <div className="relative bg-white dark:bg-slate-900 rounded-2xl shadow-2xl flex items-center p-2 transition-transform duration-300 group-hover:scale-[1.01]">
                <MagnifyingGlassIcon className="text-2xl text-slate-400 ml-4" />
                <input
                  type="text"
                  className="flex-1 bg-transparent border-none outline-none text-lg py-4 px-4 text-slate-800 dark:text-slate-200 placeholder:text-slate-400 font-medium"
                  placeholder={t('home.search_placeholder', 'Ask anything or search for an assistant...')}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  onFocus={() => setIsSearchFocused(true)}
                  onBlur={() => setTimeout(() => setIsSearchFocused(false), 200)}
                />
                <button
                  onClick={() => handleStartChat(inputValue)}
                  className="p-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl shadow-lg shadow-indigo-500/30 transition-all duration-200 active:scale-95"
                >
                  <CaretRightIcon weight="bold" className="text-xl" />
                </button>
              </div>
            </div>
          </div>

          {/* 2. Rapid Access / Recent Activity (Only show if not searching) */}
          {!isSearchActive && recentSessions.length > 0 && (
            <div className="space-y-6 animate-fade-in-up">
              <div className="flex items-center gap-2 text-slate-400 text-sm font-semibold uppercase tracking-wider mx-1">
                <ClockCounterClockwiseIcon className="text-lg" />
                {t('home.recent_activity', 'Jump back in')}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {recentSessions.map(session => (
                  <div
                    key={session.id}
                    onClick={() => handleResumeSession(session)}
                    className="group bg-white dark:bg-slate-900/50 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-indigo-500/50 dark:hover:border-indigo-500/50 hover:shadow-lg hover:shadow-indigo-500/10 transition-all duration-300 cursor-pointer flex flex-col justify-between h-32 relative overflow-hidden"
                  >
                    {/* Decoration */}
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                      <ChatCircleDotsIcon size={64} className="text-indigo-500 transform rotate-12" />
                    </div>

                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-300 border border-indigo-100 dark:border-indigo-500/20">
                          {session.bots?.name || 'Chat'}
                        </span>
                        <span className="text-xs text-slate-400">{new Date(session.updated_at || session.created_at).toLocaleDateString()}</span>
                      </div>
                      <h3 className="font-semibold text-slate-700 dark:text-slate-200 line-clamp-2 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                        {session.summary_text || t('chatbot.new_chat')}
                      </h3>
                    </div>

                    <div className="flex items-center gap-1 text-xs font-medium text-indigo-600 dark:text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity transform translate-y-2 group-hover:translate-y-0 duration-300">
                      Continue <CaretRightIcon />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 3. Explore Assistants (Filtered List) */}
          <div className="space-y-6 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
            <div className="flex items-center justify-between mx-1">
              <div className="flex items-center gap-2 text-slate-400 text-sm font-semibold uppercase tracking-wider">
                <SparkleIcon className="text-lg" />
                {t('home.suggestions.available_bots', 'Explore Assistants')}
              </div>
            </div>

            {isLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="bg-white/60 dark:bg-gray-800/60 rounded-2xl p-5 border border-white/50 dark:border-gray-700 shadow-sm h-48 flex flex-col items-center justify-center space-y-4">
                    {/* Icon Skeleton */}
                    <Skeleton className="w-10 h-10 rounded-lg" />

                    <div className="space-y-2 w-full flex flex-col items-center">
                      {/* Title Skeleton */}
                      <Skeleton className="h-5 w-3/4 rounded" />
                      {/* Desc Skeleton */}
                      <Skeleton className="h-3 w-full rounded" />
                      <Skeleton className="h-3 w-2/3 rounded" />
                    </div>
                  </div>
                ))}
              </div>
            ) : filteredBots.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
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
            ) : (
              <div className="text-center py-12">
                <div className="text-slate-300 dark:text-slate-600 mb-2">
                  <MagnifyingGlassIcon size={48} className="mx-auto" />
                </div>
                <p className="text-slate-500 dark:text-slate-400">No assistants found matching "{inputValue}"</p>
              </div>
            )}
          </div>

        </div>
      </main>
    </>
  );
};

export default UserHome;
