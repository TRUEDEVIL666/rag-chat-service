import React, { useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import Skeleton from '../../common/Skeleton';
import {
  MonitorPlayIcon,
  SquaresFourIcon,
  RobotIcon,
  FilesIcon,
  UsersIcon,
  GearIcon,
  SignOutIcon,
  BrainIcon,
  ClockCounterClockwiseIcon,
  XIcon,
  CaretDownIcon,
  TrashIcon,
  GraduationCapIcon
} from '@phosphor-icons/react';

import { useAuth } from '../../../context/AuthContext';
import { useChat } from '../../../context/ChatContext';
import { useTranslation } from 'react-i18next';
import clsx from 'clsx';

const Sidebar = ({ isOpen, toggleSidebar }) => {
  const { logout } = useAuth();
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const {
    sessions,
    sessionsLoading,
    deleteSession: deleteSessionContext
  } = useChat();

  const handleLogout = (e) => {
    e.preventDefault();
    if (confirm(t('common.logoutConfirm', 'Are you sure you want to log out?'))) {
      logout();
    }
  };

  const NavItem = ({ to, icon: Icon, label }) => (
    <NavLink end
      to={to}
      onClick={() => {
        if (window.innerWidth < 768 && toggleSidebar) {
          toggleSidebar();
        }
      }}
      className={({ isActive }) => clsx(
        "flex items-center gap-3 px-4 py-3 rounded-lg transition font-medium text-sm group",
        isActive
          ? "bg-blue-50 text-blue-600 dark:bg-primary-900/10 dark:text-primary-400"
          : "text-gray-500 dark:text-gray-400 hover:bg-primary-50 dark:hover:bg-primary-900/10 hover:text-primary-600 dark:hover:text-primary-400"
      )}
    >
      {({ isActive }) => (
        <>
          <Icon size={24} weight={isActive ? "fill" : "regular"} className={clsx(isActive ? "" : "group-hover:text-primary-600 dark:group-hover:text-primary-400")} />
          <span>{label}</span>
        </>
      )}
    </NavLink>
  );

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-gray-900/50 z-40 md:hidden backdrop-blur-sm transition-opacity"
          onClick={toggleSidebar}
        />
      )}

      <aside className={clsx(
        "w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col flex-shrink-0 h-full fixed left-0 top-0 z-50 transition-transform duration-300 md:translate-x-0",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-6 border-b border-gray-100 dark:border-gray-700 shadow-sm relative z-10">
          <div className="flex items-center gap-2 text-primary-600 font-bold text-xl uppercase tracking-wider">
            <MonitorPlayIcon size={24} weight="fill" />
            <span>{t('common.adminPortal', 'Admin Portal')}</span>
          </div>
          {/* Mobile Close Button */}
          <button onClick={toggleSidebar} className="md:hidden text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
            <XIcon size={24} />
          </button>
        </div>

        {/* Menu */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto custom-scrollbar">
          <NavItem to="/admin/dashboard" icon={SquaresFourIcon} label={t('sidebar.dashboard')} />
          <NavItem to="/admin/ai-models" icon={BrainIcon} label={t('sidebar.aiModels', 'AI Models')} />
          <NavItem to="/admin/bots" icon={RobotIcon} label={t('sidebar.chatbots')} />
          <NavItem to="/admin/courses" icon={GraduationCapIcon} label={t('sidebar.courses', 'Courses')} />
          <NavItem to="/admin/classes" icon={UsersIcon} label={t('sidebar.classes', 'Classes')} />


          {/* History Collapsible */}
          <div className="space-y-0.5">
            <div className="flex items-center pr-2 group">
              <NavLink end
                to="/admin/history"
                onClick={(e) => {
                  if (window.innerWidth < 768 && toggleSidebar) toggleSidebar();
                }}
                className={({ isActive }) => clsx(
                  "flex-1 flex items-center gap-3 px-4 py-3 rounded-lg transition font-medium text-sm",
                  isActive
                    ? "bg-blue-50 text-blue-600 dark:bg-primary-900/10 dark:text-primary-400"
                    : "text-gray-500 dark:text-gray-400 hover:bg-primary-50 dark:hover:bg-primary-900/10 hover:text-primary-600 dark:hover:text-primary-400"
                )}
              >
                <ClockCounterClockwiseIcon size={24} className="group-hover:text-primary-600 dark:group-hover:text-primary-400" />
                <span>{t('sidebar.history', 'Chat History')}</span>
              </NavLink>

              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setIsHistoryOpen(!isHistoryOpen);
                }}
                className={clsx(
                  "p-2 rounded-lg transition-colors ml-1",
                  isHistoryOpen
                    ? "text-blue-600 dark:text-primary-400 bg-blue-50 dark:bg-primary-900/10"
                    : "text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800"
                )}
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
              <div className="pl-3 border-l border-gray-200 dark:border-gray-700/50 space-y-1 py-1">
                {sessionsLoading ? (
                  <Skeleton className="h-4 w-24 mx-4 my-2" />
                ) : sessions.length === 0 ? (
                  <div className="px-4 py-2 text-xs text-gray-500 italic">No recent sessions</div>
                ) : (
                  sessions.map(session => (
                    <NavLink
                      key={session.id}
                      to={`/admin/chat/${session.bot_id}?sessionId=${session.id}`}
                      onClick={() => window.innerWidth < 768 && toggleSidebar()}
                      className={({ isActive }) => clsx(
                        "group/item flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all text-xs relative",
                        // Check if current URL matches this session ID
                        location.search.includes(`sessionId=${session.id}`)
                          ? "bg-gray-100 text-primary-700 dark:bg-gray-800 dark:text-primary-300 border border-gray-200 dark:border-gray-700"
                          : "text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800/50 hover:text-gray-700 dark:hover:text-gray-200"
                      )}
                    >
                      <div className="flex-1 truncate">
                        <span className="block truncate font-medium">
                          {session.summary_text || session.bots?.name || t('chatbot.new_chat', 'New Chat')}
                        </span>
                      </div>

                      {/* Delete Action */}
                      <button
                        onClick={async (e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          if (window.confirm(t('common.delete') + '?')) {
                            // Check if deleting active session
                            const searchParams = new URLSearchParams(location.search);
                            const currentSessionId = searchParams.get('sessionId');

                            await deleteSessionContext(session.id);

                            if (currentSessionId === session.id) {
                              navigate('/admin/history');
                            }
                          }
                        }}
                        className="p-0.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-gray-400 hover:text-red-500 dark:hover:text-red-400 opacity-0 group-hover/item:opacity-100 transition-opacity"
                      >
                        <TrashIcon size={12} />
                      </button>
                    </NavLink>
                  ))
                )}
              </div>
            </div>
          </div>

          <NavItem to="/admin/documents" icon={FilesIcon} label={t('sidebar.documents')} />
          <NavItem to="/admin/users" icon={UsersIcon} label={t('sidebar.users')} />

          <div className="pt-4 mt-4 border-t border-gray-100 dark:border-gray-700">
            <p className="px-4 text-xs font-semibold text-gray-400 uppercase mb-2">{t('sidebar.system', 'System')}</p>
            <NavItem to="/admin/settings" icon={GearIcon} label={t('sidebar.settings')} />
          </div>
        </nav>

        <div className="p-4 border-t border-gray-100 dark:border-gray-700">
          <button onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 text-gray-500 dark:text-gray-400 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400 rounded-lg transition font-medium text-sm cursor-pointer group">
            <SignOutIcon size={24} className="group-hover:text-red-600" />
            <span>{t('nav.sign_out', 'Sign Out')}</span>
          </button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
