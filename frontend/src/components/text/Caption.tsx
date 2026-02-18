import React, { useMemo } from "react";
import DOMPurify from "dompurify";
import katex from "katex";
import "katex/dist/katex.min.css";
import type { NodeComponentProps } from "../../registry/registry";
import { useResolvedText } from "../../context/WidgetStore";

// Simple check if text contains HTML tags
const containsHtml = (text: string): boolean => {
  return /<[a-z][\s\S]*>/i.test(text);
};

// Emoji shortcode mapping (common emojis)
const emojiMap: Record<string, string> = {
  "+1": "👍", "-1": "👎", thumbsup: "👍", thumbsdown: "👎",
  heart: "❤️", fire: "🔥", star: "⭐", rocket: "🚀",
  check: "✅", x: "❌", warning: "⚠️", info: "ℹ️",
  smile: "😄", wink: "😉", sunglasses: "😎",
};

// Color class mapping
const colorClasses: Record<string, string> = {
  blue: "text-blue-600", green: "text-green-600", red: "text-red-600",
  orange: "text-orange-600", violet: "text-violet-600", gray: "text-gray-600",
};

// Background color class mapping
const bgColorClasses: Record<string, string> = {
  blue: "bg-blue-100 text-blue-800 px-1 rounded",
  green: "bg-green-100 text-green-800 px-1 rounded",
  red: "bg-red-100 text-red-800 px-1 rounded",
  orange: "bg-orange-100 text-orange-800 px-1 rounded",
  violet: "bg-violet-100 text-violet-800 px-1 rounded",
  gray: "bg-gray-100 text-gray-800 px-1 rounded",
};

// Helper to render LaTeX
const renderLatex = (latex: string, displayMode: boolean = false): string => {
  try {
    return katex.renderToString(latex, { throwOnError: false, displayMode, output: "html" });
  } catch {
    return `<span class="text-red-500">${latex}</span>`;
  }
};

// Parse markdown
const parseMarkdown = (text: string): string => {
  const latexPlaceholders: string[] = [];
  
  // Process LaTeX first
  let processed = text.replace(/\$\$([^$]+)\$\$/g, (_, latex) => {
    const placeholder = `___LATEX_BLOCK_${latexPlaceholders.length}___`;
    latexPlaceholders.push(renderLatex(latex.trim(), true));
    return placeholder;
  });
  processed = processed.replace(/(?<!\\)\$([^$\n]+?)\$/g, (_, latex) => {
    const placeholder = `___LATEX_INLINE_${latexPlaceholders.length}___`;
    latexPlaceholders.push(renderLatex(latex.trim(), false));
    return placeholder;
  });
  
  let html = processed
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  
  // Restore LaTeX
  html = html.replace(/___LATEX_BLOCK_(\d+)___/g, (_, idx) => latexPlaceholders[parseInt(idx)]);
  html = html.replace(/___LATEX_INLINE_(\d+)___/g, (_, idx) => latexPlaceholders[parseInt(idx)]);
  
  // Colored background: :color-background[text]
  html = html.replace(/:(\w+)-background\[([^\]]+)\]/g, (_, color, content) => {
    const bgClass = bgColorClasses[color] || "bg-gray-100 px-1 rounded";
    return `<span class="${bgClass}">${content}</span>`;
  });
  
  // Colored text: :color[text]
  html = html.replace(/:(\w+)\[([^\]]+)\]/g, (_, color, content) => {
    const colorClass = colorClasses[color];
    return colorClass ? `<span class="${colorClass}">${content}</span>` : `:${color}[${content}]`;
  });
  
  // Emoji shortcodes
  html = html.replace(/:([a-z0-9_+-]+):/gi, (match, code) => emojiMap[code.toLowerCase()] || match);
  
  // Markdown formatting
  html = html.replace(/~~(.+?)~~/g, "<del>$1</del>");
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/__(.+?)__/g, "<strong>$1</strong>");
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
  html = html.replace(/_(.+?)_/g, "<em>$1</em>");
  html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono">$1</code>');
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">$1</a>');

  return html;
};

export const Caption: React.FC<NodeComponentProps> = ({ props }) => {
  const resolved = useResolvedText(props.text, props._tpl, props._refs);
  const help = props.help;

  // If contains HTML, sanitize and render
  if (containsHtml(resolved)) {
    const sanitized = DOMPurify.sanitize(resolved);
    return (
      <p
        className="text-sm text-gray-500 mb-2"
        title={help || undefined}
        dangerouslySetInnerHTML={{ __html: sanitized }}
      />
    );
  }

  // Parse markdown
  const html = useMemo(() => parseMarkdown(resolved), [resolved]);

  return (
    <p
      className="text-sm text-gray-500 mb-2"
      title={help || undefined}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};
