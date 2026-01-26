import React, { useState } from 'react';
import { useNavigate, NavLink, useLocation } from 'react-router-dom';
import { ROUTES } from '../../../routes';
import {
  HouseIcon,
  FolderIcon,
  ClockCounterClockwiseIcon,
  GearIcon,
  XIcon,
  SignOutIcon,
  ChatsCircleIcon,
  TrashIcon,
  CaretDownIcon,
  StudentIcon
} from '@phosphor-icons/react';
import Skeleton from '../../common/Skeleton'; // Added import
import { useAuth } from '../../../context/AuthContext';
import { useChat } from '../../../context/ChatContext';
import { useTranslation } from 'react-i18next';
import clsx from 'clsx';

const UserSidebar = ({ isOpen, toggleSidebar }) => {
  const { t } = useTranslation();
  const { logout } = useAuth();
  const {
    sessions,
    activeSession,
    setActiveSession,
    deleteSession: deleteSessionContext,
    loading: sessionsLoading
  } = useChat();

  const activeSessionId = activeSession?.id;

  const navigate = useNavigate();
  const location = useLocation();

  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  const handleDeleteSession = async (e, sessionId) => {
    e.stopPropagation();
    if (window.confirm(t('common.delete') + '?')) {
      await deleteSessionContext(sessionId);
      if (String(activeSessionId) === String(sessionId)) {
        navigate('/user/history');
      }
    }
  };

  const handleSelectSession = (session) => {
    setActiveSession(session);
    navigate(ROUTES.USER.CHAT(session.bot_id, session.id));
    if (window.innerWidth < 768) toggleSidebar();
  };

  const toggleHistory = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsHistoryOpen(!isHistoryOpen);
  };

  const handleLogout = () => {
    if (window.confirm("Are you sure you want to sign out?")) {
      logout();
    }
  };

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden backdrop-blur-sm transition-opacity"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={clsx(
          "fixed md:static inset-y-0 left-0 z-40 w-64 flex flex-col transition-transform duration-300 ease-in-out border-r shadow-2xl md:shadow-none",
          "bg-white/70 backdrop-blur-md dark:bg-slate-950/90 border-slate-200 dark:border-slate-800",
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
          "md:flex"
        )}
      >
        {/* Header */}
        <div className="h-16 flex items-center justify-between px-6 border-b shrink-0 bg-transparent border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <ChatsCircleIcon weight="fill" className="text-white text-lg" />
            </div>
            <span className="font-bold text-lg text-slate-900 dark:text-white tracking-wide">UniChat</span>
          </div>
          <button onClick={toggleSidebar} className="md:hidden text-slate-400 hover:text-slate-600 dark:hover:text-white transition">
            <XIcon size={20} />
          </button>
        </div >

        {/* Navigation */}
        < nav className="px-3 flex-1 overflow-y-auto space-y-1 py-4" >
          {/* Dashboard */}
          < NavLink
            to="/user/home"
            onClick={() => window.innerWidth < 768 && toggleSidebar()}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group text-sm font-medium",
                isActive
                  ? "bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-400 shadow-sm ring-1 ring-indigo-200 dark:ring-indigo-500/20"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white"
              )
            }
          >
            <HouseIcon className="text-lg transition-colors group-hover:text-indigo-600 dark:group-hover:text-indigo-400" weight="duotone" />
            <span>{t('nav.home')}</span>
          </NavLink >

          {/* Classes */}
          < NavLink
            to="/user/classes"
            onClick={() => window.innerWidth < 768 && toggleSidebar()}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group text-sm font-medium",
                isActive
                  ? "bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-400 shadow-sm ring-1 ring-indigo-200 dark:ring-indigo-500/20"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white"
              )
            }
          >
            <StudentIcon className="text-lg transition-colors group-hover:text-indigo-600 dark:group-hover:text-indigo-400" weight="duotone" />
            <span>{t('nav.classes', 'My Classes')}</span>
          </NavLink >

          {/* Custom History Item with Dropdown */}
          < div className="space-y-0.5" >
            <div className="flex items-center pr-2 group">
              <NavLink
                to="/user/history"
                onClick={() => window.innerWidth < 768 && toggleSidebar()}
                className={({ isActive }) =>
                  clsx(
                    "flex-1 flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 text-sm font-medium",
                    isActive
                      ? "bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-400"
                      : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white"
                  )
                }
              >
                <ClockCounterClockwiseIcon className="text-lg transition-colors group-hover:text-indigo-600 dark:group-hover:text-indigo-400" weight="duotone" />
                <span>{t('nav.history')}</span>
              </NavLink>

              <button
                onClick={toggleHistory}
                className={clsx(
                  "p-2 rounded-lg transition-colors ml-1",
                  isHistoryOpen
                    ? "text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-500/10"
                    : "text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
                )}
                title="Toggle Recent Sessions"
              >
                <CaretDownIcon
                  size={16}
                  weight="bold"
                  className={clsx("transition-transform duration-200", isHistoryOpen ? "rotate-0" : "-rotate-90")}
                />
              </button>
            </div>

            {/* Dropdown Content */}
            <div className={clsx(
              "overflow-hidden transition-all duration-300 ease-in-out pl-4",
              isHistoryOpen ? "max-h-96 opacity-100 mt-1" : "max-h-0 opacity-0"
            )}>
              <div className="pl-3 border-l border-slate-200 dark:border-slate-700/50 space-y-1 py-1">
                {sessionsLoading ? (
                  <Skeleton className="h-4 w-24 mx-4 my-2" />
                ) : sessions.length === 0 ? (
                  <div className="px-4 py-2 text-xs text-slate-500 italic">No recent sessions</div>
                ) : (
                  sessions.map(session => (
                    <div
                      key={session.id}
                      className={clsx(
                        "group/item flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all text-xs relative",
                        (String(activeSessionId) === String(session.id) && location.pathname.includes('/chat'))
                          ? "bg-slate-100 text-indigo-700 dark:bg-slate-800 dark:text-indigo-300 border border-slate-200 dark:border-slate-700"
                          : "text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50 hover:text-slate-700 dark:hover:text-slate-200"
                      )}
                      onClick={() => handleSelectSession(session)}
                    >
                      <div className="flex-1 truncate">
                        <span className="block truncate font-medium">
                          {session.summary_text || session.bots?.name || t('chatbot.new_chat')}
                        </span>
                      </div>

                      {/* Hover Actions */}
                      <div className={clsx("flex items-center gap-1 opacity-100 md:opacity-0 transition-opacity", String(activeSessionId) === String(session.id) ? "opacity-100 md:opacity-100" : "group-hover/item:opacity-100")}>
                        <button
                          onClick={(e) => handleDeleteSession(e, session.id)}
                          className="p-0.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-slate-400 hover:text-red-500 dark:hover:text-red-400"
                        >
                          <TrashIcon size={12} />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div >

          {/* Settings */}
          < NavLink
            to="/user/settings"
            onClick={() => window.innerWidth < 768 && toggleSidebar()}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group text-sm font-medium",
                isActive
                  ? "bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-400 shadow-sm ring-1 ring-indigo-200 dark:ring-indigo-500/20"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white"
              )
            }
          >
            <GearIcon className="text-lg transition-colors group-hover:text-indigo-600 dark:group-hover:text-indigo-400" weight="duotone" />
            <span>{t('nav.settings')}</span>
          </NavLink >

        </nav >

        {/* Footer */}
        < div className="p-4 border-t border-slate-200 dark:border-slate-700/50 bg-slate-50 dark:bg-slate-900/50" >
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-red-50 dark:hover:bg-red-500/10 text-slate-500 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-all group"
          >
            <SignOutIcon className="text-lg group-hover:text-red-600 dark:group-hover:text-red-400 transition-colors" weight="duotone" />
            <span className="font-medium text-sm">{t('nav.sign_out')}</span>
          </button>
        </div >
      </aside >
    </>
  );
};

export default UserSidebar;
