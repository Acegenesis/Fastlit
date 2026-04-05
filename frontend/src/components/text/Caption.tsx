import React, { useEffect, useMemo, useState } from "react";
import MarkdownIt from "markdown-it";
import type { NodeComponentProps } from "../../registry/registry";
import { useResolvedPropText, useResolvedText } from "../../context/WidgetStore";
import { loadKatex } from "../../utils/katexLoader";
import { sanitizeHtml } from "../../utils/sanitize";

// Simple check if text contains HTML tags
const containsHtml = (text: string): boolean => {
  return /<[a-z][\s\S]*>/i.test(text);
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

// Create a configured markdown-it instance for captions (inline rendering)
const md = new MarkdownIt({
  html: false, // Disable raw HTML input for security
  linkify: true,
  typographer: false,
  breaks: false,
});

// Override link rendering to add security attributes
const defaultLinkOpen =
  md.renderer.rules.link_open ||
  function (tokens: any, idx: number, options: any, _env: any, self: any) {
    return self.renderToken(tokens, idx, options);
  };

md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
  const token = tokens[idx];
  const hrefIdx = token.attrIndex("href");
  if (hrefIdx >= 0) {
    const href = token.attrs![hrefIdx][1];
    const trimmed = href.trim();
    if (trimmed && !trimmed.startsWith("/") && !trimmed.startsWith("#") && !trimmed.startsWith("?")) {
      try {
        const parsed = new URL(trimmed, window.location.origin);
        const protocol = parsed.protocol.toLowerCase();
        if (protocol !== "http:" && protocol !== "https:" && protocol !== "mailto:" && protocol !== "tel:") {
          token.attrs![hrefIdx][1] = "";
        }
      } catch {
        token.attrs![hrefIdx][1] = "";
      }
    }
  }
  token.attrSet("target", "_blank");
  token.attrSet("rel", "noopener noreferrer");
  token.attrSet("class", "text-blue-600 hover:underline");
  return defaultLinkOpen(tokens, idx, options, env, self);
};

// Apply Streamlit-specific extensions
function applyStreamlitExtensions(text: string): string {
  let result = text;

  // Colored background: :color-background[text]
  result = result.replace(/:(\w+)-background\[([^\]]+)\]/g, (_, color, content) => {
    const bgClass = bgColorClasses[color] || "bg-gray-100 px-1 rounded";
    return `<span class="${bgClass}">${md.utils.escapeHtml(content)}</span>`;
  });

  // Colored text: :color[text]
  result = result.replace(/:(\w+)\[([^\]]+)\]/g, (_, color, content) => {
    const colorClass = colorClasses[color];
    return colorClass ? `<span class="${colorClass}">${md.utils.escapeHtml(content)}</span>` : `:${color}[${content}]`;
  });

  // Emoji shortcodes
  result = result.replace(/:([a-z0-9_+-]+):/gi, (match, code) => emojiMap[code.toLowerCase()] || match);

  return result;
}

// Parse markdown for captions
const parseMarkdown = (
  text: string,
  renderLatex?: ((latex: string, displayMode?: boolean) => string) | null
): string => {
  const latexPlaceholders: string[] = [];

  // Extract LaTeX first
  let processed = text.replace(/\$\$([^$]+)\$\$/g, (_, latex) => {
    if (!renderLatex) return `$$${latex}$$`;
    const placeholder = `FASTLIT_LATEX_BLOCK_${latexPlaceholders.length}`;
    latexPlaceholders.push(renderLatex(latex.trim(), true));
    return placeholder;
  });
  processed = processed.replace(/(?<!\\)\$([^$\n]+?)\$/g, (_, latex) => {
    if (!renderLatex) return `$${latex}$`;
    const placeholder = `FASTLIT_LATEX_INLINE_${latexPlaceholders.length}`;
    latexPlaceholders.push(renderLatex(latex.trim(), false));
    return placeholder;
  });

  // Apply Streamlit extensions
  processed = applyStreamlitExtensions(processed);

  // Use renderInline for captions (no wrapping <p> tags)
  let html = md.renderInline(processed);

  // Restore LaTeX
  html = html.replace(/FASTLIT_LATEX_BLOCK_(\d+)/g, (_, idx) => latexPlaceholders[parseInt(idx)]);
  html = html.replace(/FASTLIT_LATEX_INLINE_(\d+)/g, (_, idx) => latexPlaceholders[parseInt(idx)]);

  return html;
};

export const Caption: React.FC<NodeComponentProps> = ({ props }) => {
  const resolved = useResolvedText(props.text, props._tpl, props._refs, props._exprs);
  const help = useResolvedPropText(props, "help");
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
      return sanitizeHtml(resolved);
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
            return `<span class="text-red-500">${md.utils.escapeHtml(latex)}</span>`;
          }
        }
      : null;

    return sanitizeHtml(parseMarkdown(resolved, latexRenderer));
  }, [hasHtml, resolved, shouldParseCaption, katexModule]);

  // Fast path for plain text captions.
  if (!hasHtml && !shouldParseCaption) {
    return (
      <p className="text-sm text-gray-500 mb-2 whitespace-pre-wrap break-words" title={help || undefined}>
        {resolved}
      </p>
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
