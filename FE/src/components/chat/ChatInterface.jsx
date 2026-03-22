import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
  PaperPlaneRightIcon,
  RobotIcon,
  PaperclipIcon,
  SpinnerIcon,
  StopIcon,
  ClockCounterClockwiseIcon
} from '@phosphor-icons/react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import { useChat } from '../../context/ChatContext';
import MessageBubble from './MessageBubble';
import { streamChatResponse, getSessionMessages, getSession, rateMessage } from '../../services/chatService';
import QuizHistoryModal from './QuizHistoryModal';
import { botService } from '../../services/botService';
import AgentStatusIndicator from './AgentStatusIndicator';

const ChatInterface = ({ basePath = '/user/chat', homePath = '/user/home', sessionIdProp = null, botIdProp = null }) => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { activeSession, setActiveSession, fetchSessions } = useChat();
  const { sessionId: paramSessionId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const sessionIdPropFromQuery = new URLSearchParams(location.search).get('sessionId');
  const sessionId = sessionIdProp || paramSessionId || sessionIdPropFromQuery;

  const [inputValue, setInputValue] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeStatus, setActiveStatus] = useState('');

  const [isQuizMode, setIsQuizMode] = useState(false);
  const [showQuizHistory, setShowQuizHistory] = useState(false);

  const chatBottomRef = useRef(null);
  const scrollContainerRef = useRef(null);
  const shouldAutoScrollRef = useRef(true);
  const abortControllerRef = useRef(null);
  const isInitialStreamingRef = useRef(false); // Track if we are currently streaming the first message

  // State for Infinite Scroll
  const [nextCursor, setNextCursor] = useState(null);
  const [isFetchingMore, setIsFetchingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);

  // Initial setup: Handle routing and state initialization
  useEffect(() => {
    const controller = new AbortController();

    const initializeSession = async () => {
      // If we have a sessionId (prop or param), we load that session
      if (sessionId) {
        // Guard: If we just started this session via streaming, don't reload history
        // as the backend might not have finished saving the response yet.
        if (isInitialStreamingRef.current) {
          console.log("[ChatInterface] Skipping session load during initial stream to prevent race condition (sessionId:", sessionId, ")");
          return;
        }

        console.log("[ChatInterface] initializeSession: Loading session", sessionId);
        if (activeSession?.id !== sessionId) {
          // Context update handled inside loadSessionAndMessages or redundant
        }
        await loadSessionAndMessages(sessionId, controller.signal);
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
              if (controller.signal.aborted) return;
              const botDetails = await botService.getBot(targetBotId);
              if (controller.signal.aborted) return;
              targetBotName = botDetails.name;
            } catch (err) {
              console.error("Failed to fetch bot details for new chat", err);
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

    return () => controller.abort();
  }, [sessionId, location.state, homePath, botIdProp]);

  // Transform raw messages to UI format
  const transformMessages = (messageList, sessionName) => {
    return messageList.map(msg => ({
      id: msg.id,
      role: msg.role,
      text: msg.content,
      senderName: msg.role === 'user' ? (user?.full_name || 'You') : (sessionName || 'Bot'),
      timestamp: msg.created_at,
      rating: msg.rating
    }));
  };

  const loadSessionAndMessages = async (id, signal, isRecovery = false) => {
    console.log(`[ChatInterface] loadSessionAndMessages calling for id: ${id} (Recovery: ${isRecovery})`);
    setLoadingMessages(!isRecovery); // Don't show full page spinner during silent recovery
    try {
      // 1. Fetch Session Details if needed
      let currentSession = activeSession;
      if (!currentSession || activeSession.id !== id) {
        const sessionData = await getSession(id, { 
          signal,
          timeout: isRecovery ? 5000 : 30000 // Faster timeout for recovery
        });
        if (sessionData) {
          const newSessionState = {
            id: sessionData.id,
            botId: sessionData.bot_id,
            botName: sessionData.bots?.name || activeSession?.botName || 'Bot',
            title: sessionData.summary_text || sessionData.title || 'Chat',
            isExisting: true
          };
          // Abort check before state update
          if (signal?.aborted) return;
          setActiveSession(newSessionState);
          currentSession = newSessionState;
        }
      }

      // 2. Fetch Messages (sort_desc=true to get latest)
      const response = await getSessionMessages(id, 
        { limit: 20, sort_desc: true }, 
        { 
          signal,
          timeout: isRecovery ? 5000 : 30000 
        }
      );
      if (signal?.aborted) return;

      const messageList = response.items || [];
      const cursor = response.next_cursor || null;

      // Reverse to show Chronological
      const uiMessages = transformMessages(messageList, currentSession?.botName).reverse();

      setChatHistory(uiMessages);
      setNextCursor(cursor);
      setHasMore(!!cursor);

    } catch (error) {
      if (error.code === 'ERR_CANCELED' || error.name === 'AbortError') {
        console.log('Session loading aborted');
        return;
      }
      console.error("Failed to load session/messages", error);
      // If session not found (404), maybe we should notify user or redirect?
      // For now, let's at least clear the loading state and show an error in history
      setChatHistory([{
        role: 'bot',
        text: "Error: Could not load the conversation. It might have been deleted.",
        timestamp: new Date()
      }]);
    } finally {
      if (!signal?.aborted) {
        setLoadingMessages(false);
        setTimeout(scrollToBottom, 50);
      }
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
        loadMoreMessages();
      }
    }
  };

  useEffect(() => {
    if (shouldAutoScrollRef.current && !isFetchingMore) {
      scrollToBottom();
    }
  }, [chatHistory, isTyping, isFetchingMore]);

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsTyping(false);
    setIsStreaming(false);
  };

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
    setIsStreaming(false);

    // If we have a URL param sessionId, use it. Otherwise undefined.
    const currentSessionId = sessionId;
    const isNewChat = !currentSessionId;

    if (isNewChat) {
      console.log("[ChatInterface] Starting new chat, setting isInitialStreamingRef = true");
      isInitialStreamingRef.current = true;
    }

    // Create new AbortController
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {

      await streamChatResponse({
        botId: botId, // Needs to be known for new chats
        sessionId: currentSessionId,
        message: message,
        quizMode: isQuizMode,
        signal: controller.signal,
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
          setIsTyping(true);
          setIsStreaming(true); // Text has started arriving
          setActiveStatus(''); // Clear tool status when real text arrives
          updateLastBotMessage(accumulated);
        },
        onStatus: (status) => {
          setActiveStatus(status);
        },
        onToolCall: (toolCall) => {
          // Append tool call to the last bot message
          setChatHistory(prev => {
            const lastIndex = prev.length - 1;
            if (lastIndex >= 0 && prev[lastIndex].role === 'bot') {
              const newHistory = [...prev];
              newHistory[lastIndex] = {
                ...prev[lastIndex],
                toolCalls: [...(prev[lastIndex].toolCalls || []), toolCall]
              };
              return newHistory;
            }
            return prev;
          });
        }
      });
    } catch (err) {
      if (err.name === 'AbortError') {
        console.log("Response generation stopped by user or timeout");
      } else {
        const isConnectionError = 
          err.message?.toLowerCase().includes('failed to fetch') || 
          err.message?.toLowerCase().includes('network error') ||
          err.message?.toLowerCase().includes('connection timeout') ||
          err instanceof TypeError;

        console.error("Sending failed", { isConnectionError, err });

        // If it's a clear connection error, don't waste time trying to refresh messages
        if (!isConnectionError) {
          const targetSessionId = currentSessionId || activeSession?.id;
          if (targetSessionId) {
            try {
              // Silent refresh with shorter timeout
              await loadSessionAndMessages(targetSessionId, null, true);
              return; 
            } catch (recoverErr) {
              console.error("Recovery failed", recoverErr);
            }
          }
        }
        
        const errorMsg = isConnectionError 
          ? "Connection to server lost. Please check if the API is running." 
          : "Sorry, I encountered an error. Please try again.";
          
        addMessage('bot', errorMsg, false, activeSession?.botName);
      }
    } finally {
      setIsTyping(false);
      setIsStreaming(false);
      setActiveStatus('');
      isInitialStreamingRef.current = false;
      abortControllerRef.current = null;
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

  const handleRateMessage = async (messageId, rating) => {
    if (!messageId) return;

    // Update locally first for instant feedback
    setChatHistory(prev => prev.map(msg =>
      msg.id === messageId ? { ...msg, rating } : msg
    ));

    try {
      await rateMessage(messageId, rating);
    } catch (err) {
      console.error("Failed to rate message", err);
      // Optional: rollback on failure
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isTyping && !loadingMessages) {
        handleSendMessage();
      }
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900 relative">
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] bg-opacity-20 pointer-events-none opacity-5"></div>

      {/* Chat History Area */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto custom-scrollbar scroll-smooth flex flex-col"
      >
        {loadingMessages ? (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-400 min-h-[50%]">
            <SpinnerIcon className="animate-spin text-3xl text-indigo-500 mb-2" />
            <p className="text-sm font-medium">Loading conversation...</p>
          </div>
        ) : (
          <div className="mt-auto w-full max-w-4xl mx-auto px-4 md:px-8 pt-6 pb-4 space-y-6">
            {/* Loading More Indicator */}
            {isFetchingMore && (
              <div className="w-full flex justify-center py-4">
                <SpinnerIcon className="animate-spin text-indigo-500" size={24} />
              </div>
            )}

            {chatHistory.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center text-gray-400 opacity-60 min-h-[40vh]">
                <div className="w-16 h-16 rounded-2xl bg-gray-50 dark:bg-gray-800 flex items-center justify-center mb-4 border border-gray-100 dark:border-gray-700">
                  <RobotIcon size={32} weight="duotone" />
                </div>
                <p className="text-lg font-medium text-gray-500">How can I help you today?</p>
              </div>
            ) : (
              chatHistory.map((msg, idx) => (
                <MessageBubble
                  key={idx}
                  id={msg.id}
                  role={msg.role}
                  text={msg.text}
                  rating={msg.rating}
                  senderName={msg.senderName}
                  botId={activeSession?.botId}
                  sessionId={activeSession?.id || sessionId}
                  onRate={handleRateMessage}
                  toolCalls={msg.toolCalls}
                />
              ))
            )}
          </div>
        )}

        {isTyping && !isStreaming && (
          <div className="w-full max-w-4xl mx-auto px-4 md:px-8 pb-6">
            <div className="flex w-full justify-start fade-in">
              <div className="w-8 h-8 rounded-lg bg-indigo-100 dark:bg-indigo-500/10 flex items-center justify-center text-indigo-600 dark:text-indigo-400 mr-3 mt-0.5 shrink-0 border border-indigo-200 dark:border-indigo-500/20 shadow-sm">
                <RobotIcon size={20} weight="duotone" />
              </div>
              {activeStatus ? (
                <AgentStatusIndicator status={activeStatus} />
              ) : (
                <div className="bg-gray-100 dark:bg-gray-800 px-4 py-3 rounded-2xl rounded-tl-sm flex items-center gap-1.5 min-h-[40px]">
                  <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-75"></div>
                  <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-150"></div>
                </div>
              )}
            </div>
          </div>
        )}
        <div ref={chatBottomRef} />
      </div>

      {/* Bottom Input Area */}
      <div className="px-4 pt-3 pb-2 bg-white dark:bg-gray-900 border-t border-gray-100 dark:border-gray-800 relative z-20">
        <div className="max-w-4xl mx-auto relative group">

          <div className="relative border border-gray-300 dark:border-gray-700 rounded-xl shadow-sm bg-white dark:bg-gray-800 focus-within:ring-2 focus-within:ring-indigo-500/20 focus-within:border-indigo-500 transition-all overflow-hidden flex flex-col">
            <textarea
              rows="1"
              spellCheck="false"
              className="w-full resize-none border-none focus:ring-0 p-4 text-base text-gray-900 dark:text-gray-100 placeholder-gray-400 font-sans max-h-48 bg-transparent"
              placeholder={t('chatbot.placeholder', 'Send a message...')}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyPress}
              disabled={(!activeSession?.botId && !botIdProp) || loadingMessages || isTyping}
            ></textarea>

            <div className="px-3 py-2 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-100 dark:border-gray-700 flex justify-between items-center">
              <div className="flex items-center gap-1">
                <button className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors" title="Attach">
                  <PaperclipIcon size={18} />
                </button>
                <div className="h-4 w-px bg-gray-300 dark:bg-gray-700 mx-1"></div>
                <button
                  onClick={() => setIsQuizMode(!isQuizMode)}
                  className={`p-2 rounded-lg transition-colors text-xs font-medium flex items-center gap-1 ${isQuizMode ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400' : 'text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'}`}
                  title="Toggle Quiz Mode"
                >
                  <span className={`w-2 h-2 rounded-full ${isQuizMode ? 'bg-indigo-500' : 'bg-gray-400'}`}></span>
                  Quiz
                </button>
                <button
                  onClick={() => setShowQuizHistory(true)}
                  className="p-2 rounded-lg transition-colors text-xs font-medium flex items-center gap-1 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 ml-1"
                  title={t('chat.quiz_history', 'View Quiz History')}
                >
                  <ClockCounterClockwiseIcon size={16} />
                  <span>{t('chatbot.quiz_history_btn', 'Quiz History')}</span>
                </button>
              </div>

              {isTyping ? (
                <button
                  onClick={handleStop}
                  className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition shadow-sm flex items-center gap-2 text-sm font-medium"
                >
                  <StopIcon weight="bold" />
                  Stop
                </button>
              ) : (
                <button
                  onClick={handleSendMessage}
                  disabled={(!activeSession?.botId && !botIdProp) || !inputValue.trim() || loadingMessages}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition shadow-sm flex items-center gap-2 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Send
                  <PaperPlaneRightIcon weight="bold" />
                </button>
              )}
            </div>

            <p className="text-center text-[10px] text-gray-400 mt-2">{t('chatbot.disclaimer')}</p>
          </div>
        </div>
        <QuizHistoryModal isOpen={showQuizHistory} onClose={() => setShowQuizHistory(false)} />
      </div>
    </div>
  );
};

export default ChatInterface;
