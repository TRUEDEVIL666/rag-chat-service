import React, { useState, memo, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import remarkBreaks from 'remark-breaks';
import rehypeKatex from 'rehype-katex';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { CheckIcon, CopyIcon, TerminalIcon } from '@phosphor-icons/react';

// Required for Math rendering
import 'katex/dist/katex.min.css';

/**
 * Minimal, table-safe preprocessing.
 * DO NOT touch table separator rows.
 */
const preProcessMarkdown = (content) => {
  if (!content) return '';

  let processed = content
    // 1. Normalize line endings
    .replace(/\r\n/g, '\n')

    // 2. Nuclear Option: Replace ALL non-breaking spaces with standard space
    // This fixes "Unicode Pollution" where LLMs use \u00A0 for alignment
    .replace(/\u00A0/g, ' ')

    // 3. Enforce Table Gaps (GFM Requirement)
    // If a line starts with a pipe but the previous line didn't end with a newline OR A PIPE, force double newline.
    // This fixed the "Table Explosion" bug where every row was separated.
    // Matches: (CharNotPipeOrNewline)(OptionalSpaces)\n(Spaces)(Pipe)
    .replace(/([^|\n])([ \t]*)\n(\s*\|)/g, '$1$2\n\n$3')

    // 4. Clean Header Separators
    // Ensure the separator row |---|---| contains only dashes/colons/pipes/spaces

    // 5. Fix "Glued" separator rows
    // Matches the full separator row (e.g. |---|---|) followed by the start of the next row.
    // Uses [ \t:-] instead of \s to ensure we don't accidentally match across newlines inside the separator itself.
    .replace(/((\|[ \t:-]+)+\|)\s*(\|[^\n])/g, '$1\n$3');

  // 6. Auto-close code blocks for streaming safety
  // Count backticks. If odd number of triple-backticks, append one.
  const codeBlockCount = (processed.match(/```/g) || []).length;
  if (codeBlockCount % 2 !== 0) {
    processed += '\n```';
  }

  return processed;
};

/**
 * Code block renderer with copy support
 */
const CodeBlock = memo(({ inline, className, children, ...props }) => {
  const match = /language-(\w+)/.exec(className || '');
  const language = match ? match[1] : 'text';
  const codeString = String(children).replace(/\n$/, '');
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(codeString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Copy failed', err);
    }
  };

  // Heuristic: If it's a block (inline=false) but it's "text" language, 
  // single-line, and short (< 80 chars), render it as an inline-style code snippet 
  // instead of a full terminal block. This catches things like indented math formulas.
  const isShortText =
    !inline &&
    (language === 'text' || !language) &&
    !codeString.includes('\n') &&
    codeString.length < 80;

  if (inline || isShortText) {
    return (
      <code
        className="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-gray-800 dark:text-gray-200 font-mono text-sm"
        {...props}
      >
        {children}
      </code>
    );
  }

  return (
    <div className="relative my-6 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 bg-[#1e1e1e] shadow-sm">
      <div className="flex items-center justify-between px-4 py-2 bg-[#2d2d2d] border-b border-gray-700">
        <div className="flex items-center gap-2 text-xs text-gray-400 uppercase font-bold tracking-wider">
          <TerminalIcon size={14} />
          {language}
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-colors"
        >
          {copied ? (
            <>
              <CheckIcon size={14} className="text-green-500" />
              <span className="text-green-500">Copied</span>
            </>
          ) : (
            <>
              <CopyIcon size={14} />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      <SyntaxHighlighter
        style={vscDarkPlus}
        language={language}
        PreTag="div"
        wrapLongLines
        customStyle={{
          margin: 0,
          padding: '1.25rem',
          background: 'transparent',
          fontSize: '0.875rem',
          lineHeight: '1.6',
        }}
        {...props}
      >
        {codeString}
      </SyntaxHighlighter>
    </div>
  );
});

/**
 * Main Markdown Renderer
 */
const MarkdownRenderer = ({ content }) => {
  const cleanContent = useMemo(
    () => preProcessMarkdown(content),
    [content]
  );

  return (
    <div className="markdown-body prose prose-slate dark:prose-invert max-w-none text-gray-800 dark:text-gray-100">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath, remarkBreaks]}
        rehypePlugins={[rehypeKatex]}
        components={{
          code: CodeBlock,
          pre: ({ children }) => <>{children}</>,

          // Prevent invalid nesting
          p: (props) => (
            <p className="mb-4 last:mb-0 leading-relaxed" {...props} />
          ),

          // Tables
          table: ({ children }) => (
            <div className="my-6 overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
              <table className="w-full border-collapse text-left text-sm">
                {children}
              </table>
            </div>
          ),
          thead: (props) => (
            <thead className="bg-gray-50 dark:bg-gray-800/50" {...props} />
          ),
          th: (props) => (
            <th className="px-4 py-3 font-bold border-b border-gray-200 dark:border-gray-700" {...props} />
          ),
          td: (props) => (
            <td className="px-4 py-3 border-b border-gray-100 dark:border-gray-800 align-top" {...props} />
          ),

          // Lists
          ul: (props) => (
            <ul className="list-disc pl-6 mb-4 space-y-1" {...props} />
          ),
          ol: (props) => (
            <ol className="list-decimal pl-6 mb-4 space-y-1" {...props} />
          ),
          li: (props) => <li className="mb-1" {...props} />,

          // Headings
          h1: (props) => (
            <h1 className="text-2xl font-bold mt-8 mb-4 border-b pb-2" {...props} />
          ),
          h2: (props) => (
            <h2 className="text-xl font-bold mt-6 mb-3" {...props} />
          ),

          // Blockquotes
          blockquote: (props) => (
            <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 py-1 italic text-gray-600 dark:text-gray-400 my-4" {...props} />
          ),
        }}
      >
        {cleanContent}
      </ReactMarkdown>
    </div>
  );
};

export default memo(MarkdownRenderer);
