import React, { useMemo } from "react";
import DOMPurify from "dompurify";
import type { NodeComponentProps } from "../../registry/registry";
import { useResolvedText } from "../../context/WidgetStore";

// Simple check if text contains HTML tags
const containsHtml = (text: string): boolean => {
  return /<[a-z][\s\S]*>/i.test(text);
};

// Basic markdown parsing for common patterns
const parseMarkdown = (text: string): string => {
  let html = text
    // Escape HTML entities first (if not already HTML)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    // Bold: **text** or __text__
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/__(.+?)__/g, "<strong>$1</strong>")
    // Italic: *text* or _text_
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/_(.+?)_/g, "<em>$1</em>")
    // Code: `code`
    .replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>')
    // Links: [text](url)
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">$1</a>')
    // Line breaks
    .replace(/\n/g, "<br />");

  return html;
};

export const Markdown: React.FC<NodeComponentProps> = ({ props }) => {
  const resolved = useResolvedText(props.text, props._tpl, props._refs);

  // If the content contains HTML tags, sanitize and render
  if (containsHtml(resolved)) {
    const sanitized = DOMPurify.sanitize(resolved);
    return (
      <div
        className="text-gray-700 mb-2 leading-relaxed prose prose-sm max-w-none"
        dangerouslySetInnerHTML={{ __html: sanitized }}
      />
    );
  }

  // Otherwise, parse simple markdown (memoized to avoid regex on every render)
  const html = useMemo(() => parseMarkdown(resolved), [resolved]);

  return (
    <div
      className="text-gray-700 mb-2 leading-relaxed"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};
