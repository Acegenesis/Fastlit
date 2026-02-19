import React, { useMemo } from "react";
import DOMPurify from "dompurify";
import katex from "katex";
import "katex/dist/katex.min.css";
import type { NodeComponentProps } from "../../registry/registry";
import { useResolvedText } from "../../context/WidgetStore";
import { highlightCode } from "../../utils/highlight";

// Helper to render LaTeX using KaTeX
const renderLatex = (latex: string, displayMode: boolean = false): string => {
  try {
    return katex.renderToString(latex, {
      throwOnError: false,
      displayMode,
      output: "html",
    });
  } catch (err) {
    console.error("KaTeX render error:", err);
    return `<span class="text-red-500">${latex}</span>`;
  }
};

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

// Emoji shortcode mapping (common emojis)
const emojiMap: Record<string, string> = {
  // Faces
  smile: "😄", grin: "😁", joy: "😂", rofl: "🤣", smiley: "😃",
  laugh: "😆", wink: "😉", blush: "😊", heart_eyes: "😍", star_struck: "🤩",
  thinking: "🤔", neutral_face: "😐", expressionless: "😑", unamused: "😒",
  rolling_eyes: "🙄", grimacing: "😬", relieved: "😌", pensive: "😔",
  sleepy: "😪", drooling_face: "🤤", sleeping: "😴", mask: "😷",
  sunglasses: "😎", nerd_face: "🤓", confused: "😕", worried: "😟",
  frowning: "☹️", open_mouth: "😮", hushed: "😯", astonished: "😲",
  flushed: "😳", pleading_face: "🥺", crying_face: "😢", sob: "😭",
  scream: "😱", angry: "😠", rage: "😡", skull: "💀",
  // Hands
  "+1": "👍", "-1": "👎", thumbsup: "👍", thumbsdown: "👎",
  clap: "👏", wave: "👋", ok_hand: "👌", v: "✌️",
  raised_hands: "🙌", pray: "🙏", handshake: "🤝", point_up: "☝️",
  point_down: "👇", point_left: "👈", point_right: "👉", muscle: "💪",
  // Hearts
  heart: "❤️", orange_heart: "🧡", yellow_heart: "💛", green_heart: "💚",
  blue_heart: "💙", purple_heart: "💜", black_heart: "🖤", white_heart: "🤍",
  broken_heart: "💔", sparkling_heart: "💖", heartbeat: "💓", heartpulse: "💗",
  two_hearts: "💕", revolving_hearts: "💞", cupid: "💘", heart_decoration: "💟",
  // Objects
  fire: "🔥", star: "⭐", star2: "🌟", sparkles: "✨", zap: "⚡",
  boom: "💥", collision: "💥", sweat_drops: "💦", dash: "💨",
  rocket: "🚀", airplane: "✈️", car: "🚗", bike: "🚲",
  trophy: "🏆", medal: "🏅", crown: "👑", gem: "💎",
  bulb: "💡", flashlight: "🔦", wrench: "🔧", hammer: "🔨",
  gear: "⚙️", link: "🔗", lock: "🔒", unlock: "🔓",
  key: "🔑", bell: "🔔", bookmark: "🔖", tag: "🏷️",
  money_bag: "💰", dollar: "💵", credit_card: "💳", chart: "📊",
  // Nature
  sun: "☀️", moon: "🌙", cloud: "☁️", rainbow: "🌈",
  snowflake: "❄️", snowman: "⛄", umbrella: "☂️", droplet: "💧",
  ocean: "🌊", earth_americas: "🌎", earth_africa: "🌍", earth_asia: "🌏",
  // Animals
  dog: "🐕", cat: "🐈", mouse: "🐁", rabbit: "🐇",
  fox: "🦊", bear: "🐻", panda: "🐼", koala: "🐨",
  tiger: "🐯", lion: "🦁", cow: "🐄", pig: "🐷",
  frog: "🐸", monkey: "🐒", chicken: "🐔", penguin: "🐧",
  bird: "🐦", eagle: "🦅", duck: "🦆", owl: "🦉",
  butterfly: "🦋", bee: "🐝", bug: "🐛", snail: "🐌",
  snake: "🐍", turtle: "🐢", fish: "🐟", whale: "🐳",
  dolphin: "🐬", octopus: "🐙", crab: "🦀", shrimp: "🦐",
  // Food
  apple: "🍎", orange: "🍊", lemon: "🍋", banana: "🍌",
  watermelon: "🍉", grapes: "🍇", strawberry: "🍓", peach: "🍑",
  pizza: "🍕", hamburger: "🍔", fries: "🍟", hotdog: "🌭",
  taco: "🌮", burrito: "🌯", sushi: "🍣", ramen: "🍜",
  cake: "🍰", cookie: "🍪", chocolate_bar: "🍫", candy: "🍬",
  coffee: "☕", tea: "🍵", beer: "🍺", wine_glass: "🍷",
  cocktail: "🍸", champagne: "🍾", ice_cream: "🍨", doughnut: "🍩",
  // Symbols
  check: "✅", x: "❌", warning: "⚠️", no_entry: "⛔",
  question: "❓", exclamation: "❗", info: "ℹ️", stop_sign: "🛑",
  recycle: "♻️", white_check_mark: "✅", negative_squared_cross_mark: "❎",
  arrow_up: "⬆️", arrow_down: "⬇️", arrow_left: "⬅️", arrow_right: "➡️",
  // Misc
  eyes: "👀", eye: "👁️", tongue: "👅", lips: "👄",
  brain: "🧠", bone: "🦴", tooth: "🦷", ear: "👂",
  nose: "👃", foot: "🦶", hand: "✋", fist: "✊",
  calendar: "📅", clock: "🕐", hourglass: "⏳", stopwatch: "⏱️",
  phone: "📱", laptop: "💻", desktop: "🖥️", keyboard: "⌨️",
  mouse_cursor: "🖱️", printer: "🖨️", camera: "📷", video_camera: "📹",
  movie_camera: "🎥", tv: "📺", radio: "📻", microphone: "🎤",
  headphones: "🎧", musical_note: "🎵", notes: "🎶", guitar: "🎸",
  violin: "🎻", piano: "🎹", drum: "🥁", trumpet: "🎺",
  art: "🎨", paintbrush: "🖌️", crayon: "🖍️", pen: "🖊️",
  pencil: "✏️", scissors: "✂️", paperclip: "📎", pushpin: "📌",
  book: "📖", books: "📚", notebook: "📓", newspaper: "📰",
  envelope: "✉️", email: "📧", inbox: "📥", outbox: "📤",
  package: "📦", gift: "🎁", balloon: "🎈", confetti_ball: "🎊",
  tada: "🎉", party_popper: "🎉", ribbon: "🎀", medal_sports: "🏅",
  first_place_medal: "🥇", second_place_medal: "🥈", third_place_medal: "🥉",
  soccer: "⚽", basketball: "🏀", football: "🏈", baseball: "⚾",
  tennis: "🎾", volleyball: "🏐", rugby: "🏉", golf: "⛳",
  "100": "💯", new: "🆕", free: "🆓", sos: "🆘",
  vs: "🆚", ok: "🆗", cool: "🆒", top: "🔝",
};

// Color class mapping for Streamlit-style colored text
const colorClasses: Record<string, string> = {
  blue: "text-blue-600",
  green: "text-green-600",
  red: "text-red-600",
  orange: "text-orange-600",
  violet: "text-violet-600",
  gray: "text-gray-600",
  grey: "text-gray-600",
};

// Background color class mapping
const bgColorClasses: Record<string, string> = {
  blue: "bg-blue-100 text-blue-800 px-1 rounded",
  green: "bg-green-100 text-green-800 px-1 rounded",
  red: "bg-red-100 text-red-800 px-1 rounded",
  orange: "bg-orange-100 text-orange-800 px-1 rounded",
  violet: "bg-violet-100 text-violet-800 px-1 rounded",
  gray: "bg-gray-100 text-gray-800 px-1 rounded",
  grey: "bg-gray-100 text-gray-800 px-1 rounded",
};

// Basic markdown parsing for common patterns
const parseMarkdown = (text: string): string => {
  // Placeholders for raw HTML blocks extracted before any escaping
  const rawPlaceholders: string[] = [];

  // 0. Extract fenced code blocks FIRST (before HTML escaping)
  //    ```lang\ncode\n``` → dark themed pre block with syntax highlighting
  let processed0 = text.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    const placeholder = `___RAW_${rawPlaceholders.length}___`;
    const trimmed = code.replace(/\n$/, ""); // strip trailing newline
    const highlighted = highlightCode(trimmed, lang || null);
    const header = lang
      ? `<div class="flex items-center px-4 py-1.5 bg-gray-800 border-b border-gray-700">` +
        `<span class="text-xs text-gray-400 font-mono">${lang}</span></div>`
      : "";
    rawPlaceholders.push(
      `<div class="mb-3 rounded-lg overflow-hidden bg-gray-900">` +
        header +
        `<pre class="p-4 text-sm font-mono text-gray-100 overflow-x-auto whitespace-pre">${highlighted}</pre>` +
      `</div>`
    );
    return placeholder;
  });

  // Store LaTeX renders to restore after processing
  const latexPlaceholders: string[] = [];
  let processed = processed0;

  // Process block math first: $$...$$
  processed = processed.replace(/\$\$([^$]+)\$\$/g, (_, latex) => {
    const placeholder = `___LATEX_BLOCK_${latexPlaceholders.length}___`;
    latexPlaceholders.push(renderLatex(latex.trim(), true));
    return placeholder;
  });
  
  // Process inline math: $...$  (but not escaped \$)
  processed = processed.replace(/(?<!\\)\$([^$\n]+?)\$/g, (_, latex) => {
    const placeholder = `___LATEX_INLINE_${latexPlaceholders.length}___`;
    latexPlaceholders.push(renderLatex(latex.trim(), false));
    return placeholder;
  });
  
  let html = processed
    // Escape HTML entities first (if not already HTML)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  
  // Restore LaTeX renders
  html = html.replace(/___LATEX_BLOCK_(\d+)___/g, (_, idx) => {
    return `<div class="my-2 overflow-x-auto">${latexPlaceholders[parseInt(idx)]}</div>`;
  });
  html = html.replace(/___LATEX_INLINE_(\d+)___/g, (_, idx) => {
    return latexPlaceholders[parseInt(idx)];
  });
  
  // Colored background: :color-background[text]
  html = html.replace(/:(\w+)-background\[([^\]]+)\]/g, (_, color, content) => {
    const bgClass = bgColorClasses[color] || "bg-gray-100 px-1 rounded";
    return `<span class="${bgClass}">${content}</span>`;
  });
  
  // Colored text: :color[text]
  html = html.replace(/:(\w+)\[([^\]]+)\]/g, (_, color, content) => {
    const colorClass = colorClasses[color];
    if (colorClass) {
      return `<span class="${colorClass}">${content}</span>`;
    }
    // If not a known color, return as-is
    return `:${color}[${content}]`;
  });
  
  // Emoji shortcodes: :emoji_name:
  html = html.replace(/:([a-z0-9_+-]+):/gi, (match, code) => {
    const emoji = emojiMap[code.toLowerCase()];
    return emoji || match;
  });
  
  // Strikethrough: ~~text~~
  html = html.replace(/~~(.+?)~~/g, "<del>$1</del>");
  
  // Bold: **text** or __text__
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/__(.+?)__/g, "<strong>$1</strong>");
  
  // Italic: *text* or _text_
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
  html = html.replace(/_(.+?)_/g, "<em>$1</em>");
  
  // Code: `code`
  html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>');
  
  // Links: [text](url)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, url) => {
    const safeUrl = sanitizeUrl(String(url));
    if (!safeUrl) {
      return label;
    }
    return `<a href="${escapeHtmlAttr(safeUrl)}" class="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">${label}</a>`;
  });
  
  // Unordered lists: - item or * item
  html = html.replace(/^[\-\*]\s+(.+)$/gm, '<li class="ml-4">$1</li>');
  
  // Ordered lists: 1. item
  html = html.replace(/^\d+\.\s+(.+)$/gm, '<li class="ml-4 list-decimal">$1</li>');

  // Tables: must happen before \n → <br /> conversion
  // Matches: header row | separator row | data rows (with optional leading whitespace)
  html = html.replace(
    /([ \t]*\|[^\n]+\n[ \t]*\|[\s\-:|]+\n(?:[ \t]*\|[^\n]+\n?)*)/g,
    (match) => {
      const lines = match.split("\n").filter((l) => l.trim());
      if (lines.length < 2) return match;

      const parseCells = (line: string): string[] => {
        const trimmed = line.trim();
        const inner = trimmed.startsWith("|") ? trimmed.slice(1) : trimmed;
        const without = inner.endsWith("|") ? inner.slice(0, -1) : inner;
        return without.split("|").map((c) => c.trim());
      };

      const headers = parseCells(lines[0]);
      // lines[1] is the separator — skip it
      const bodyLines = lines.slice(2);

      let tableHtml =
        '<table class="border-collapse w-full my-3 text-sm">' +
        "<thead><tr>";
      for (const h of headers) {
        tableHtml += `<th class="border border-gray-300 bg-gray-50 px-3 py-1.5 text-left font-semibold text-gray-700">${h}</th>`;
      }
      tableHtml += "</tr></thead><tbody>";
      for (const row of bodyLines) {
        if (!row.trim()) continue;
        const cells = parseCells(row);
        tableHtml += '<tr class="even:bg-gray-50">';
        for (const c of cells) {
          tableHtml += `<td class="border border-gray-300 px-3 py-1.5 text-gray-700">${c}</td>`;
        }
        tableHtml += "</tr>";
      }
      tableHtml += "</tbody></table>";
      return tableHtml;
    }
  );

  // Line breaks (after table parsing so table newlines aren't converted)
  html = html.replace(/\n/g, "<br />");

  // Restore fenced code blocks (after all other processing)
  html = html.replace(/___RAW_(\d+)___/g, (_, idx) => rawPlaceholders[parseInt(idx)]);

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
  const html = useMemo(() => DOMPurify.sanitize(parseMarkdown(resolved)), [resolved]);

  return (
    <div
      className="text-gray-700 mb-2 leading-relaxed"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};
