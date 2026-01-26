import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import {
  BooksIcon,
  CalendarBlankIcon,
  CaretLeftIcon,
  ChalkboardTeacherIcon,
  DownloadSimpleIcon,
  EyeIcon,
  FileDocIcon,
  FileIcon,
  FilePdfIcon,
  FilesIcon,
  FileTextIcon,
  RobotIcon,
  StudentIcon
} from '@phosphor-icons/react';

import BotCard from '../../components/user/BotCard';
import Skeleton from '../../components/common/Skeleton';
import { useChat } from '../../context/ChatContext';
import { ROUTES } from '../../routes';
import courseService from '../../services/courseService';

const UserClassDetail = () => {
  const { t, i18n } = useTranslation();
  const { id } = useParams();
  const navigate = useNavigate();
  const { setActiveSession } = useChat();

  const [classData, setClassData] = useState(null);
  const [bots, setBots] = useState([]);

  const [activeTab, setActiveTab] = useState('assistants');
  const [viewMode, setViewMode] = useState('folders'); // 'folders' or 'files'
  const [kbs, setKbs] = useState([]);
  const [selectedKB, setSelectedKB] = useState(null);
  const [docs, setDocs] = useState([]); // Docs for the selected KB
  const [allDocs, setAllDocs] = useState(null); // Cache for all class documents
  const [loading, setLoading] = useState(true);
  const [docsLoading, setDocsLoading] = useState(false);

  useEffect(() => {
    fetchClassDetails();
  }, [id]);

  const fetchClassDetails = async () => {
    try {
      setLoading(true);
      const [cls, classBots, classKbs] = await Promise.all([
        courseService.getClass(id),
        courseService.getClassBots(id),
        courseService.getClassKBs(id)
      ]);

      setClassData(cls);
      setBots(classBots);
      setKbs(classKbs || []);
    } catch (error) {
      console.error('Failed to fetch class details:', error);
    } finally {
      setLoading(false);
    }
  };

  const getBotVisuals = (bot) => {
    const name = bot.name.toLowerCase();
    if (name.includes('academic') || name.includes('student') || name.includes('sinh viên')) return { icon: <StudentIcon weight="fill" className="text-xl" />, color: 'blue' };
    if (name.includes('admin') || name.includes('staff')) return { icon: <FilesIcon weight="fill" className="text-xl" />, color: 'orange' };
    if (name.includes('library') || name.includes('thư viện')) return { icon: <BooksIcon weight="fill" className="text-xl" />, color: 'emerald' };
    return { icon: <RobotIcon weight="fill" className="text-xl" />, color: 'indigo' };
  };

  const getFileIcon = (fileName) => {
    const ext = fileName.split('.').pop().toLowerCase();
    if (ext === 'pdf') return <FilePdfIcon className="text-rose-500" size={24} />;
    if (['doc', 'docx'].includes(ext)) return <FileDocIcon className="text-blue-500" size={24} />;
    if (ext === 'txt') return <FileTextIcon className="text-slate-500" size={24} />;
    return <FileIcon className="text-indigo-500" size={24} />;
  };

  const handleViewDocument = async (doc) => {
    try {
      const { url } = await courseService.getDocumentViewUrl(doc.id);
      window.open(url, '_blank');
    } catch (error) {
      console.error("Failed to get document view URL", error);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 p-6 md:p-8 space-y-8 max-w-7xl mx-auto w-full">
        {/* Header Skeleton */}
        <div className="flex items-start justify-between">
          <div className="space-y-4 w-full">
            <Skeleton className="h-6 w-24 rounded-full" />
            <Skeleton className="h-10 w-2/3 max-w-xl rounded-lg" />
            <div className="flex gap-4">
              <Skeleton className="h-5 w-32" />
              <Skeleton className="h-5 w-40" />
            </div>

            {/* Tabs Skeleton */}
            <div className="flex gap-2 pt-4">
              <Skeleton className="h-10 w-32 rounded-full" />
              <Skeleton className="h-10 w-36 rounded-full" />
              <Skeleton className="h-10 w-28 rounded-full" />
            </div>
          </div>
        </div>

        {/* Content Skeleton - Grid of cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => (
            <div key={i} className="border border-slate-200 dark:border-gray-700 rounded-2xl p-6 space-y-4">
              <div className="flex items-start justify-between">
                <Skeleton className="w-12 h-12 rounded-xl" />
                <Skeleton className="w-8 h-8 rounded-full" />
              </div>
              <Skeleton className="h-6 w-3/4 rounded-md" />
              <Skeleton className="h-4 w-full rounded-md" />
              <Skeleton className="h-4 w-2/3 rounded-md" />
              <Skeleton className="h-10 w-full rounded-xl mt-4" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!classData) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
        <ChalkboardTeacherIcon size={48} className="mb-4 opacity-50" />
        <p>{t('courses.class.notFound', 'Class not found')}</p>
        <button
          onClick={() => navigate('/user/classes')}
          className="mt-4 text-indigo-600 hover:underline"
        >
          {t('common.back', 'Back')}
        </button>
      </div>
    );
  }

  // Helper to group docs by KB - No longer needed in Folder Mode, but nice to keep if we switch back or for analysis
  // const groupedDocs = ...

  const handleKBClick = async (kb) => {
    try {
      setDocsLoading(true);
      setSelectedKB(kb);
      setViewMode('files');

      let currentAllDocs = allDocs;
      if (!currentAllDocs) {
        // Fetch only if not cached
        currentAllDocs = await courseService.getClassDocuments(id);
        setAllDocs(currentAllDocs);
      }

      const filtered = currentAllDocs.filter(d => d.knowledgebase_id === kb.id);
      setDocs(filtered);
    } catch (error) {
      console.error("Failed to load KB docs", error);
    } finally {
      setDocsLoading(false);
    }
  };

  const handleBackToFolders = () => {
    setViewMode('folders');
    setSelectedKB(null);
    setDocs([]);
  };

  return (
    <div className="flex-1 overflow-y-auto bg-slate-50 dark:bg-black/20 relative">
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">

        {/* Header / Breadcrumb */}
        <div>
          <button
            onClick={() => navigate('/user/classes')}
            className="flex items-center gap-2 text-sm text-slate-500 hover:text-indigo-600 dark:hover:text-indigo-400 mb-4 transition-colors"
          >
            <CaretLeftIcon />
            {t('nav.classes', 'My Classes')}
          </button>

          <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 p-8 opacity-5">
              <ChalkboardTeacherIcon size={160} weight="fill" />
            </div>

            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-2">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-50 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-300 border border-indigo-100 dark:border-indigo-500/20">
                  {classData.course_code || 'COURSE'}
                </span>
                <span className="text-sm text-slate-500 dark:text-slate-400 font-medium flex items-center gap-1">
                  <CalendarBlankIcon />
                  {classData.semester_name || 'Current Semester'}
                </span>
              </div>
              <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white mb-2">
                {classData.name}
              </h1>
              <p className="text-lg text-slate-600 dark:text-slate-300 max-w-2xl">
                {classData.course_name}
              </p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-6 border-b border-slate-200 dark:border-slate-800">
          <button
            onClick={() => setActiveTab('assistants')}
            className={`pb-4 text-sm font-semibold flex items-center gap-2 transition-all relative ${activeTab === 'assistants'
              ? 'text-indigo-600 dark:text-indigo-400'
              : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
          >
            <RobotIcon size={20} weight={activeTab === 'assistants' ? 'fill' : 'regular'} />
            {t('courses.detail.bots', 'Assistants')}
            {activeTab === 'assistants' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600 dark:bg-indigo-400 rounded-t-full" />
            )}
          </button>

          <button
            onClick={() => setActiveTab('documents')}
            className={`pb-4 text-sm font-semibold flex items-center gap-2 transition-all relative ${activeTab === 'documents'
              ? 'text-indigo-600 dark:text-indigo-400'
              : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
          >
            <FilesIcon size={20} weight={activeTab === 'documents' ? 'fill' : 'regular'} />
            {t('nav.documents', 'Documents')}
            {activeTab === 'documents' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600 dark:bg-indigo-400 rounded-t-full" />
            )}
          </button>
        </div>

        {/* Tab Content */}
        <div className="min-h-[400px]">
          {activeTab === 'assistants' ? (
            <div className="space-y-6 animate-fade-in-up">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-slate-800 dark:text-white">
                  {t('home.suggestions.available_bots', 'Available Assistants')}
                </h3>
              </div>

              {bots.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {bots.map(bot => {
                    const visuals = getBotVisuals(bot);
                    return (
                      <BotCard
                        key={bot.id}
                        icon={visuals.icon}
                        color={visuals.color}
                        title={bot.name}
                        desc={bot.description}
                        onClick={() => {
                          setActiveSession({ botId: bot.id, botName: bot.name, title: "New Chat", isExisting: false });
                          navigate(ROUTES.USER.CHAT(bot.id), { state: { bot } });
                        }}
                      />
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-20 bg-white dark:bg-slate-900/50 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700">
                  <RobotIcon size={48} className="mx-auto text-slate-300 mb-4" />
                  <p className="text-slate-500">{t('courses.class.noBots', 'No bots assigned')}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-6 animate-fade-in-up">
              {viewMode === 'folders' ? (
                <>
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-slate-800 dark:text-white">
                      {t('nav.documents', 'Documents')}
                    </h3>
                  </div>

                  {kbs.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {kbs.map(kb => (
                        <div
                          key={kb.id}
                          onClick={() => handleKBClick(kb)}
                          className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-indigo-500 dark:hover:border-indigo-500 cursor-pointer transition-all hover:shadow-lg group"
                        >
                          <div className="flex items-start justify-between mb-4">
                            <div className="p-3 bg-indigo-50 dark:bg-indigo-500/10 rounded-xl text-indigo-600 dark:text-indigo-400 group-hover:scale-110 transition-transform">
                              <FilesIcon size={32} weight="duotone" />
                            </div>

                          </div>
                          <h3 className="font-bold text-slate-800 dark:text-white text-lg mb-1 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                            {kb.name}
                          </h3>
                          <p className="text-sm text-slate-500 dark:text-slate-400 line-clamp-2">
                            {kb.description || t('common.no_description', 'No description')}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-20 bg-white dark:bg-slate-900/50 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700">
                      <FilesIcon size={48} className="mx-auto text-slate-300 mb-4" />
                      <h3 className="text-lg font-medium text-slate-700 dark:text-slate-300">
                        {t('classes.details.no_kbs', 'No Knowledge Bases Found')}
                      </h3>
                      <p className="text-slate-500 max-w-sm mx-auto mt-2">
                        {t('classes.details.no_kbs_desc', 'This class has no linked knowledge bases yet.')}
                      </p>
                    </div>
                  )}
                </>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <button
                      onClick={handleBackToFolders}
                      className="p-2 -ml-2 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                    >
                      <CaretLeftIcon size={24} />
                    </button>
                    <div>
                      <h3 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
                        <FilesIcon className="text-indigo-500" size={24} />
                        {selectedKB?.name}
                      </h3>
                    </div>
                  </div>

                  {docsLoading ? (
                    <div className="space-y-4">
                      {[1, 2, 3].map(i => (
                        <div key={i} className="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-slate-200 dark:border-slate-800 flex items-center gap-4">
                          <Skeleton className="w-10 h-10 rounded-lg" />
                          <div className="flex-1 space-y-2">
                            <Skeleton className="h-4 w-1/3 rounded" />
                            <Skeleton className="h-3 w-1/4 rounded" />
                          </div>
                          <Skeleton className="w-8 h-8 rounded-lg" />
                        </div>
                      ))}
                    </div>
                  ) : docs.length > 0 ? (
                    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm animate-fade-in-up">
                      <table className="w-full text-left">
                        <thead>
                          <tr className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 text-xs font-bold uppercase tracking-wider">
                            <th className="px-6 py-4">{t('documents.table.name', 'Name')}</th>
                            <th className="px-6 py-4 text-right">{t('common.actions', 'Actions')}</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                          {docs.map((doc) => (
                            <tr key={doc.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors group">
                              <td className="px-6 py-4">
                                <div className="flex items-center gap-3">
                                  <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded-lg group-hover:bg-white dark:group-hover:bg-slate-700 transition-colors">
                                    {getFileIcon(doc.name)}
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <div className="text-sm font-semibold text-slate-700 dark:text-slate-200 line-clamp-1 truncate">
                                      {doc.name}
                                    </div>
                                  </div>
                                </div>
                              </td>
                              <td className="px-6 py-4 text-right">
                                <div className="flex items-center justify-end gap-2">

                                  <button
                                    onClick={() => handleViewDocument(doc)}
                                    className="p-2 text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-all"
                                    title={t('common.view', 'View')}
                                  >
                                    <EyeIcon size={18} />
                                  </button>
                                  <button
                                    className="p-2 text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-all"
                                    title={t('common.download', 'Download')}
                                  >
                                    <DownloadSimpleIcon size={18} />
                                  </button>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-center py-20 bg-white dark:bg-slate-900/50 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700">
                      <FilesIcon size={48} className="mx-auto text-slate-300 mb-4" />
                      <h3 className="text-lg font-medium text-slate-700 dark:text-slate-300">
                        {t('classes.details.empty_kb', 'Folder Empty')}
                      </h3>
                      <p className="text-slate-500 max-w-sm mx-auto mt-2">
                        {t('classes.details.empty_kb_desc', 'There are no documents in this folder yet.')}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserClassDetail;
