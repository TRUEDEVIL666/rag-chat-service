import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { calculateChunks, getDefaultParams } from '../../../utils/chunking';
import { formatSize } from '../../../utils/formatters';
import { useNavigate, useLocation } from 'react-router-dom';
import { ROUTES } from '../../../routes';
import { useDocuments } from '../../../hooks/useDocuments';
import { useKnowledgeBases } from '../../../hooks/useKnowledgeBases';
import {
  ArrowLeftIcon,
  BooksIcon,
  CaretDownIcon,
  ScissorsIcon,
  EyeIcon,
  CloudArrowUpIcon,
  FileTextIcon,
  TrashIcon,
  PaperPlaneTiltIcon,
  SpinnerIcon,
  InfoIcon,
  LightbulbIcon,
  CheckSquareIcon,
  SquareIcon,
} from '@phosphor-icons/react';
import { clsx } from 'clsx';



import { usePageTour } from '../../../hooks/usePageTour';
import TourButton from '../../../components/common/TourButton';

const UploadDocument = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { kbs, loading: kbsLoading, error: kbsError, fetchKBs } = useKnowledgeBases(); // Destructure loading and error
  const { uploadDocuments } = useDocuments();

  const defaultKbId = location.state?.defaultKbId;
  const [selectedFiles, setSelectedFiles] = useState([]);
  // Removed commented out kbList state
  const [selectedKb, setSelectedKb] = useState('default');
  const [chunkingMethod, setChunkingMethod] = useState('sentence');
  const [enableSparse, setEnableSparse] = useState(false);
  // ... rest of state
  const [previewText, setPreviewText] = useState(t('admin.documents.upload.preview.defaultExample'));
  const [chunks, setChunks] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [msg, setMsg] = useState({ text: '', type: '' });
  const fileInputRef = useRef(null);

  const tourSteps = [
    { element: '#upload-header', popover: { title: t('tour.upload.title'), description: t('tour.upload.desc') } },
    { element: '#kb-select', popover: { title: t('tour.upload.kb'), description: t('tour.upload.kbDesc') } },
    { element: '#chunk-settings', popover: { title: t('tour.upload.chunk'), description: t('tour.upload.chunkDesc') } },
    { element: '#drop-zone', popover: { title: t('tour.upload.drop'), description: t('tour.upload.dropDesc') } },
    { element: '#preview-area', popover: { title: t('tour.upload.preview'), description: t('tour.upload.previewDesc') } },
    { element: '#start-upload-btn', popover: { title: t('tour.upload.start'), description: t('tour.upload.startDesc') } }
  ];

  const { startTour } = usePageTour('upload-docs', tourSteps);

  // Chunking Params State ...
  const [chunkSize, setChunkSize] = useState('');
  const [chunkOverlap, setChunkOverlap] = useState('');
  const [windowSize, setWindowSize] = useState('');
  const [separator, setSeparator] = useState('\\n\\n');
  const [thresholdPercentage, setThresholdPercentage] = useState('');
  const [bufferSize, setBufferSize] = useState('');
  const [chunkSizes, setChunkSizes] = useState(''); // "2048, 512, 128"

  useEffect(() => {
    // Set defaults when method changes
    const defaults = getDefaultParams(chunkingMethod);
    if (defaults.chunkSize !== undefined) setChunkSize(defaults.chunkSize);
    if (defaults.chunkOverlap !== undefined) setChunkOverlap(defaults.chunkOverlap);
    if (defaults.windowSize !== undefined) setWindowSize(defaults.windowSize);
    if (defaults.separator !== undefined) setSeparator(defaults.separator);
    if (defaults.bufferSize !== undefined) setBufferSize(defaults.bufferSize);
    if (defaults.thresholdPercentage !== undefined) setThresholdPercentage(defaults.thresholdPercentage);
    if (defaults.chunkSizes !== undefined) setChunkSizes(defaults.chunkSizes);
  }, [chunkingMethod]);

  // Load KBs
  useEffect(() => {
    fetchKBs();
  }, [fetchKBs]);

  useEffect(() => {
    // Normalization helper
    const normalize = (s) => s ? s.replace(/\r\n/g, '\n').trim() : '';
    const current = normalize(previewText);

    const getDefaults = (lang) => [
      i18n.getResource(lang, 'translation', 'admin.documents.upload.preview.defaultExample'),
      i18n.getResource(lang, 'translation', 'admin.documents.upload.preview.recursiveExample')
    ].map(normalize);

    const enDefaults = getDefaults('en');
    const viDefaults = getDefaults('vi');
    const allDefaults = [...enDefaults, ...viDefaults];

    if (allDefaults.includes(current) || !current) {
      if (chunkingMethod === 'recursive') {
        setPreviewText(t('admin.documents.upload.preview.recursiveExample'));
      } else {
        setPreviewText(t('admin.documents.upload.preview.defaultExample'));
      }
    }
  }, [i18n.language, chunkingMethod]);

  useEffect(() => {
    updateChunkPreview();
  }, [previewText, chunkingMethod, chunkSize, chunkOverlap, windowSize, separator, thresholdPercentage, bufferSize, chunkSizes]);

  // Set default selected KB when KBs load
  useEffect(() => {
    if (kbs.length > 0) {
      if (defaultKbId && kbs.some(kb => kb.id === defaultKbId)) {
        setSelectedKb(defaultKbId);
      } else {
        setSelectedKb(kbs[0].id);
      }
    }
  }, [kbs, defaultKbId]);

  const updateChunkPreview = () => {
    if (!previewText) {
      setChunks([]);
      return;
    }

    let chunksDisplay = [];
    const text = previewText;

    // Simulation logic matching original HTML
    const params = {
      chunkSize, chunkOverlap, windowSize,
      separator, bufferSize, thresholdPercentage,
      chunkSizes
    };

    setChunks(calculateChunks(text, chunkingMethod, params));
  };


  const renderChunkingParams = () => {
    switch (chunkingMethod) {
      case 'sentence':
        return (
          <div onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-slide-up mt-6">
            <div>
              <label onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 min-h-[2.5rem] flex items-end">{t('admin.documents.upload.chunking.params.chunkSize')}</label>
              <input type="number" value={chunkSize} onChange={e => setChunkSize(e.target.value)} placeholder="Default" onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-none rounded-xl outline-none focus:ring-2 focus:ring-primary-500/20 transition-all text-gray-700 dark:text-gray-200" />
            </div>
            <div>
              <label onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 min-h-[2.5rem] flex items-end">{t('admin.documents.upload.chunking.params.chunkOverlap')}</label>
              <input type="number" value={chunkOverlap} onChange={e => setChunkOverlap(e.target.value)} placeholder="Default" onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-none rounded-xl outline-none focus:ring-2 focus:ring-primary-500/20 transition-all text-gray-700 dark:text-gray-200" />
            </div>
          </div>
        );
      case 'token':
      case 'word':
      case 'recursive':
        return (
          <div onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-slide-up mt-6">
            <div>
              <label onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 min-h-[2.5rem] flex items-end">{t('admin.documents.upload.chunking.params.chunkSize')}</label>
              <input type="number" value={chunkSize} onChange={e => setChunkSize(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-none rounded-xl outline-none focus:ring-2 focus:ring-primary-500/20 transition-all text-gray-700 dark:text-gray-200" />
            </div>
            <div>
              <label onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 min-h-[2.5rem] flex items-end">{t('admin.documents.upload.chunking.params.chunkOverlap')}</label>
              <input type="number" value={chunkOverlap} onChange={e => setChunkOverlap(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-none rounded-xl outline-none focus:ring-2 focus:ring-primary-500/20 transition-all text-gray-700 dark:text-gray-200" />
            </div>
          </div>
        );
      case 'character':
        return (
          <div onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-slide-up mt-6">
            <div>
              <label onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 min-h-[2.5rem] flex items-end">{t('admin.documents.upload.chunking.params.chunkSize')}</label>
              <input type="number" value={chunkSize} onChange={e => setChunkSize(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-none rounded-xl outline-none focus:ring-2 focus:ring-primary-500/20 transition-all text-gray-700 dark:text-gray-200" />
            </div>
            <div>
              <label onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 min-h-[2.5rem] flex items-end">{t('admin.documents.upload.chunking.params.chunkOverlap')}</label>
              <input type="number" value={chunkOverlap} onChange={e => setChunkOverlap(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-none rounded-xl outline-none focus:ring-2 focus:ring-primary-500/20 transition-all text-gray-700 dark:text-gray-200" />
            </div>
            <div>
              <label onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 min-h-[2.5rem] flex items-end">{t('admin.documents.upload.chunking.params.separator')}</label>
              <input type="text" value={separator} onChange={e => setSeparator(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-none rounded-xl outline-none focus:ring-2 focus:ring-primary-500/20 transition-all text-gray-700 dark:text-gray-200" />
            </div>
          </div>
        );
      case 'sliding':
        return (
          <div onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="animate-slide-up mt-6">
            <label onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">{t('admin.documents.upload.chunking.params.windowSize')}</label>
            <input type="number" value={windowSize} onChange={e => setWindowSize(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-none rounded-xl outline-none focus:ring-2 focus:ring-primary-500/20 transition-all text-gray-700 dark:text-gray-200" />
          </div>
        );
      case 'semantic':
        return (
          <div onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-slide-up mt-6">
            <div>
              <label onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">{t('admin.documents.upload.chunking.params.bufferSize')}</label>
              <input type="number" value={bufferSize} onChange={e => setBufferSize(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-none rounded-xl outline-none focus:ring-2 focus:ring-primary-500/20 transition-all text-gray-700 dark:text-gray-200" />
            </div>
            <div>
              <label onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">{t('admin.documents.upload.chunking.params.threshold')}</label>
              <input type="number" value={thresholdPercentage} onChange={e => setThresholdPercentage(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-none rounded-xl outline-none focus:ring-2 focus:ring-primary-500/20 transition-all text-gray-700 dark:text-gray-200" />
            </div>
          </div>
        );
      case 'hierarchical':
        return (
          <div onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="animate-slide-up mt-6">
            <label onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">{t('admin.documents.upload.chunking.params.chunkSizes')}</label>
            <input type="text" value={chunkSizes} onChange={e => setChunkSizes(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()} className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-none rounded-xl outline-none focus:ring-2 focus:ring-primary-500/20 transition-all text-gray-700 dark:text-gray-200" />
          </div>
        );
      default: return null;
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files);
      setSelectedFiles(prev => {
        const uniqueNewFiles = newFiles.filter(nf => !prev.some(pf => pf.name === nf.name));
        return [...prev, ...uniqueNewFiles];
      });
    }
  };

  const handleRemoveFile = (fileName) => {
    setSelectedFiles(prev => prev.filter(f => f.name !== fileName));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files);
      setSelectedFiles(prev => {
        const uniqueNewFiles = newFiles.filter(nf => !prev.some(pf => pf.name === nf.name));
        return [...prev, ...uniqueNewFiles];
      });
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (selectedFiles.length === 0) {
      setMsg({ text: t('admin.documents.upload.alert.selectAtLeastOne'), type: "error" });
      return;
    }


    // Validation Logic
    const cSize = parseInt(chunkSize);
    const cOverlap = parseInt(chunkOverlap);

    if (['sentence', 'token', 'word', 'character', 'recursive'].includes(chunkingMethod)) {
      if (isNaN(cSize) || cSize <= 0) {
        setMsg({ text: t('admin.documents.upload.validation.invalidChunkSize'), type: "error" });
        return;
      }
      if (isNaN(cOverlap) || cOverlap < 0) {
        setMsg({ text: t('admin.documents.upload.validation.negativeOverlap'), type: "error" });
        return;
      }
      if (cOverlap >= cSize) {
        setMsg({ text: t('admin.documents.upload.validation.overlapTooLarge'), type: "error" });
        return;
      }
    }

    if (chunkingMethod === 'character' && !separator) {
      setMsg({ text: t('admin.documents.upload.validation.emptySeparator'), type: "error" });
      return;
    }

    if (chunkingMethod === 'sliding') {
      if (isNaN(parseInt(windowSize)) || parseInt(windowSize) < 1) {
        setMsg({ text: t('admin.documents.upload.validation.invalidWindowSize'), type: "error" });
        return;
      }
    }

    if (chunkingMethod === 'semantic') {
      if (isNaN(parseInt(bufferSize)) || parseInt(bufferSize) < 1) {
        setMsg({ text: t('admin.documents.upload.validation.invalidBufferSize'), type: "error" });
        return;
      }
      const threshold = parseInt(thresholdPercentage);
      if (isNaN(threshold) || threshold < 0 || threshold > 100) {
        setMsg({ text: t('admin.documents.upload.validation.invalidThreshold'), type: "error" });
        return;
      }
    }

    if (chunkingMethod === 'hierarchical') {
      try {
        let sizes;
        // Try parsing string format "2048, 512, 128"
        if (typeof chunkSizes === 'string' && chunkSizes.includes(',')) {
          sizes = chunkSizes.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
        } else {
          // Try JSON parse fallback
          sizes = JSON.parse(chunkSizes);
        }

        if (!Array.isArray(sizes) || sizes.some(s => typeof s !== 'number' || s <= 0)) {
          throw new Error();
        }
        // Check for descending order
        const sorted = [...sizes].sort((a, b) => b - a);
        if (JSON.stringify(sizes) !== JSON.stringify(sorted)) {
          setMsg({ text: t('admin.documents.upload.validation.hierarchicalOrder'), type: "error" });
          return;
        }
      } catch (e) {
        setMsg({ text: t('admin.documents.upload.validation.invalidHierarchical'), type: "error" });
        return;
      }
    }

    setUploading(true);
    setMsg({ text: "", type: "" });

    const formData = new FormData();
    formData.append("knowledge_base_id", selectedKb);
    formData.append("chunking_method", chunkingMethod);
    const chunkingParams = {};
    if (chunkSize) chunkingParams.chunk_size = parseInt(chunkSize);
    if (chunkOverlap) chunkingParams.chunk_overlap = parseInt(chunkOverlap);
    if (windowSize) chunkingParams.window_size = parseInt(windowSize);
    if (separator) chunkingParams.separator = separator;
    if (thresholdPercentage) chunkingParams.threshold_percentage = parseInt(thresholdPercentage);
    if (bufferSize) chunkingParams.buffer_size = parseInt(bufferSize);
    if (chunkSizes) chunkingParams.chunk_sizes = chunkSizes;

    // Add sparse embedding flag
    formData.append("sparse_embedding", enableSparse);

    formData.append("chunking_params", JSON.stringify(chunkingParams));
    selectedFiles.forEach(file => {
      formData.append("files", file);
    });

    try {
      await uploadDocuments(selectedKb, formData, (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        // Progress handling if needed
      });

      setMsg({ text: t('admin.documents.upload.alert.uploadSuccess'), type: "success" });
      setTimeout(() => navigate(ROUTES.ADMIN.DOCUMENTS.LIST), 1500);

    } catch (error) {
      console.error("Upload failed", error);
      const detail = error.response?.data?.detail || error.message;
      setMsg({ text: `${t('common.actionFailed')}: ${detail}`, type: "error" });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-gray-50 dark:bg-gray-900 transition-colors">

      {/* Form Scroll Area */}
      <div className="flex-1 overflow-auto p-10 flex justify-center">
        <div className="w-full animate-slide-up">
          <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-3xl shadow-xl dark:shadow-2xl border border-gray-200 dark:border-gray-600 p-8 lg:p-10 relative overflow-hidden grid grid-cols-1 lg:grid-cols-12 gap-10">
            <div className="lg:col-span-12">
              <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6 sticky top-0 z-50 -mx-8 lg:-mx-10 -mt-8 lg:-mt-10 mb-8">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => navigate(ROUTES.ADMIN.DOCUMENTS.LIST)}
                    className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors text-gray-500"
                  >
                    <ArrowLeftIcon size={24} />
                  </button>
                  <div>
                    <div className="flex items-center gap-3">
                      <h1 id="upload-header" className="text-xl font-bold text-gray-900 dark:text-white leading-tight">{t('admin.documents.upload.title')}</h1>
                      <TourButton startTour={startTour} />
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{t('admin.documents.upload.subtitle')}</p>
                  </div>
                </div>
              </header>          </div>

            {/* Selection Section */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:col-span-12">
              <div id="kb-select">
                <label className="block text-sm font-bold text-primary-600 uppercase tracking-widest mb-4">
                  {t('admin.documents.upload.kbLabel')}
                </label>
                {kbsError && (
                  <div className="mb-2 text-sm text-red-500 flex items-center gap-1">
                    <InfoIcon size={16} /> {t('common.errorLoadingKBs')}: {kbsError.message || String(kbsError)}
                  </div>
                )}
                <div className="relative">
                  <BooksIcon size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                  <select
                    value={selectedKb}
                    onChange={(e) => setSelectedKb(e.target.value)}
                    className="w-full pl-12 pr-10 py-3.5 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-none rounded-2xl outline-none text-gray-700 dark:text-gray-200 appearance-none cursor-pointer focus:ring-2 focus:ring-primary-500/20"
                  >
                    {kbs.length === 0 ? (
                      <option value="default" disabled>{kbsLoading ? t('common.loading') : t('admin.documents.upload.noKbFound')}</option>
                    ) : (
                      kbs.map(kb => (
                        <option key={kb.id} value={kb.id}>{kb.name}</option>
                      ))
                    )}
                  </select>
                  <CaretDownIcon size={16} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                </div>
                {/* Model Info */}
                {kbs.find(kb => kb.id === selectedKb)?.embedding_model && (
                  <div className="mt-2 text-xs text-gray-500 font-medium px-4 flex items-center gap-2 animate-fade-in">
                    <LightbulbIcon size={12} weight="fill" className="text-primary-500" />
                    {t('admin.documents.upload.usingModel', {
                      model: kbs.find(kb => kb.id === selectedKb).embedding_model
                    })}
                  </div>
                )}

                {/* Sparse Embedding Checkbox */}
                <div className="mt-4 p-4 rounded-2xl bg-indigo-50/50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800/50">
                  <div
                    className="flex items-start gap-3 cursor-pointer group"
                    onClick={() => setEnableSparse(!enableSparse)}
                  >
                    <div className={clsx(
                      "transition-colors duration-200",
                      enableSparse ? "text-indigo-600 dark:text-indigo-400" : "text-gray-400 group-hover:text-gray-500"
                    )}>
                      {enableSparse ? <CheckSquareIcon size={20} weight="fill" /> : <SquareIcon size={20} />}
                    </div>
                    <div>
                      <span className={clsx(
                        "block font-bold text-sm mb-1 transition-colors",
                        enableSparse ? "text-indigo-900 dark:text-indigo-100" : "text-gray-600 dark:text-gray-300"
                      )}>
                        {t('admin.documents.upload.sparseEmbedding.label')}
                      </span>
                      <p className="text-xs text-amber-600 dark:text-amber-400 flex items-start gap-1.5 animate-slide-up">
                        <InfoIcon size={14} className="mt-0.5 shrink-0" weight="fill" />
                        {t('admin.documents.upload.sparseEmbedding.warning')}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div id="chunk-settings">
                <label className="block text-sm font-bold text-primary-600 uppercase tracking-widest mb-4">
                  {t('admin.documents.upload.chunkingLabel')}
                </label>
                <div className="relative">
                  <ScissorsIcon size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                  <select
                    value={chunkingMethod}
                    onChange={(e) => setChunkingMethod(e.target.value)}
                    className="w-full pl-12 pr-10 py-3.5 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-none rounded-2xl outline-none text-gray-700 dark:text-gray-200 appearance-none cursor-pointer focus:ring-2 focus:ring-primary-500/20"
                  >
                    <option value="sentence">{t('admin.documents.upload.chunking.sentence')}</option>
                    <option value="semantic">{t('admin.documents.upload.chunking.semantic')}</option>
                    <option value="token">{t('admin.documents.upload.chunking.token')}</option>
                    <option value="character">{t('admin.documents.upload.chunking.character')}</option>
                    <option value="word">{t('admin.documents.upload.chunking.word')}</option>
                    <option value="recursive">{t('admin.documents.upload.chunking.recursive')}</option>
                    <option value="hierarchical">{t('admin.documents.upload.chunking.hierarchical')}</option>
                    <option value="sliding">{t('admin.documents.upload.chunking.sliding')}</option>
                  </select>
                  <CaretDownIcon size={16} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                </div>
                {renderChunkingParams()}
              </div>
            </div>

            {/* Chunking Explanation Card */}
            {['sentence', 'token', 'character', 'word', 'recursive', 'sliding', 'semantic', 'hierarchical'].includes(chunkingMethod) && (
              <div className="bg-blue-50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-800 rounded-2xl p-6 flex gap-4 animate-slide-up lg:col-span-12">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-blue-100 dark:bg-blue-800 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-300">
                    <InfoIcon size={24} weight="fill" />
                  </div>
                </div>
                <div>
                  <h4 className="text-base font-bold text-gray-800 dark:text-gray-100 mb-1">
                    {t(`admin.documents.upload.chunking.info.${chunkingMethod}.title`)}
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 leading-relaxed">
                    {t(`admin.documents.upload.chunking.info.${chunkingMethod}.desc`)}
                  </p>
                  <div className="flex items-center gap-2 text-xs font-semibold text-blue-700 dark:text-blue-400 bg-blue-100/50 dark:bg-blue-900/30 px-3 py-1.5 rounded-lg w-fit">
                    <LightbulbIcon size={16} weight="fill" />
                    <span>Best Use Case: {t(`admin.documents.upload.chunking.info.${chunkingMethod}.usage`)}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Chunking Preview */}
            <div id="preview-area" className="bg-indigo-50/60 dark:bg-indigo-900/10 rounded-3xl p-8 border border-indigo-200 dark:border-indigo-800/30 space-y-6 lg:col-span-12">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/50 rounded-xl flex items-center justify-center text-indigo-600 dark:text-indigo-400 shadow-sm">
                  <EyeIcon size={20} weight="bold" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-800 dark:text-white">{t('admin.documents.upload.preview.title')}</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">{t('admin.documents.upload.preview.subtitle')}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">{t('admin.documents.upload.preview.sampleText')}</label>
                  <textarea
                    value={previewText}
                    onChange={(e) => setPreviewText(e.target.value)}
                    rows={5}
                    className="w-full h-96 p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl text-sm outline-none focus:ring-2 focus:ring-indigo-100 dark:focus:ring-indigo-900 transition resize-none text-gray-700 dark:text-gray-300"
                    placeholder={t('admin.documents.upload.preview.samplePlaceholder')}
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">{t('admin.documents.upload.preview.resultTitle')}</label>
                  <div className="w-full h-96 overflow-auto space-y-2 pr-2">
                    {chunks.length === 0 && <p className="text-xs text-gray-300 italic">{t('admin.documents.upload.preview.enterText')}</p>}
                    {chunks.map((chunk, idx) => {
                      if (chunk.type === 'hierarchical') {
                        return (
                          <div key={idx} className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm shadow-sm animate-slide-up">
                            <span className="font-bold text-indigo-800 dark:text-indigo-400">[{t('admin.documents.upload.preview.parentNode')} - ID: {chunk.parentIdx}]</span>
                            <span className="italic text-gray-500 dark:text-gray-400">"{chunk.text}"</span>
                            <div className="mt-2 pl-4 border-l-2 border-indigo-200 dark:border-indigo-700 text-xs text-gray-600 dark:text-gray-400">
                              ↳ {t('admin.documents.upload.preview.childChunks', { count: chunk.childrenCount })}
                            </div>
                          </div>
                        )
                      }
                      return (
                        <div key={idx} className="p-3 bg-indigo-50/50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800 rounded-xl text-sm font-medium text-indigo-700 dark:text-indigo-300 leading-relaxed animate-slide-up hover:bg-white dark:hover:bg-gray-800 hover:shadow-md transition-all duration-200">
                          <div className="flex justify-between items-center mb-1">
                            <span className="inline-block bg-indigo-600 text-white text-xs px-2 py-0.5 rounded uppercase tracking-wider">Chunk {idx + 1}</span>
                            <span className="text-xs text-gray-400 font-mono">{typeof chunk === 'string' ? chunk.length : 0} chars</span>
                          </div>
                          "{chunk}"
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>
            </div>

            {/* Upload Zone */}
            <div className="lg:col-span-12">
              <label className="block text-sm font-bold text-primary-600 uppercase tracking-widest mb-4">{t('admin.documents.upload.filesLabel')}</label>
              <div
                id="drop-zone"
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                className={clsx(
                  "border-2 border-dashed border-gray-200 dark:border-gray-600 rounded-3xl p-8 flex flex-col transition-all group relative",
                  selectedFiles.length === 0
                    ? "items-center justify-center text-center cursor-pointer hover:border-primary-400 dark:hover:border-primary-500 hover:bg-gray-50 dark:hover:bg-gray-800/50 min-h-[320px]"
                    : "bg-white dark:bg-gray-800/50 min-h-[400px]"
                )}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  multiple
                  className="hidden"
                  accept=".pdf,.docx,.pptx,.txt,.md,.html,.xlsx,.jpg,.jpeg,.png,.bmp,.tiff"
                  onChange={handleFileChange}
                />

                {selectedFiles.length === 0 ? (
                  // Empty State
                  <div className="w-full h-full flex flex-col items-center justify-center" onClick={() => fileInputRef.current?.click()}>
                    <div className="w-20 h-20 bg-indigo-50 dark:bg-indigo-900/30 rounded-full flex items-center justify-center text-primary-600 dark:text-primary-400 text-4xl mb-6 group-hover:scale-110 transition-transform duration-300">
                      <CloudArrowUpIcon size={40} weight="fill" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-2">{t('admin.documents.upload.dragDrop')}</h3>
                    <p className="text-gray-400 mb-6">{t('admin.documents.upload.supportedFormats')}</p>
                    <button
                      type="button"
                      className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 px-6 py-2.5 rounded-xl font-bold text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition shadow-sm"
                    >
                      {t('admin.documents.upload.selectFromComputer')}
                    </button>
                  </div>
                ) : (
                  // File List State
                  <div className="flex flex-col h-full w-full">
                    <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-100 dark:border-gray-700">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-indigo-50 dark:bg-indigo-900/30 rounded-full flex items-center justify-center text-primary-600">
                          <CloudArrowUpIcon size={24} weight="fill" />
                        </div>
                        <div>
                          <h3 className="font-bold text-gray-800 dark:text-white">{t('admin.documents.upload.selectedFiles')} ({selectedFiles.length})</h3>
                          <p className="text-xs text-gray-400">{t('admin.documents.upload.dropMore')}</p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="text-sm font-bold text-primary-600 hover:text-primary-700 dark:hover:text-primary-400 transition"
                      >
                        + {t('admin.documents.upload.addMore')}
                      </button>
                    </div>

                    <div className="flex-1 overflow-y-auto custom-scrollbar space-y-3 pr-2 -mr-2 min-h-0">
                      {selectedFiles.map((file, idx) => (
                        <div key={`${file.name}-${idx}`} className="flex items-center justify-between bg-gray-50 dark:bg-gray-900/50 border border-gray-100 dark:border-gray-700/50 p-4 rounded-2xl animate-slide-up group/item hover:border-primary-200 dark:hover:border-primary-800 transition-colors">
                          <div className="flex items-center gap-4 min-w-0">
                            <div className="w-10 h-10 bg-white dark:bg-gray-800 rounded-xl flex items-center justify-center text-gray-400 shadow-sm">
                              <FileTextIcon size={24} className="text-indigo-500" />
                            </div>
                            <div className="min-w-0">
                              <p className="text-sm font-bold text-gray-700 dark:text-gray-200 truncate">{file.name}</p>
                              <p className="text-xs text-gray-400">{formatSize(file.size)}</p>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={(e) => { e.stopPropagation(); handleRemoveFile(file.name); }}
                            className="p-2 text-gray-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition opacity-0 group-hover/item:opacity-100"
                          >
                            <TrashIcon size={20} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Footer Actions */}
            <div className="pt-8 flex items-center justify-between border-t border-gray-50 dark:border-gray-700/50 lg:col-span-12">
              <p className={clsx("text-sm font-medium",
                msg.type === 'error' ? 'text-red-500' :
                  msg.type === 'success' ? 'text-green-500' : 'text-primary-500'
              )}>
                {msg.text}
              </p>
              <div className="flex gap-4">
                <button
                  type="button"
                  onClick={() => navigate(ROUTES.ADMIN.DOCUMENTS.LIST)}
                  className="px-8 py-3.5 text-gray-700 dark:text-gray-300 font-bold bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-2xl transition"
                >
                  {t('common.cancel')}
                </button>
                <button
                  id="start-upload-btn"
                  type="submit"
                  disabled={uploading}
                  className="bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-700 hover:to-indigo-700 px-10 py-3.5 text-white font-bold rounded-2xl shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 flex items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
                >
                  {uploading ? (
                    <>
                      <SpinnerIcon size={20} className="animate-spin" />
                      <span>{t('common.processing')}</span>
                    </>
                  ) : (
                    <>
                      <span>{t('admin.documents.upload.startProcess')}</span>
                      <PaperPlaneTiltIcon size={20} weight="bold" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};


export default UploadDocument;
