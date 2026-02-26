import React, { useEffect, useMemo, useState } from "react";
import DOMPurify from "dompurify";
import type { NodeComponentProps } from "../../registry/registry";
import { useResolvedText } from "../../context/WidgetStore";
import { loadKatex } from "../../utils/katexLoader";

// Simple check if text contains HTML tags
const containsHtml = (text: string): boolean => {
  return /<[a-z][\s\S]*>/i.test(text);
};

const escapeHtmlAttr = (value: string): string =>
  value
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

const sanitizeUrl = (url: string): string | null => {
  const trimmed = url.trim();
  if (!trimmed) return null;
  if (trimmed.startsWith("/") || trimmed.startsWith("#") || trimmed.startsWith("?")) {
    return trimmed;
  }
  try {
    const parsed = new URL(trimmed, window.location.origin);
    const protocol = parsed.protocol.toLowerCase();
    if (protocol === "http:" || protocol === "https:" || protocol === "mailto:" || protocol === "tel:") {
      return parsed.href;
    }
  } catch {
    return null;
  }
  return null;
};

const RICH_CAPTION_HINTS =
  /`|\$\$|(?<!\\)\$|:\w+(?:-background)?\[|:[a-z0-9_+-]+:|\[[^\]]+\]\([^)]+\)|~~|\*\*|__|\*|_/;
const LATEX_HINTS = /\$\$[^$]+\$\$|(?<!\\)\$[^$\n]+?\$/;

const needsRichCaptionParsing = (text: string): boolean => RICH_CAPTION_HINTS.test(text);

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

// Parse markdown
const parseMarkdown = (
  text: string,
  renderLatex?: ((latex: string, displayMode?: boolean) => string) | null
): string => {
  const latexPlaceholders: string[] = [];
  
  // Process LaTeX first
  let processed = text.replace(/\$\$([^$]+)\$\$/g, (_, latex) => {
    if (!renderLatex) return `$$${latex}$$`;
    const placeholder = `___LATEX_BLOCK_${latexPlaceholders.length}___`;
    latexPlaceholders.push(renderLatex(latex.trim(), true));
    return placeholder;
  });
  processed = processed.replace(/(?<!\\)\$([^$\n]+?)\$/g, (_, latex) => {
    if (!renderLatex) return `$${latex}$`;
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
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, url) => {
    const safeUrl = sanitizeUrl(String(url));
    if (!safeUrl) {
      return label;
    }
    return `<a href="${escapeHtmlAttr(safeUrl)}" class="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">${label}</a>`;
  });

  return html;
};

export const Caption: React.FC<NodeComponentProps> = ({ props }) => {
  const resolved = useResolvedText(props.text, props._tpl, props._refs);
  const help = props.help;
  const hasHtml = useMemo(() => containsHtml(resolved), [resolved]);
  const needsKatex = useMemo(
    () => !hasHtml && LATEX_HINTS.test(resolved),
    [hasHtml, resolved]
  );
  const [katexModule, setKatexModule] = useState<Awaited<ReturnType<typeof loadKatex>> | null>(
    null
  );

  useEffect(() => {
    if (!needsKatex || katexModule) return;
    let cancelled = false;
    loadKatex()
      .then((mod) => {
        if (!cancelled) setKatexModule(mod);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [needsKatex, katexModule]);

  const shouldParseCaption = useMemo(
    () => !hasHtml && needsRichCaptionParsing(resolved),
    [hasHtml, resolved]
  );

  const html = useMemo(() => {
    if (hasHtml) {
      return DOMPurify.sanitize(resolved);
    }
    if (!shouldParseCaption) {
      return "";
    }

    const latexRenderer = katexModule
      ? (latex: string, displayMode: boolean = false) => {
          try {
            return katexModule.renderToString(latex, {
              throwOnError: false,
              displayMode,
              output: "html",
            });
          } catch {
            return `<span class="text-red-500">${latex}</span>`;
          }
        }
      : null;

    return DOMPurify.sanitize(parseMarkdown(resolved, latexRenderer));
  }, [hasHtml, resolved, shouldParseCaption, katexModule]);

  // Fast path for plain text captions.
  if (!hasHtml && !shouldParseCaption) {
    return (
      <p className="text-sm text-gray-500 mb-2 whitespace-pre-wrap break-words" title={help || undefined}>
        {resolved}
      </p>
    );
  }

  // If contains HTML, sanitize and render
  if (hasHtml) {
    return (
      <p
        className="text-sm text-gray-500 mb-2"
        title={help || undefined}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    );
  }

  return (
    <p
      className="text-sm text-gray-500 mb-2"
      title={help || undefined}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};
