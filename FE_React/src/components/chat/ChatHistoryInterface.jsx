import React, { useMemo } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { ClockCounterClockwise, MagnifyingGlass, List, ChatsCircle } from '@phosphor-icons/react';
import { useChat } from '../../context/ChatContext';
import { useTranslation } from 'react-i18next';

const ChatHistoryInterface = ({ basePath }) => {
  const { toggleSidebar } = useOutletContext() || {};
  const { loadSession } = useChat();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [historySessions, setHistorySessions] = React.useState([]);
  const [search, setSearch] = React.useState('');
  const [dateRange, setDateRange] = React.useState({ start: '', end: '' });
  const [loading, setLoading] = React.useState(false);

  // Admin portal might not have 'chat' context properly populating sessions if it uses different state, 
  // but getSessions is API level.
  // Note: loadSession updates UserContext.Admin might need its own context or just navigating.
  // Ideally, clicking a session in Admin -> navigates to /admin/chat/:id

  const fetchHistory = React.useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        limit: 100,
        search: search || undefined,
        start_date: dateRange.start ? new Date(dateRange.start).toISOString() : undefined,
        end_date: dateRange.end ? new Date(dateRange.end).toISOString() : undefined,
      };

      const data = await import('../../services/chatService').then(m => m.getSessions(params));
      setHistorySessions(data);
    } catch (err) {
      console.error("Failed to fetch history", err);
    } finally {
      setLoading(false);
    }
  }, [search, dateRange]);

  React.useEffect(() => {
    const timer = setTimeout(() => {
      fetchHistory();
    }, 500); // Debounce
    return () => clearTimeout(timer);
  }, [fetchHistory]);

  const groupedSessions = useMemo(() => {
    const groups = {};
    if (!historySessions) return groups;

    historySessions.forEach(session => {
      const date = new Date(session.updated_at || session.created_at);
      const key = date.toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
      if (!groups[key]) groups[key] = [];
      groups[key].push(session);
    });
    return groups;
  }, [historySessions]);

  const handleSessionClick = (session) => {
    // For User: loadSession updates context, then navigate to /user/chat (which reads context) OR /user/chat/:id
    // For Admin: loadSession updates context (maybe same context?), then navigate to /admin/chat/:id
    // To be safe and explicit: Navigate to `${basePath}/${session.id}`
    // If we use loadSession from context, it updates the "Active Session" in global state.

    // Check if we are in Admin or User mode based on basePath or props?
    // Doing both is fine if they share Context.
    loadSession(session);
    // UserChat usually redirects to /user/home if "Chat" is clicked without ID, but here we have ID.
    // Wait, UserChat logic: /user/chat/:sessionId -> loads session.
    // So we should navigate to `${basePath}/${session.id}`.
    // But original UserChatHistory navigated to `/user/home`?
    // Original: `loadSession(session); navigate('/user/home');` 
    // This is because /user/home is the main chat view in previous architecture?
    // NO, /user/home is the Bot Selection screen. /user/chat is the chat.
    // Let's check `UserChatHistory.jsx` original code again.
    // Line 60: `navigate('/user/home');`
    // This seems weird if it's history. Usually you go to /user/chat.
    // Maybe /user/home renders the chat if activeSession is set?
    // Let's Look at `UserHome.jsx` logic? 
    // Actually, `UserChat` is at `/user/chat`. 
    // If I click history, I want to go to the chat.
    // Let's assume standard behavior: Navigate to chat page with session ID.

    if (basePath.includes('admin')) {
      // Admin: /admin/chat/:botId is the route mapped to Chatbot.jsx.
      // AND we just updated Chatbot.jsx to accept prop sessionId or resolve it.
      // BUT currently Chatbot.jsx expects :id to be BOT_ID in URL?
      // Let's re-read Chatbot.jsx.
      // `const { id: botId } = useParams();` -> It interprets ID as BotID.
      // If we navigate to `/admin/chat/${session.bot_id}`, it loads the latest session for that bot.
      // It doesn't strictly support opening a *specific* session ID from URL yet, unless we change route.
      // OR we pass state.

      navigate(`${basePath}/${session.bot_id}`, { state: { sessionId: session.id } });
      // We need to update Chatbot.jsx to read location.state?.sessionId too?
      // Update: Chatbot.jsx uses ChatInterface. ChatInterface reads sessionId from props or params.
      // Chatbot.jsx currently checks for existing session for bot. 
      // If we pass state, we should use it.
    } else {
      // User: /user/chat/:sessionId
      navigate(`${basePath}/${session.id}`);
    }
  };

  return (
    <>
      {/* Header */}
      <header className="h-16 border-b border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-gray-900/50 backdrop-blur flex items-center justify-between px-6 shrink-0 transition-colors duration-300">
        <div className="flex items-center gap-3">
          {toggleSidebar && (
            <button onClick={toggleSidebar} className="md:hidden p-2 text-slate-500 dark:text-slate-400 hover:bg-white/50 dark:hover:bg-slate-800 rounded-lg">
              <List className="text-xl" />
            </button>
          )}
          <h1 className="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
            <ClockCounterClockwise weight="fill" className="text-indigo-600 dark:text-indigo-500" />
            {t('nav.history', 'Lịch sử trò chuyện')}
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <input
              type="date"
              className="px-2 py-1.5 bg-white dark:bg-gray-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs"
              value={dateRange.start}
              onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
            />
            <span className="text-slate-400">-</span>
            <input
              type="date"
              className="px-2 py-1.5 bg-white dark:bg-gray-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs"
              value={dateRange.end}
              onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
            />
          </div>
          <div className="relative">
            <MagnifyingGlass className="absolute left-3 top-2.5 text-slate-400 dark:text-slate-500" />
            <input
              type="text"
              placeholder={t('home.search_placeholder', 'Tìm kiếm...')}
              className="pl-10 pr-4 py-2 bg-white dark:bg-gray-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 w-64 placeholder:text-slate-400 dark:placeholder:text-slate-600 transition-colors"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-6 bg-slate-50/50 dark:bg-gray-900/50 transition-colors duration-300">
        <div className="max-w-4xl mx-auto space-y-8">
          {loading && <div className="text-center py-10 text-slate-400">Loading...</div>}

          {!loading && Object.keys(groupedSessions).length === 0 && (
            <div className="text-center py-20">
              <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-400 dark:text-slate-500">
                <ChatsCircle weight="duotone" className="text-3xl" />
              </div>
              <h3 className="text-slate-500 dark:text-slate-400 font-medium">Chưa có lịch sử trò chuyện</h3>
            </div>
          )}

          {Object.entries(groupedSessions).map(([month, monthSessions]) => (
            <div key={month} className="animate-fade-in-up">
              <h3 className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-3 px-2">{month}</h3>
              <div className="bg-white/60 dark:bg-gray-800/60 backdrop-blur border border-slate-200 dark:border-slate-700/50 rounded-xl overflow-hidden shadow-sm dark:shadow-none">
                {monthSessions.map((session, index) => (
                  <HistoryItem
                    key={session.id || session.session_id}
                    title={session.title || session.bots?.name || session.bot_name || t('chatbot.new_chat')}
                    date={new Date(session.updated_at || session.created_at).toLocaleDateString()}
                    snippet={session.summary_text || "..."}
                    last={index === monthSessions.length - 1}
                    onClick={() => handleSessionClick(session)}
                  />
                ))}
              </div>
            </div>
          ))}

        </div>
      </main>
    </>
  );
};

const HistoryItem = ({ title, date, snippet, last = false, onClick }) => (
  <div
    onClick={onClick}
    className={`p-4 ${!last ? 'border-b border-slate-100 dark:border-slate-700/50' : ''} hover:bg-white dark:hover:bg-gray-700/50 transition cursor-pointer group`}
  >
    <div className="flex justify-between items-start mb-1">
      <h4 className="font-medium text-slate-700 dark:text-slate-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition">{title}</h4>
      <span className="text-xs text-slate-400 dark:text-slate-500">{date}</span>
    </div>
    <p className="text-sm text-slate-500 dark:text-slate-400 line-clamp-2">{snippet}</p>
  </div>
);

export default ChatHistoryInterface;
