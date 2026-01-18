import React, { useState, useRef } from 'react';
import Papa from 'papaparse';
import {
  XIcon,
  UploadSimpleIcon,
  CheckCircleIcon,
  WarningCircleIcon,
  SpinnerIcon,
  FileCsvIcon
} from '@phosphor-icons/react';
import { useTranslation } from 'react-i18next';
import { userService } from '../../../services/userService';
import { clsx } from 'clsx';

const BatchCreateUserDialog = ({ isOpen, onClose, onSuccess }) => {
  const { t } = useTranslation();
  const fileInputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [parsedData, setParsedData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);

  if (!isOpen) return null;

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === "text/csv" || droppedFile.name.endsWith(".csv")) {
      handleFileSelection(droppedFile);
    } else {
      setError(t('admin.users.batch.invalidFileType', "Please upload a CSV file."));
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      handleFileSelection(selectedFile);
    }
  };

  const handleFileSelection = (selectedFile) => {
    setFile(selectedFile);
    setParsedData([]);
    setError(null);
    setResult(null);
    parseFile(selectedFile);
  };

  // ... (parseFile and handleSubmit remain same, just update JSX below)

  const parseFile = (file) => {
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        if (results.errors.length > 0) {
          setError("Error parsing CSV: " + results.errors[0].message);
        } else {
          // Validate required fields
          const data = results.data;
          const valid = data.every(row => row.email && row.password && (row.name || row.full_name));
          if (!valid) {
            setError(t('admin.users.batch.invalidFormat', "Invalid CSV format. Missing required columns: email, password, name."));
          } else {
            setParsedData(data);
          }
        }
      },
      error: (err) => {
        setError("Failed to read file: " + err.message);
      }
    });
  };

  const handleSubmit = async () => {
    if (!parsedData.length) return;

    setLoading(true);
    setError(null);
    try {
      // Map CSV fields to API expected fields (cleanup keys if needed)
      const users = parsedData.map(row => ({
        email: row.email?.trim(),
        name: (row.name || row.full_name)?.trim(),
        password: row.password?.trim(),
        role: row.role?.trim() || 'user',
        tenant_id: row.tenant_id?.trim() || null
      }));

      const response = await userService.createUsersBatch(users);
      setResult(response);
      if (response.created_count > 0 && onSuccess) {
        onSuccess(false); // don't close immediately so they see result
      }
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || t('common.errorOccurred'));
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setFile(null);
    setParsedData([]);
    setResult(null);
    setError(null);
    setIsDragOver(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden animate-scale-up border border-gray-100 dark:border-gray-700">

        {/* Header */}
        <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between bg-gray-50/50 dark:bg-gray-800/50">
          <h3 className="text-lg font-bold text-gray-800 dark:text-white flex items-center gap-2">
            <UploadSimpleIcon size={24} className="text-primary-500" />
            {t('admin.users.batch.title', 'Batch Create Users')}
          </h3>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full transition text-gray-500"
          >
            <XIcon size={20} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto space-y-6">

          {/* Instructions / Template */}
          <div className="bg-blue-50 dark:bg-blue-900/10 p-4 rounded-xl border border-blue-100 dark:border-blue-800/30">
            <h4 className="font-semibold text-blue-800 dark:text-blue-300 mb-2 text-sm flex items-center gap-2">
              <FileCsvIcon size={18} /> CSV Format Required
            </h4>
            <p className="text-xs text-blue-600 dark:text-blue-400 mb-3">
              Please upload a CSV file with the following headers:
            </p>
            <div className="bg-white dark:bg-gray-900/50 rounded-lg border border-blue-200 dark:border-blue-800/30 overflow-hidden">
              <table className="w-full text-xs text-left">
                <thead className="bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 font-semibold border-b border-gray-200 dark:border-gray-700">
                  <tr>
                    <th className="px-3 py-2">email</th>
                    <th className="px-3 py-2">name</th>
                    <th className="px-3 py-2">password</th>
                    <th className="px-3 py-2">role</th>
                    <th className="px-3 py-2">tenant_id</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800 text-gray-600 dark:text-gray-300 font-mono">
                  <tr>
                    <td className="px-3 py-2">user1@example.com</td>
                    <td className="px-3 py-2">John Doe</td>
                    <td className="px-3 py-2">pass123</td>
                    <td className="px-3 py-2">user</td>
                    <td className="px-3 py-2 opacity-50"><i>(optional)</i></td>
                  </tr>
                  <tr>
                    <td className="px-3 py-2">admin@example.com</td>
                    <td className="px-3 py-2">Jane Smith</td>
                    <td className="px-3 py-2">secret</td>
                    <td className="px-3 py-2">admin</td>
                    <td className="px-3 py-2"></td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="text-xs text-blue-500 dark:text-blue-400 mt-2 italic">
              Note: <code>role</code> defaults to 'user', <code>tenant_id</code> is optional.
            </p>
          </div>

          {!result ? (
            <>
              {/* File Upload Area */}
              <div
                className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center transition cursor-pointer
                  ${isDragOver
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800/50'
                  }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  accept=".csv"
                  className="hidden"
                  onChange={handleFileChange}
                />

                {file ? (
                  <div className="flex flex-col items-center animate-fade-in">
                    <FileCsvIcon size={48} className="text-green-500 mb-3" />
                    <span className="font-semibold text-gray-800 dark:text-white">{file.name}</span>
                    <span className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</span>
                    <span className="text-xs text-primary-500 font-bold mt-2">Click to replace</span>
                  </div>
                ) : (
                  <>
                    <UploadSimpleIcon size={48} className="text-gray-400 mb-3" />
                    <span className="font-medium text-gray-600 dark:text-gray-300">Click to upload CSV</span>
                    <span className="text-xs text-gray-400 mt-1">Accepts .csv files only</span>
                  </>
                )}
              </div>

              {/* Status Messages */}
              {error && (
                <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl flex items-start gap-3 text-sm">
                  <WarningCircleIcon size={20} className="shrink-0 mt-0.5" />
                  <div>{error}</div>
                </div>
              )}

              {parsedData.length > 0 && !error && (
                <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                  <CheckCircleIcon size={18} />
                  <span>Ready to import <strong>{parsedData.length}</strong> users.</span>
                </div>
              )}
            </>
          ) : (
            /* Results View */
            <div className="space-y-4 animate-fade-in">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-xl border border-green-100 dark:border-green-800/30 text-center">
                  <div className="text-2xl font-bold text-green-600 dark:text-green-400">{result.created_count}</div>
                  <div className="text-xs text-green-800 dark:text-green-300 uppercase tracking-wide font-bold">Created</div>
                </div>
                <div className="bg-amber-50 dark:bg-amber-900/20 p-4 rounded-xl border border-amber-100 dark:border-amber-800/30 text-center">
                  <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">{result.skipped_count}</div>
                  <div className="text-xs text-amber-800 dark:text-amber-300 uppercase tracking-wide font-bold">Skipped</div>
                </div>
              </div>

              {result.errors && result.errors.length > 0 && (
                <div className="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
                  <div className="bg-gray-50 dark:bg-gray-800 px-4 py-2 border-b border-gray-200 dark:border-gray-700 text-xs font-bold text-gray-500 uppercase tracking-wider">
                    Errors / Warnings
                  </div>
                  <div className="max-h-48 overflow-y-auto p-2 bg-white dark:bg-gray-900">
                    {result.errors.map((err, idx) => (
                      <div key={idx} className="text-xs py-1 px-2 border-b border-gray-100 dark:border-gray-800 last:border-0 flex justify-between">
                        <span className="font-medium text-gray-700 dark:text-gray-300">{err.email}</span>
                        <span className="text-red-500 italic ml-2">{err.error}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-100 dark:border-gray-700/50 flex justify-end gap-3 bg-gray-50/50 dark:bg-gray-800/50">
          {!result ? (
            <>
              <button
                onClick={handleClose}
                className="px-4 py-2 text-gray-500 dark:text-gray-400 font-bold hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={handleSubmit}
                disabled={loading || !parsedData.length || !!error}
                className="bg-primary-600 hover:bg-primary-700 text-white font-bold rounded-lg px-6 py-2 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {loading && <SpinnerIcon size={18} className="animate-spin" />}
                Import Users
              </button>
            </>
          ) : (
            <button
              onClick={() => { onSuccess(true); handleClose(); }}
              className="bg-primary-600 hover:bg-primary-700 text-white font-bold rounded-lg px-6 py-2 transition"
            >
              Done
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default BatchCreateUserDialog;
