import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
  PaperPlaneRightIcon,
  RobotIcon,
  PaperclipIcon,
  SpinnerIcon
} from '@phosphor-icons/react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import { useChat } from '../../context/ChatContext';
import MessageBubble from './MessageBubble';
import { streamChatResponse, getSessionMessages, getSession } from '../../services/chatService';
import QuizHistoryModal from './QuizHistoryModal';
import { botService } from '../../services/botService';

const ChatInterface = ({ basePath = '/user/chat', homePath = '/user/home', sessionIdProp = null, botIdProp = null }) => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { activeSession, setActiveSession, fetchSessions } = useChat();
  const { sessionId: paramSessionId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const sessionId = sessionIdProp || paramSessionId;

  const [inputValue, setInputValue] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [isTyping, setIsTyping] = useState(false);

  const [isQuizMode, setIsQuizMode] = useState(false);
  const [showQuizHistory, setShowQuizHistory] = useState(false);

  const chatBottomRef = useRef(null);
  const scrollContainerRef = useRef(null);
  const shouldAutoScrollRef = useRef(true);

  // State for Infinite Scroll
  const [nextCursor, setNextCursor] = useState(null);
  const [isFetchingMore, setIsFetchingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);

  // Initial setup: Handle routing and state initialization
  useEffect(() => {
    const initializeSession = async () => {
      // If we have a sessionId (prop or param), we load that session
      if (sessionId) {
        if (activeSession?.id !== sessionId) {
          // Context update handled inside loadSessionAndMessages or redundant
        }
        await loadSessionAndMessages(sessionId);
      } else {
        // No sessionId (New Chat)
        // Check if we have activeSession state passed from Home (bot selection)
        const botState = location.state?.bot;
        const targetBotId = botIdProp || botState?.id;
        let targetBotName = botState?.name;

        if (targetBotId) {
          // If we have an ID but no name, fetch it
          if (!targetBotName) {
            try {
              const botDetails = await botService.getBot(targetBotId);
              targetBotName = botDetails.name;
            } catch (err) {
              console.error("Failed to fetch bot details for new chat", err);
              // Avoid showing empty bot name if fetch fails
              targetBotName = null;
            }
          }

          setChatHistory([{
            role: 'bot',
            text: targetBotName ? t('chatbot.welcome', { name: targetBotName }) : t('chatbot.welcome_generic', "Start a conversation..."),
            timestamp: new Date(),
            isIntro: true,
            senderName: targetBotName || 'Bot'
          }]);
          setNextCursor(null);
          setHasMore(false);

          // Update context if not set or different
          // We check against targetBotId to ensure synchronization
          if (!activeSession || activeSession.botId !== targetBotId || !activeSession.botName) {
            setActiveSession({
              botId: targetBotId,
              botName: targetBotName,
              title: 'New Chat',
              isExisting: false
            });
          }
        } else if (activeSession && !activeSession.isExisting) {
          // Fallback if context has new chat but no loc state
        } else {
          // No bot selected, invalid new chat state -> Redirect home
          if (!activeSession && !botIdProp) {
            navigate(homePath);
          }
        }
      }
    };

    initializeSession();
  }, [sessionId, location.state, homePath, botIdProp]);

  // Transform raw messages to UI format
  const transformMessages = (messageList, sessionName) => {
    return messageList.map(msg => ({
      role: msg.role,
      text: msg.content,
      senderName: msg.role === 'user' ? (user?.full_name || 'You') : (sessionName || 'Bot'),
      timestamp: msg.created_at
    }));
  };



  const loadSessionAndMessages = async (id) => {
    setLoadingMessages(true);
    try {
      // 1. Fetch Session Details if needed
      let currentSession = activeSession;
      if (!currentSession || activeSession.id !== id) {
        const sessionData = await getSession(id);
        if (sessionData) {
          const newSessionState = {
            id: sessionData.id,
            botId: sessionData.bot_id,
            botName: sessionData.bots?.name || 'Bot',
            title: sessionData.summary_text || sessionData.title || 'Chat',
            isExisting: true
          };
          setActiveSession(newSessionState);
          currentSession = newSessionState;
        }
      }

      // 2. Fetch Messages (sort_desc=true to get latest)
      const response = await getSessionMessages(id, { limit: 20, sort_desc: true });
      const messageList = response.items || [];
      const cursor = response.next_cursor || null;

      // Reverse to show Chronological
      const uiMessages = transformMessages(messageList, currentSession?.botName).reverse();

      setChatHistory(uiMessages);
      setNextCursor(cursor);
      setHasMore(!!cursor);

    } catch (error) {
      console.error("Failed to load session/messages", error);
      // If session not found (404), maybe we should notify user or redirect?
      // For now, let's at least clear the loading state and show an error in history
      setChatHistory([{
        role: 'bot',
        text: "Error: Could not load the conversation. It might have been deleted.",
        timestamp: new Date()
      }]);
    } finally {
      setLoadingMessages(false);
      setTimeout(scrollToBottom, 50);
    }
  };

  // Infinite Scroll Load More
  const loadMoreMessages = async () => {
    if (isFetchingMore || !hasMore || !nextCursor || !sessionId) return;

    setIsFetchingMore(true);
    // Capture current scroll height to maintain position
    const container = scrollContainerRef.current;
    const oldScrollHeight = container ? container.scrollHeight : 0;
    const oldScrollTop = container ? container.scrollTop : 0;

    try {
      // Fetch next batch using cursor
      const response = await getSessionMessages(sessionId, {
        limit: 50,
        sort_desc: true,
        cursor_timestamp: nextCursor
      });

      const newMessagesRaw = response.items || [];
      const newCursor = response.next_cursor || null;

      if (newMessagesRaw.length > 0) {
        // Transform and Reverse (Oldest -> Newest of this batch)
        const newUiMessages = transformMessages(newMessagesRaw, activeSession?.botName).reverse();

        // Prepend to history: [OldestBatch...CurrentHistory]
        setChatHistory(prev => [...newUiMessages, ...prev]);
        setNextCursor(newCursor);
        setHasMore(!!newCursor);

        // Adjust scroll position after render
        // We need to wait for DOM update. state flush isn't instant, but useLayoutEffect/useEffect helps.
        // Here we rely on a small timeout or requestAnimationFrame, 
        // ideally we use useLayoutEffect with a flag, but quick fix:
        requestAnimationFrame(() => {
          if (container) {
            const newScrollHeight = container.scrollHeight;
            const heightDiff = newScrollHeight - oldScrollHeight;
            // Restore visual position
            container.scrollTop = heightDiff + oldScrollTop;
          }
        });
      } else {
        setHasMore(false);
      }
    } catch (err) {
      console.error("Failed to load more messages", err);
    } finally {
      setIsFetchingMore(false);
    }
  };

  // Sticky Scroll & Infinite Scroll Trigger
  const scrollToBottom = () => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'auto' });
    }
  };

  const handleScroll = () => {
    if (scrollContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight, children } = scrollContainerRef.current;

      // Auto-scroll logic (bottom)
      const isBottom = scrollHeight - scrollTop - clientHeight < 100;
      shouldAutoScrollRef.current = isBottom;

      // Infinite Scroll logic (top)
      // Trigger if we are near top and have more messages
      if (!isFetchingMore && hasMore && scrollTop < 500) {
        // User requested "4 messages away from top".
        // Use a pixel buffer or check element. 
        // 500px is roughly 4-5 generous messages depending on length.
        // Let's also try to be more specific if possible, but 200-300px is standard.
        // If the user wants specifically "4 messages", we can check height of top 4 children?
        // Let's stick to a robust pixel threshold for smoothness. 
        // Wait, if scrollTop is 0, we definitely load.
        loadMoreMessages();
      }
    }
  };

  useEffect(() => {
    if (shouldAutoScrollRef.current && !isFetchingMore) {
      scrollToBottom();
    }
  }, [chatHistory, isTyping, isFetchingMore]);


  const handleSendMessage = async () => {
    // Safety check: specific botId is required for the API
    const botId = activeSession?.botId || botIdProp;
    if (!inputValue.trim() || !botId) return;

    const message = inputValue;
    addMessage('user', message, false, user?.full_name || 'You');
    // Force scroll when user sends
    shouldAutoScrollRef.current = true;
    setTimeout(scrollToBottom, 50);

    setInputValue('');
    setIsTyping(true);

    // If we have a URL param sessionId, use it. Otherwise undefined.
    const currentSessionId = sessionId;

    try {

      await streamChatResponse({
        botId: botId, // Needs to be known for new chats
        sessionId: currentSessionId,
        message: message,
        quizMode: isQuizMode,
        onSessionId: (newId) => {
          // If we were in "new chat" mode (no URL param), we now have an ID.
          // Update URL to active chat path without reloading
          if (!sessionId && newId) {
            // Update context
            setActiveSession(prev => ({ ...prev, id: newId, isExisting: true }));

            // Build navigation URL based on route pattern
            // User: /user/chat/:sessionId
            // Admin: /admin/chat/:botId?sessionId=:sessionId
            let navUrl = `${basePath}/${newId}`;
            if (activeSession?.botId || botIdProp) {
              const bId = activeSession?.botId || botIdProp;
              // Detect if basePath is /admin/chat or similar that needs query params
              if (basePath.includes('/admin/')) {
                navUrl = `${basePath}/${bId}?sessionId=${newId}`;
              }
            }

            navigate(navUrl, { replace: true });
            fetchSessions();
          }
        },
        onChunk: (accumulated) => {
          setIsTyping(false); // Hide typing indicator as soon as we start receiving data
          updateLastBotMessage(accumulated);
        }
      });
    } catch (err) {
      console.error("Sending failed, attempting recovery...", err);
      // Self-healing: If the error was network/extension related but backend saved it,
      // fetching the latest messages will restore the missing response.
      const targetSessionId = currentSessionId || activeSession?.id;
      if (targetSessionId) {
        try {
          // Silent refresh
          await loadSessionAndMessages(targetSessionId);
          return; // If successful, skip the error message
        } catch (recoverErr) {
          console.error("Recovery failed", recoverErr);
        }
      }
      addMessage('bot', "Sorry, I encountered an error.", false, activeSession?.botName);
    } finally {
      setIsTyping(false);
    }
  };

  const updateLastBotMessage = (text) => {
    setChatHistory(prev => {
      const lastIndex = prev.length - 1;
      if (lastIndex >= 0 && prev[lastIndex].role === 'bot') {
        const newHistory = [...prev];
        newHistory[lastIndex] = { ...prev[lastIndex], text };
        return newHistory;
      } else {
        // Did not find the last message to be from bot (rare if we just started streaming), 
        // OR we are adding the very first chunk.
        // Ensure we include senderName from activeSession
        return [...prev, {
          role: 'bot',
          text,
          timestamp: new Date(),
          senderName: activeSession?.botName || 'Bot'
        }];
      }
    });
  };

  const addMessage = (role, text, isIntro = false, senderName = null) => {
    setChatHistory(prev => [...prev, { role, text, timestamp: new Date(), isIntro, senderName }]);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50/50 dark:bg-gray-900/50 backdrop-blur-sm relative">
      {/* Chat History Area */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 md:p-10 space-y-6 custom-scrollbar"
      >
        {loadingMessages ? (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-400 min-h-[50%]">
            <SpinnerIcon className="animate-spin text-3xl text-indigo-500 mb-2" />
            <p className="text-sm font-medium">Loading conversation...</p>
          </div>
        ) : (
          <>
            {/* Loading More Indicator */}
            {isFetchingMore && (
              <div className="w-full flex justify-center py-4">
                <SpinnerIcon className="animate-spin text-indigo-500" size={24} />
              </div>
            )}

            {chatHistory.map((msg, idx) => (
              <MessageBubble
                key={idx}
                role={msg.role}
                text={msg.text}
                senderName={msg.senderName}
                botId={activeSession?.botId}
                sessionId={activeSession?.id || sessionId}
              />
            ))}
          </>
        )}

        {isTyping && (
          <div className="flex w-full justify-start fade-in">
            <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center text-indigo-600 dark:text-indigo-400 mr-3 mt-1 shrink-0">
              <RobotIcon weight="fill" />
            </div>
            <div className="bg-white dark:bg-gray-800 border border-slate-200 dark:border-gray-700 px-4 py-3 rounded-2xl rounded-tl-sm flex items-center gap-1 shadow-sm">
              <div className="w-2 h-2 bg-slate-400 dark:bg-slate-600 rounded-full typing-dot"></div>
              <div className="w-2 h-2 bg-slate-400 dark:bg-slate-600 rounded-full typing-dot"></div>
              <div className="w-2 h-2 bg-slate-400 dark:bg-slate-600 rounded-full typing-dot"></div>
            </div>
          </div>
        )}
        <div ref={chatBottomRef} />
      </div>

      {/* Bottom Input Area */}
      <div className="p-4 md:p-6 bg-white/80 dark:bg-gray-900/80 border-t border-slate-100 dark:border-gray-700 backdrop-blur pb-8">
        <div className="max-w-3xl mx-auto relative group">
          <div className="absolute inset-0 bg-indigo-200 dark:bg-indigo-900/30 rounded-2xl blur opacity-20 transition"></div>
          <div className="relative bg-white dark:bg-gray-800 border border-slate-200 dark:border-gray-700 rounded-2xl flex items-end p-2 shadow-sm focus-within:ring-2 ring-indigo-100 dark:ring-indigo-900/30 transition">
            <button className="p-3 text-slate-400 dark:text-slate-500 hover:text-indigo-600 dark:hover:text-indigo-400 transition self-end pb-3">
              <PaperclipIcon className="text-xl" />
            </button>

            {/* Quiz Mode Toggle */}
            <div className="absolute -top-10 right-0 flex items-center gap-2">
              <button
                onClick={() => setShowQuizHistory(true)}
                className="bg-white/90 dark:bg-gray-800/90 py-1.5 px-3 rounded-full border border-slate-200 dark:border-gray-700 shadow-sm backdrop-blur-sm text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition"
                title="View History"
              >
                History
              </button>
              <div className="flex items-center gap-2 bg-white/90 dark:bg-gray-800/90 py-1.5 px-3 rounded-full border border-slate-200 dark:border-gray-700 shadow-sm backdrop-blur-sm">
                <span className="text-xs font-medium text-slate-600 dark:text-slate-300">Quiz Mode</span>
                <button
                  onClick={() => setIsQuizMode(!isQuizMode)}
                  className={`w-8 h-4 rounded-full relative transition-colors ${isQuizMode ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-gray-600'}`}
                  title="Toggle Quiz Mode"
                >
                  <div className={`absolute top-0.5 left-0.5 w-3 h-3 bg-white rounded-full transition-transform shadow-sm ${isQuizMode ? 'translate-x-4' : ''}`} />
                </button>
              </div>
            </div>

            <textarea
              rows="1"
              className="flex-1 bg-transparent border-none outline-none text-base py-3 px-2 resize-none max-h-32 dark:text-slate-200 dark:placeholder:text-slate-600 disabled:opacity-50 disabled:cursor-not-allowed"
              placeholder={t('chatbot.placeholder')}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyPress}
              style={{ minHeight: '48px' }}
              disabled={(!activeSession?.botId && !botIdProp)}
            ></textarea>
            <button
              onClick={handleSendMessage}
              disabled={(!activeSession?.botId && !botIdProp) || !inputValue.trim()}
              className="p-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition self-end shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <PaperPlaneRightIcon weight="bold" className="text-lg" />
            </button>
          </div>
          <p className="text-center text-[10px] text-slate-400 mt-2">{t('chatbot.disclaimer')}</p>
        </div>
      </div>
      <QuizHistoryModal isOpen={showQuizHistory} onClose={() => setShowQuizHistory(false)} />
    </div>
  );
};

export default ChatInterface;
