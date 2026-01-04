import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  CheckCircleIcon,
  XCircleIcon,
  PlayIcon,
  TableIcon,
  DownloadIcon,
  ArrowLeftIcon
} from '@phosphor-icons/react';

const QuizRenderer = ({ data }) => {
  const { t } = useTranslation();
  const [mode, setMode] = useState('start'); // 'start', 'play', 'table'
  const [answers, setAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);

  // Validation: Ensure data is an array
  if (!Array.isArray(data) || data.length === 0) {
    return <div className="text-red-500 text-sm">{t('quiz.invalidData')}</div>;
  }

  // --- CSV Export Logic ---
  const handleExportCSV = () => {
    // We keep a separate "Correct Answer" column for CSV because text formatting (green color) 
    // does not persist in CSV files. This is the standard way to preserve data integrity.
    const headers = [
      t('quiz.headers.question'),
      t('quiz.headers.optionA'),
      t('quiz.headers.optionB'),
      t('quiz.headers.optionC'),
      t('quiz.headers.optionD'),
      t('quiz.headers.correctAnswer')
    ];
    const rows = data.map(q => {
      const options = q.options || [];
      // Attempt to find the index logic if needed, but here we just dump the text
      return [
        `"${q.question.replace(/"/g, '""')}"`,
        `"${(options[0] || "").replace(/"/g, '""')}"`,
        `"${(options[1] || "").replace(/"/g, '""')}"`,
        `"${(options[2] || "").replace(/"/g, '""')}"`,
        `"${(options[3] || "").replace(/"/g, '""')}"`,
        `"${q.correct_answer.replace(/"/g, '""')}"`
      ].join(",");
    });

    const csvContent = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "quiz_export.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // --- Helper: Check Answer Robustly ---
  const isAnswerCorrect = (q, index, optionText) => {
    const ans = (q.correct_answer || "").trim();
    if (!ans) return false;

    // 1. Exact Text Match
    if (ans === optionText) return true;

    // 2. Letter/Index Match
    const letter = String.fromCharCode(65 + index); // A, B...
    const upperAns = ans.toUpperCase();

    if (upperAns === letter) return true;
    if (upperAns === `OPTION ${letter}`) return true;
    if (upperAns.startsWith(`${letter})`) || upperAns.startsWith(`${letter}.`)) return true;

    return false;
  };

  // --- Helper: Reset Quiz ---
  const resetQuiz = () => {
    setMode('start');
    setAnswers({});
    setShowResults(false);
  };

  // --- Start Screen ---
  if (mode === 'start') {
    return (
      <div className="w-full max-w-md bg-white dark:bg-gray-800 rounded-xl p-6 border border-slate-200 dark:border-gray-700 shadow-sm flex flex-col gap-4">
        <h3 className="text-lg font-bold text-slate-800 dark:text-white text-center">
          {t('quiz.generated')}
        </h3>
        <p className="text-slate-500 dark:text-slate-400 text-center text-sm">
          {t('quiz.readyMessage', { count: data.length })}
        </p>
        <div className="flex gap-3 mt-2">
          <button
            onClick={() => setMode('play')}
            className="flex-1 flex flex-col items-center justify-center gap-2 p-4 rounded-xl bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800 hover:bg-indigo-100 dark:hover:bg-indigo-900/40 transition group"
          >
            <PlayIcon size={32} className="text-indigo-600 dark:text-indigo-400 group-hover:scale-110 transition-transform" weight="duotone" />
            <span className="font-semibold text-indigo-700 dark:text-indigo-300">{t('quiz.play')}</span>
          </button>
          <button
            onClick={() => setMode('table')}
            className="flex-1 flex flex-col items-center justify-center gap-2 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-gray-700 hover:bg-slate-100 dark:hover:bg-slate-700 transition group"
          >
            <TableIcon size={32} className="text-slate-600 dark:text-slate-400 group-hover:scale-110 transition-transform" weight="duotone" />
            <span className="font-semibold text-slate-700 dark:text-slate-300">{t('quiz.viewTable')}</span>
          </button>
        </div>
      </div>
    );
  }

  // --- Table Mode ---
  if (mode === 'table') {
    return (
      <div className="w-full max-w-5xl bg-white dark:bg-gray-800 rounded-xl border border-slate-200 dark:border-gray-700 shadow-sm overflow-hidden flex flex-col">
        <div className="p-4 border-b border-slate-200 dark:border-gray-700 flex items-center justify-between bg-slate-50 dark:bg-gray-900/50">
          <button
            onClick={resetQuiz}
            className="flex items-center gap-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition"
          >
            <ArrowLeftIcon /> {t('quiz.back')}
          </button>
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-2 px-3 py-1.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition shadow-sm"
          >
            <DownloadIcon weight="bold" /> {t('quiz.exportCsv')}
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead className="bg-slate-100 dark:bg-gray-900 text-slate-700 dark:text-slate-300 font-semibold border-b border-slate-200 dark:border-gray-700 whitespace-nowrap">
              <tr>
                <th className="px-4 py-3 w-12 text-center">#</th>
                <th className="px-4 py-3 min-w-[200px]">{t('quiz.headers.question')}</th>
                <th className="px-4 py-3 min-w-[150px]">{t('quiz.headers.optionA')}</th>
                <th className="px-4 py-3 min-w-[150px]">{t('quiz.headers.optionB')}</th>
                <th className="px-4 py-3 min-w-[150px]">{t('quiz.headers.optionC')}</th>
                <th className="px-4 py-3 min-w-[150px]">{t('quiz.headers.optionD')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-gray-700">
              {data.map((q, idx) => {
                const options = q.options || [];
                return (
                  <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-gray-800/50">
                    <td className="px-4 py-3 text-slate-500 text-center">{idx + 1}</td>
                    <td className="px-4 py-3 text-slate-900 dark:text-slate-100 font-medium">{q.question}</td>

                    {[0, 1, 2, 3].map(i => {
                      const optText = options[i];
                      const active = isAnswerCorrect(q, i, optText);
                      return (
                        <td
                          key={i}
                          className={`px-4 py-3 border-l border-slate-100 dark:border-gray-700 ${active
                            ? "text-green-600 dark:text-green-400 font-bold"
                            : "text-slate-600 dark:text-slate-400"
                            }`}
                        >
                          {optText || "-"}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  // --- Play Mode (Default) ---
  const handleOptionSelect = (qIndex, option) => {
    if (showResults) return;
    setAnswers(prev => ({ ...prev, [qIndex]: option }));
  };

  const calculateScore = () => {
    let correct = 0;
    data.forEach((q, idx) => {
      const selectedOption = answers[idx];
      // Find the index of the selected option
      const selectedIndex = (q.options || []).indexOf(selectedOption);
      if (selectedIndex !== -1 && isAnswerCorrect(q, selectedIndex, selectedOption)) {
        correct++;
      }
    });
    return correct;
  };

  const isSelected = (qIndex, option) => answers[qIndex] === option;

  return (
    <div className="space-y-6 w-full max-w-2xl bg-white dark:bg-gray-800 rounded-xl p-6 border border-slate-200 dark:border-gray-700 shadow-sm relative">
      <button
        onClick={resetQuiz}
        className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-full hover:bg-slate-100 dark:hover:bg-gray-700 transition"
      >
        <ArrowLeftIcon size={20} />
      </button>

      <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-4">
        {t('quiz.title')}
      </h3>

      {data.map((q, qIndex) => (
        <div key={qIndex} className="space-y-3 pb-4 border-b border-slate-100 dark:border-gray-700 last:border-0">
          <p className="font-medium text-slate-700 dark:text-slate-200">
            {qIndex + 1}. {q.question}
          </p>

          <div className="space-y-2 pl-2">
            {Array.isArray(q.options) && q.options.map((option, oIndex) => {
              const selected = isSelected(qIndex, option);
              const isCorrectAnswer = isAnswerCorrect(q, oIndex, option);

              let btnClass = "w-full text-left px-4 py-2 rounded-lg border text-sm transition-all ";

              if (showResults) {
                if (isCorrectAnswer) {
                  btnClass += "bg-green-50 border-green-200 text-green-700 dark:bg-green-900/30 dark:border-green-800 dark:text-green-300 hash-highlight-green";
                } else if (selected && !isCorrectAnswer) {
                  btnClass += "bg-red-50 border-red-200 text-red-700 dark:bg-red-900/30 dark:border-red-800 dark:text-red-300";
                } else {
                  btnClass += "bg-slate-50 border-slate-200 text-slate-400 opacity-60 dark:bg-gray-800/50 dark:border-gray-700";
                }
              } else {
                if (selected) {
                  btnClass += "bg-indigo-50 border-indigo-200 text-indigo-700 dark:bg-indigo-900/30 dark:border-indigo-800 dark:text-indigo-300";
                } else {
                  btnClass += "bg-white border-slate-200 text-slate-600 hover:bg-slate-50 dark:bg-gray-800 dark:border-gray-700 dark:text-slate-300 dark:hover:bg-gray-700";
                }
              }

              return (
                <button
                  key={oIndex}
                  onClick={() => handleOptionSelect(qIndex, option)}
                  className={btnClass}
                  disabled={showResults}
                >
                  <div className="flex items-center justify-between">
                    <span>{option}</span>
                    {showResults && isCorrectAnswer && <CheckCircleIcon className="text-green-600 text-lg" weight="fill" />}
                    {showResults && selected && !isCorrectAnswer && <XCircleIcon className="text-red-600 text-lg" weight="fill" />}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      ))}

      <div className="pt-2 flex items-center justify-between">
        {!showResults ? (
          <button
            onClick={() => setShowResults(true)}
            disabled={Object.keys(answers).length !== data.length}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition font-medium text-sm shadow-sm"
          >
            {t('quiz.checkAnswers')}
          </button>
        ) : (
          <div className="flex items-center gap-2 bg-slate-100 dark:bg-gray-700 px-4 py-2 rounded-lg">
            <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">
              {t('quiz.score', { score: calculateScore(), total: data.length })}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default QuizRenderer;
