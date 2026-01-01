import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { streamChatResponse } from '../../services/chatService';
import remarkGfm from 'remark-gfm';
import MarkdownRenderer from '../../components/common/MarkdownRenderer';

import {
  PaperPlaneRightIcon,
  TrashIcon,
  ArrowLeftIcon,
  RobotIcon,
  SpinnerIcon,
  UserIcon,
  CpuIcon
} from '@phosphor-icons/react';
import { clsx } from 'clsx';
import { useAuth } from '../../context/AuthContext';
import { useTranslation } from 'react-i18next';



// MarkdownContent has been moved to components/common/MarkdownRenderer.jsx

const Chatbot = () => {
  const { id: botId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const { t } = useTranslation(['chatbot', 'translation']);

  // State
  const [bot, setBot] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [initialLoad, setInitialLoad] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [sending, setSending] = useState(false);
  const [hasMoreHistory, setHasMoreHistory] = useState(true);
  const [offset, setOffset] = useState(0);
  const [streamError, setStreamError] = useState(null);

  // Refs
  const chatContainerRef = useRef(null);
  const endOfMessagesRef = useRef(null);
  const inputRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Fetch bot details
  useEffect(() => {
    if (botId && token) {
      api.get(`/bots/${botId}`)
        .then(res => setBot(res.data))
        .catch(err => console.error("Failed to fetch bot", err));
    }
  }, [botId, token]);

  // Fetch session
  useEffect(() => {
    if (botId && token) {
      setInitialLoad(true);
      api.get(`/sessions?limit=1&offset=0&bot_id=${botId}`)
        .then(res => {
          if (res.data && res.data.length > 0) {
            setSessionId(res.data[0].id);
          } else {
            setInitialLoad(false);
            setHasMoreHistory(false);
          }
        })
        .catch(err => {
          console.error("Failed to fetch session", err);
          setInitialLoad(false);
        });
    }
  }, [botId, token]);

  // Fetch initial messages when sessionId is found
  useEffect(() => {
    if (sessionId && token) {
      if (messages.length === 0) {
        loadHistory(sessionId, 0).finally(() => setInitialLoad(false));
      } else {
        setInitialLoad(false);
      }
    }
  }, [sessionId, token]);

  // Reset local transient state when botId changes
  useEffect(() => {
    setMessages([]);
    setSessionId(null);
    setInitialLoad(true);
    setOffset(0);
    setHasMoreHistory(true);
  }, [botId]);


  // --- 4. Load History Helper (Pagination - KEEPING MANUAL) ---
  const loadHistory = async (sessId, currentOffset = 0) => {
    if (!sessId) return;
    setLoadingHistory(true);

    try {
      const res = await api.get(`/sessions/${sessId}/messages?limit=20&offset=${currentOffset}`);

      const newMessages = res.data.items || [];

      if (newMessages.length < 20) {
        setHasMoreHistory(false);
      }

      setMessages(prev => {
        const existingIds = new Set(prev.map(m => m.id));
        const uniqueMessages = newMessages.filter(m => !existingIds.has(m.id));
        // Append to end (which is 'top' visually in reverse)
        return [...prev, ...uniqueMessages];
      });

      setOffset(prev => prev + newMessages.length);

    } catch (err) {
      console.error("History load failed", err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const scrollToBottom = (behavior = 'smooth') => {
    endOfMessagesRef.current?.scrollIntoView({ behavior });
  };

  // --- 4. Infinite Scroll Handler ---
  const handleScroll = (e) => {
    const { scrollTop } = e.currentTarget;
    if (scrollTop > -50 &&
      scrollTop < 50 &&
      hasMoreHistory &&
      !loadingHistory &&
      !initialLoad &&
      sessionId
    ) {
      loadHistory(sessionId, offset);
    }
  };

  // --- 5. Message Sending (Streaming) ---
  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || sending) return;

    const userMsg = input.trim();
    setInput('');
    setStreamError(null);

    // 1. Optimistic UI: Add user message (At start of array)
    const tempUserMsg = { role: 'user', content: userMsg, id: Date.now().toString() };
    setMessages(prev => [tempUserMsg, ...prev]);
    setSending(true);

    // 2. Add placeholder Bot message (At start of array)
    const tempBotMsgId = (Date.now() + 1).toString();
    setMessages(prev => [{ role: 'model', content: '', id: tempBotMsgId, isStreaming: true }, ...prev]);

    setTimeout(scrollToBottom, 0);

    try {
      if (abortControllerRef.current) abortControllerRef.current.abort();
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      await streamChatResponse({
        botId,
        sessionId,
        message: userMsg,
        signal: abortController.signal,
        onSessionId: (newSessionId) => {
          if (!sessionId) setSessionId(newSessionId);
        },
        onChunk: (accumulated) => {
          setMessages(prev => prev.map(msg =>
            msg.id === tempBotMsgId
              ? { ...msg, content: accumulated }
              : msg
          ));
        }
      });

      // Finalize message (remove streaming flag)
      setMessages(prev => prev.map(msg =>
        msg.id === tempBotMsgId ? { ...msg, isStreaming: false } : msg
      ));

    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error("Stream failed", err);
        setStreamError(t('connectionError', 'Server connection lost. Please try again.'));
        setMessages(prev => prev.map(msg =>
          msg.id === tempBotMsgId ? { ...msg, isError: true, content: t('shortError', 'Connection error.') } : msg
        ));
      }
    } finally {
      setSending(false);
      setTimeout(scrollToBottom, 100);
    }
  };

  // --- 6. Clear Chat ---
  const handleClearChat = () => {
    if (!window.confirm(t('clearConfirm', 'Start a new chat session?'))) return;
    setMessages([]);
    setSessionId(null);
    setInitialLoad(false); // No data needed to load for a fresh session
    setOffset(0);
    setHasMoreHistory(true);
  };


  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900 transition-colors">
      {/* HEADER */}
      <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6 shrink-0 z-10 shadow-sm">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="text-gray-500 hover:text-primary-600 dark:text-gray-400">
            <ArrowLeftIcon size={24} weight="bold" />
          </button>

          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900/50 flex items-center justify-center text-primary-600 dark:text-primary-400">
              {bot ? <RobotIcon size={24} weight="fill" /> : <div className="w-6 h-6 bg-gray-300 rounded-full animate-pulse" />}
            </div>
            <div>
              {bot ? (
                <>
                  <h1 className="font-bold text-gray-800 dark:text-white text-lg leading-tight">{bot.name}</h1>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    <p className="text-xs text-gray-500 dark:text-gray-400 font-mono">{bot.model?.name || 'AI Assistant'}</p>
                  </div>
                </>
              ) : (
                <div className="w-32 h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
              )}
            </div>
          </div>
        </div>

        <button
          onClick={handleClearChat}
          className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-full transition"
          title={t('clearTooltip', 'Clear chat')}
        >
          <TrashIcon size={24} />
        </button>
      </header>

      {/* CHAT AREA */}
      <main
        ref={chatContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-6 scroll-smooth bg-gray-50 dark:bg-gray-900 flex flex-col-reverse"
      >
        {/* Anchor at the visual bottom (Start of DOM) */}
        <div ref={endOfMessagesRef} />
        {initialLoad ? (
          <div className="w-full space-y-6 animate-pulse">
            {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
              <div key={i} className={`flex ${i % 2 === 0 ? 'justify-end' : 'justify-start'}`}>
                <div className={`h-16 rounded-2xl bg-gray-200 dark:bg-gray-700 ${i % 3 === 0 ? 'w-3/4' : i % 3 === 1 ? 'w-2/3' : 'w-1/2'
                  } ${i % 2 === 0 ? 'rounded-tr-none' : 'rounded-tl-none'}`}></div>
              </div>
            ))}
          </div>
        ) : messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-400 dark:text-gray-600 opacity-50">
            <RobotIcon size={64} weight="thin" className="mb-4" />
            <p>{t('welcome', 'Start a conversation with')} {bot?.name}</p>
          </div>
        ) : (
          <>
            {/* Messages are reversed in state [Newest ... Oldest] */}
            {/* But flex-col-reverse renders: [Last DOM Elem ... First DOM Elem] (Visual Top to Bottom)? */}
            {/* NO. flex-col-reverse renders: [Last DOM Elem] at TOP, [First DOM Elem] at BOTTOM. */}
            {/* So if we map messages: Msg 0 (Newest), Msg 1 ... */}
            {/* Msg 0 will be at BOTTOM. Msg N will be at TOP. */}
            {/* This is exactly what we want. */}

            {messages.map((msg, idx) => {
              const isUser = msg.role === 'user';
              const isError = msg.isError;

              return (
                <div key={msg.id || idx} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                  {/* Avatar for Bot */}
                  {!isUser && (
                    <div className="w-8 h-8 mr-3 rounded-full bg-white dark:bg-gray-800 border dark:border-gray-700 flex items-center justify-center text-primary-600 shrink-0 shadow-sm mt-1">
                      <CpuIcon size={16} weight="fill" />
                    </div>
                  )}

                  <div className={clsx(
                    "max-w-[92%] md:max-w-[85%] p-4 rounded-2xl shadow-sm text-sm md:text-base leading-relaxed break-words",
                    isUser
                      ? "bg-primary-600 text-white rounded-tr-sm"
                      : "bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 text-gray-800 dark:text-gray-100 rounded-tl-sm",
                    isError && "border-red-500 bg-red-50 dark:bg-red-900/20 text-red-600"
                  )}>
                    {isUser ? (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      msg.content ? <MarkdownRenderer content={msg.content} /> : <div className="flex gap-1 items-center h-6"><span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span><span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-75"></span><span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-150"></span></div>
                    )}
                  </div>

                  {/* Avatar for User */}
                  {isUser && (
                    <div className="w-8 h-8 ml-3 rounded-full bg-primary-100 dark:bg-primary-900/50 flex items-center justify-center text-primary-700 shrink-0 shadow-sm mt-1">
                      <UserIcon size={16} weight="fill" />
                    </div>
                  )}
                </div>
              );
            })}
            {loadingHistory && (
              <div className="w-full text-center py-2 text-xs text-gray-400 flex items-center justify-center gap-2 mt-4">
                <SpinnerIcon className="animate-spin" /> {t('loadingHistory', 'Loading older messages...')}
              </div>
            )}
          </>
        )}
      </main>

      {/* INPUT AREA */}
      <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4 shrink-0 transition-colors">
        <div className="max-w-6xl mx-auto px-4">
          <form onSubmit={handleSend} className="flex items-end gap-3 relative">
            <div className="flex-1 bg-gray-100 dark:bg-gray-700/50 rounded-2xl p-1 transition focus-within:ring-2 focus-within:ring-primary-100 dark:focus-within:ring-primary-900/30 border border-transparent focus-within:border-primary-200 dark:focus-within:border-primary-700">
              <textarea
                ref={inputRef}
                rows={1}
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  e.target.style.height = 'auto';
                  e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend(e);
                  }
                }}
                placeholder={t('placeholder', 'Type a message...')}
                className="w-full bg-transparent border-none text-gray-800 dark:text-white placeholder-gray-400 focus:ring-0 resize-none max-h-32 py-3 px-4 outline-none"
              />
            </div>
            <button
              type="submit"
              disabled={!input.trim() || sending}
              className="bg-primary-600 hover:bg-primary-700 text-white p-3.5 rounded-xl shadow-lg hover:shadow-primary-500/30 transition disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none mb-1 group"
            >
              {sending ? <SpinnerIcon size={20} className="animate-spin" /> : <PaperPlaneRightIcon size={20} weight="fill" className="group-hover:-translate-y-0.5 group-hover:translate-x-0.5 transition-transform" />}
            </button>
          </form>
          <p className="text-center text-[10px] sm:text-xs text-gray-400 dark:text-gray-500 mt-2 font-medium">
            {t('disclaimer', 'AI may make mistakes. Verify important information.')}
          </p>
        </div>
      </div>
    </div >
  );
};

export default Chatbot;
