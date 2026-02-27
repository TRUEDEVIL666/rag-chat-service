import React, { useState, useEffect } from 'react';
import PreviewModal from '../../../components/documents/PreviewModal';
import { documentService } from '../../../services/documentService';
import { useTranslation } from 'react-i18next';
import { useNavigate, useLocation, useOutletContext, useParams } from 'react-router-dom';
import { ROUTES } from '../../../routes';
import { usePageTour } from '../../../hooks/usePageTour';
import TourButton from '../../../components/common/TourButton';
import {
  FilePdfIcon,
  FileDocIcon,
  FileTextIcon,
  FileIcon,
  MagnifyingGlassIcon,
  UploadSimpleIcon,
  CircleIcon,
  CheckCircleIcon,
  CaretDownIcon,
  SpinnerIcon,
  TrashIcon,
  WarningIcon,
  ArrowCounterClockwiseIcon,
  EyeIcon,
  DownloadSimpleIcon,
  ArrowLeftIcon
} from '@phosphor-icons/react';
import { clsx } from 'clsx';
import { formatDate, getExtension, formatBytes } from '../../../utils/formatters';
import { useDocuments } from '../../../hooks/useDocuments';

const DocumentList = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { kbId } = useParams();

  // Hooks
  const {
    documents,
    loading: docsLoading,
    error: docsError,
    fetchDocuments,
    batchDeleteDocuments,
    retryDocument
  } = useDocuments();


  const { setTitle } = useOutletContext() || {};

  const kbName = location.state?.kbName || 'Documents';

  useEffect(() => {
    if (setTitle) {
      setTitle(kbName);
    }
  }, [setTitle, kbName]);

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedItems, setSelectedItems] = useState(new Set());
  const [highlightedDocId, setHighlightedDocId] = useState(null);
  const rowRefs = React.useRef({});
  const [sortConfig, setSortConfig] = useState({ key: 'name', direction: 'asc' });
  const [retryingIds, setRetryingIds] = useState(new Set());
  const [isDeleting, setIsDeleting] = useState(false);

  // Preview State
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [previewFileUrl, setPreviewFileUrl] = useState('');
  const [previewFileName, setPreviewFileName] = useState('');
  const [previewFileAppType, setPreviewFileAppType] = useState('');

  const loading = docsLoading || isDeleting;
  const error = docsError;

  const tourSteps = [
    { element: '#doc-header', popover: { title: t('tour.docs.title'), description: t('tour.docs.desc') } },
    { element: '#doc-search', popover: { title: t('tour.docs.search'), description: t('tour.docs.searchDesc') } },
    { element: '#upload-btn', popover: { title: t('tour.docs.upload'), description: t('tour.docs.uploadDesc') } },
    { element: '#doc-list', popover: { title: t('tour.docs.list'), description: t('tour.docs.listDesc') } }
  ];

  const { startTour } = usePageTour('doc-list', tourSteps);

  const loadItems = React.useCallback(async () => {
    if (!kbId) return;
    setSearchQuery('');
    setSelectedItems(new Set());

    try {
      await fetchDocuments(kbId);
    } catch (error) {
      console.error("Load failed:", error);
    }
  }, [kbId, fetchDocuments]);

  // Load items on mount/param change
  useEffect(() => {
    loadItems();
  }, [kbId, loadItems]);

  // Handle Deep Linking highlight
  useEffect(() => {
    if (location.state?.docId) {
      setHighlightedDocId(location.state.docId);
      // Clear highlight after 3 seconds
      setTimeout(() => setHighlightedDocId(null), 3000);
      window.history.replaceState({ ...location.state, docId: undefined }, document.title);
    }
  }, [location.state]);

  const items = React.useMemo(() => documents.map(doc => ({
    id: doc.id,
    name: doc.name,
    type: getExtension(doc.name) === 'pdf' ? 'pdf' : 'file',
    ext: getExtension(doc.name),
    size: doc.size ? formatBytes(doc.size) : '--',
    chunk_count: doc.chunk_count || 0,
    date_added: formatDate(doc.created_at),
    date_modified: formatDate(doc.updated_at),
    added_by: doc.creator?.name || doc.created_by || 'System',
    status: doc.status || 'unknown',
  })), [documents]);

  // Scroll to highlighted item when items load
  useEffect(() => {
    if (highlightedDocId && items.length > 0 && rowRefs.current[highlightedDocId]) {
      rowRefs.current[highlightedDocId].scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [items, highlightedDocId]);



  const handleNavigateUp = () => {
    navigate(ROUTES.ADMIN.DOCUMENTS.LIST);
  };

  const handleNavigateTo = (item) => {
    handlePreview(item);
  };

  const toggleSelection = (id) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedItems(newSelected);
  };

  const handleDelete = async () => {
    if (selectedItems.size === 0) return;

    if (!window.confirm(t('admin.documents.list.deleteConfirm', { count: selectedItems.size }))) {
      return;
    }

    setIsDeleting(true);

    try {
      await batchDeleteDocuments(Array.from(selectedItems));
      await loadItems();
    } catch (error) {
      console.error("Delete failed:", error);
      alert(t('admin.documents.list.deleteError'));
    } finally {
      setIsDeleting(false);
    }
  };

  const filteredItems = React.useMemo(() => {
    let result = [...items];

    if (searchQuery) {
      result = result.filter(item =>
        item.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    if (sortConfig.key) {
      result.sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }

    return result;
  }, [items, searchQuery, sortConfig]);

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const SortIcon = ({ columnKey }) => {
    if (sortConfig.key !== columnKey) return <CaretDownIcon size={12} className="opacity-0 group-hover:opacity-50" />;
    return sortConfig.direction === 'asc'
      ? <CaretDownIcon size={12} className="transform rotate-180 text-primary-600" />
      : <CaretDownIcon size={12} className="text-primary-600" />;
  };

  const getFileIcon = (item) => {
    switch (item.ext) {
      case 'pdf': return <FilePdfIcon className="text-2xl text-red-500" weight="fill" />;
      case 'docx': return <FileDocIcon className="text-2xl text-primary-600" weight="fill" />;
      case 'txt': return <FileTextIcon className="text-2xl text-gray-500" weight="fill" />;
      default: return <FileIcon className="text-2xl text-gray-400" weight="fill" />;
    }
  };

  const handleRetry = async (docId, e) => {
    e.stopPropagation();
    setRetryingIds(prev => {
      const next = new Set(prev);
      next.add(docId);
      return next;
    });

    try {
      await retryDocument(docId);
      await loadItems();
    } catch (err) {
      console.error("Retry failed", err);
    } finally {
      setRetryingIds(prev => {
        const next = new Set(prev);
        next.delete(docId);
        return next;
      });
    }
  };

  const handlePreview = async (item) => {
    setPreviewFileName(item.name);
    setPreviewFileAppType(item.ext);
    setPreviewFileUrl('');
    setPreviewModalOpen(true);

    try {
      const url = await documentService.getDocumentDownloadUrl(item.id);
      setPreviewFileUrl(url);
    } catch (error) {
      console.error("Failed to get preview URL:", error);
    }
  };

  const handleDownload = async (item, e) => {
    e.stopPropagation();
    try {
      const url = await documentService.getDocumentDownloadUrl(item.id);
      window.open(url, '_blank');
    } catch (error) {
      console.error("Failed to get download URL:", error);
      alert(t('common.errorOccurred'));
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden relative bg-gray-50 dark:bg-gray-900 transition-colors">
      {/* File List */}
      <div id="doc-list" className="flex-1 flex flex-col min-h-0">
        <div className="flex-1 flex flex-col min-h-0 px-6 pt-2 pb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <button
                onClick={() => handleNavigateUp()}
                className="p-2 text-gray-500 hover:text-gray-900 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-600 rounded-lg transition-colors flex items-center justify-center"
                title={t('common.back')}
              >
                <ArrowLeftIcon size={20} />
              </button>
              <h2 id="doc-header" className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-3">
                {kbName}
                <TourButton startTour={startTour} />
              </h2>
            </div>
            <div className="flex items-center gap-3">
              {selectedItems.size > 0 && (
                <button
                  onClick={handleDelete}
                  className="flex items-center gap-2 px-3 py-1.5 text-red-600 bg-red-50 hover:bg-red-100 rounded-lg text-sm font-medium transition"
                >
                  <TrashIcon size={18} />
                  <span>{t('common.delete')} ({selectedItems.size})</span>
                </button>
              )}
              <div className="relative">
                <MagnifyingGlassIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  id="doc-search"
                  type="text"
                  placeholder={t('admin.documents.list.searchPlaceholder')}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 pr-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm w-64 focus:ring-2 focus:ring-primary-500 text-gray-900 dark:text-white shadow-sm"
                />
              </div>
              <button
                id="upload-btn"
                onClick={() => {
                  navigate(ROUTES.ADMIN.DOCUMENTS.UPLOAD, { state: { defaultKbId: kbId } });
                }}
                className="btn-primary flex items-center gap-2"
              >
                <UploadSimpleIcon size={20} />
                <span className="hidden sm:inline">{t('admin.documents.list.new')}</span>
              </button>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 flex-1 flex flex-col min-h-0">
            <div className="flex-1 overflow-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700">
                  <tr>
                    <th className="px-6 py-4 text-center">
                      <CircleIcon size={18} className="opacity-0" />
                    </th>
                    <th className="px-6 py-4 text-gray-500 dark:text-gray-400 font-semibold uppercase tracking-wider text-xs">
                      {t('admin.documents.list.table.type')}
                    </th>
                    <th
                      className="px-6 py-4 text-gray-500 dark:text-gray-400 font-semibold uppercase tracking-wider text-xs cursor-pointer hover:text-primary-600 transition-colors"
                      onClick={() => handleSort('name')}
                    >
                      <div className="flex items-center gap-2">
                        {t('admin.documents.list.table.name')}
                        <SortIcon columnKey="name" />
                      </div>
                    </th>
                    <th
                      className="px-6 py-4 text-gray-500 dark:text-gray-400 font-semibold uppercase tracking-wider text-xs cursor-pointer hover:text-primary-600 transition-colors"
                      onClick={() => handleSort('status')}
                    >
                      <div className="flex items-center gap-2">
                        {t('admin.documents.list.table.status')}
                        <SortIcon columnKey="status" />
                      </div>
                    </th>
                    <th
                      className="px-6 py-4 text-gray-500 dark:text-gray-400 font-semibold uppercase tracking-wider text-xs cursor-pointer hover:text-primary-600 transition-colors"
                      onClick={() => handleSort('date_added')}
                    >
                      <div className="flex items-center gap-2">
                        {t('admin.documents.list.table.dateAdded')}
                        <SortIcon columnKey="date_added" />
                      </div>
                    </th>
                    <th
                      className="px-6 py-4 text-gray-500 dark:text-gray-400 font-semibold uppercase tracking-wider text-xs cursor-pointer hover:text-primary-600 transition-colors"
                      onClick={() => handleSort('date_modified')}
                    >
                      <div className="flex items-center gap-2">
                        {t('list.table.dateModified')}
                        <SortIcon columnKey="date_modified" />
                      </div>
                    </th>
                    <th
                      className="px-6 py-4 text-gray-500 dark:text-gray-400 font-semibold uppercase tracking-wider text-xs cursor-pointer hover:text-primary-600 transition-colors"
                      onClick={() => handleSort('added_by')}
                    >
                      <div className="flex items-center gap-2">
                        {t('admin.documents.list.table.addedBy')}
                        <SortIcon columnKey="added_by" />
                      </div>
                    </th>
                    <th className="px-6 py-4 text-center text-gray-500 dark:text-gray-400 font-semibold uppercase tracking-wider text-xs">
                      {t('admin.documents.list.table.actions')}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {loading ? (
                    <tr>
                      <td colSpan="8" className="px-6 py-20 text-center">
                        <div className="flex flex-col items-center justify-center">
                          <SpinnerIcon size={32} className="animate-spin text-primary-600 mb-3" />
                          <span className="text-sm font-medium text-gray-600 dark:text-gray-300">{t('common.processing')}</span>
                        </div>
                      </td>
                    </tr>
                  ) : error ? (
                    <tr>
                      <td colSpan="8" className="px-6 py-12 text-center bg-red-50 dark:bg-red-900/10 rounded-lg">
                        <div className="flex flex-col items-center gap-3">
                          <WarningIcon size={40} className="text-red-600 dark:text-red-400" />
                          <div className="space-y-1">
                            <p className="font-semibold text-gray-800 dark:text-slate-200">{t('common.errorOccurred')}</p>
                            <p className="text-sm text-red-600 dark:text-red-400 max-w-md mx-auto">{error?.message || String(error)}</p>
                          </div>
                          <button
                            onClick={loadItems}
                            className="mt-4 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-all"
                          >
                            {t('common.retry', 'Try Again')}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ) : filteredItems.length === 0 ? (
                    <tr>
                      <td colSpan="8" className="px-6 py-16 text-center">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-700 mb-4">
                          <FileIcon size={32} className="text-gray-400" />
                        </div>
                        <p className="text-gray-500 dark:text-gray-400">{t('admin.documents.list.empty')}</p>
                      </td>
                    </tr>
                  ) : (
                    filteredItems.map((item) => (
                      <tr
                        key={item.id}
                        ref={el => rowRefs.current[item.id] = el}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleNavigateTo(item);
                        }}
                        className={clsx(
                          "group hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer",
                          selectedItems.has(item.id) && "bg-primary-50 dark:bg-primary-900/10",
                          highlightedDocId === item.id && "bg-amber-50 dark:bg-amber-900/10"
                        )}
                      >
                        <td className="px-6 py-4 text-center">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleSelection(item.id);
                            }}
                            className={clsx(
                              "focus:outline-none transition-colors",
                              selectedItems.has(item.id) ? "text-primary-600 dark:text-primary-400" : "text-gray-400 dark:text-gray-500 hover:text-primary-600"
                            )}
                          >
                            {selectedItems.has(item.id) ? <CheckCircleIcon size={20} weight="fill" /> : <CircleIcon size={20} />}
                          </button>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center justify-center">
                            {getFileIcon(item)}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="font-medium text-gray-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors" title={item.name}>
                            {item.name}
                          </div>
                          {item.added_by && (
                            <div className="text-xs text-gray-500 dark:text-gray-400">{item.added_by}</div>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <span className={clsx(
                            "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
                            item.status === 'error' || item.status === 'failed' || item.status === 'Error'
                              ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300"
                              : item.status === 'processing' || item.status === 'pending'
                                ? "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300"
                                : "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
                          )}>
                            {item.status === 'error' || item.status === 'failed' || item.status === 'Error' && (
                              <WarningIcon size={12} className="mr-1" />
                            )}
                            {item.status}
                          </span>
                          {(item.status === 'error' || item.status === 'failed' || item.status === 'Error') && (
                            <button
                              onClick={(e) => handleRetry(item.id, e)}
                              className="ml-2 p-1 text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors disabled:opacity-50"
                              title={t('list.retry', 'Retry processing')}
                              disabled={retryingIds.has(item.id)}
                            >
                              {retryingIds.has(item.id) ? (
                                <SpinnerIcon className="animate-spin" size={16} />
                              ) : (
                                <ArrowCounterClockwiseIcon size={16} />
                              )}
                            </button>
                          )}
                        </td>
                        <td className="px-6 py-4 text-gray-500 dark:text-gray-400 text-sm whitespace-nowrap">
                          {item.date_added}
                        </td>
                        <td className="px-6 py-4 text-gray-500 dark:text-gray-400 text-sm whitespace-nowrap">
                          {item.date_modified}
                        </td>
                        <td className="px-6 py-4 text-gray-500 dark:text-gray-400 text-sm max-w-xs truncate" title={item.added_by}>
                          {item.added_by}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center justify-center gap-1.5">
                            <button
                              onClick={(e) => { e.stopPropagation(); handlePreview(item); }}
                              className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors"
                              title={t('common.preview', 'Preview')}
                            >
                              <EyeIcon size={18} />
                            </button>
                            <button
                              onClick={(e) => handleDownload(item, e)}
                              className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors"
                              title={t('common.download', 'Download')}
                            >
                              <DownloadSimpleIcon size={18} />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                if (window.confirm(t('admin.documents.list.deleteConfirmSingle'))) {
                                  batchDeleteDocuments([item.id]);
                                  loadItems();
                                }
                              }}
                              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                              title={t('common.delete', 'Delete')}
                            >
                              <TrashIcon size={18} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <div className="text-sm text-gray-500 dark:text-gray-400">
                {t('admin.documents.list.footer.itemsCount', { count: filteredItems.length })}
              </div>
              {filteredItems.length > 0 && (
                <div className="flex gap-1">
                  <button className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50">
                    {t('common.previous', 'Previous')}
                  </button>
                  <button className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
                    1
                  </button>
                  <button className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
                    2
                  </button>
                  <button className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
                    3
                  </button>
                  <button className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
                    {t('common.next', 'Next')}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      <PreviewModal
        isOpen={previewModalOpen}
        onClose={() => setPreviewModalOpen(false)}
        fileUrl={previewFileUrl}
        fileName={previewFileName}
        fileAppType={previewFileAppType}
      />
    </div >
  );
};

export default DocumentList;
