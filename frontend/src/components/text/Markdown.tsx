import React, { useEffect, useMemo, useState } from "react";
import MarkdownIt from "markdown-it";
import type { NodeComponentProps } from "../../registry/registry";
import { useResolvedText } from "../../context/WidgetStore";
import { highlightCode } from "../../utils/highlight";
import { loadKatex } from "../../utils/katexLoader";
import { sanitizeHtml } from "../../utils/sanitize";

// Simple check if text contains HTML tags
const containsHtml = (text: string): boolean => {
  return /<[a-z][\s\S]*>/i.test(text);
};

const LATEX_HINTS = /\$\$[^$]+\$\$|(?<!\\)\$[^$\n]+?\$/;

const RICH_MARKDOWN_HINTS =
  /```|`|\$\$|(?<!\\)\$|:\w+(?:-background)?\[|:[a-z0-9_+-]+:|\[[^\]]+\]\([^)]+\)|^\s*[-*]\s+|^\s*\d+\.\s+|([ \t]*\|[^\n]+\n[ \t]*\|[\s\-:|]+)/m;

const needsRichMarkdownParsing = (text: string): boolean => {
  if (RICH_MARKDOWN_HINTS.test(text)) return true;
  return (
    text.includes("~~") ||
    text.includes("**") ||
    text.includes("__") ||
    text.includes("*") ||
    text.includes("_")
  );
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

// Escape utility that works before md is initialized
const escapeForAttr = (s: string): string =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

// Create a configured markdown-it instance
const md: MarkdownIt = new MarkdownIt({
  html: false, // Disable raw HTML input for security
  linkify: true,
  typographer: false,
  breaks: true,
  highlight: (str: string, lang: string): string => {
    const trimmed = str.replace(/\n$/, "");
    const highlighted = highlightCode(trimmed, lang || null);
    const header: string = lang
      ? `<div class="flex items-center px-4 py-1.5 bg-gray-800 border-b border-gray-700">` +
        `<span class="text-xs text-gray-400 font-mono">${escapeForAttr(lang)}</span></div>`
      : "";
    return (
      `<div class="mb-3 rounded-lg overflow-hidden bg-gray-900">` +
      header +
      `<pre class="p-4 text-sm font-mono text-gray-100 overflow-x-auto whitespace-pre"><code>${highlighted}</code></pre>` +
      `</div>`
    );
  },
});

// Override link rendering to add security attributes and URL sanitization
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const defaultLinkOpen: any =
  md.renderer.rules.link_open ||
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  function (tokens: any[], idx: number, options: any, _env: any, self: any) {
    return self.renderToken(tokens, idx, options);
  };

// eslint-disable-next-line @typescript-eslint/no-explicit-any
md.renderer.rules.link_open = function (tokens: any[], idx: number, options: any, _env: any, self: any) {
  const token = tokens[idx];
  const hrefIdx = token.attrIndex("href");
  if (hrefIdx >= 0) {
    const href = token.attrs![hrefIdx][1];
    // Validate URL protocol
    const trimmed = href.trim();
    if (trimmed && !trimmed.startsWith("/") && !trimmed.startsWith("#") && !trimmed.startsWith("?")) {
      try {
        const parsed = new URL(trimmed, window.location.origin);
        const protocol = parsed.protocol.toLowerCase();
        if (protocol !== "http:" && protocol !== "https:" && protocol !== "mailto:" && protocol !== "tel:") {
          // Unsafe protocol — remove href
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
  return defaultLinkOpen(tokens, idx, options, _env, self);
};

// Apply Streamlit-specific extensions as a pre-processing step
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
    if (colorClass) {
      return `<span class="${colorClass}">${md.utils.escapeHtml(content)}</span>`;
    }
    return `:${color}[${content}]`;
  });

  // Emoji shortcodes: :emoji_name:
  result = result.replace(/:([a-z0-9_+-]+):/gi, (match, code) => {
    const emoji = emojiMap[code.toLowerCase()];
    return emoji || match;
  });

  return result;
}

// Parse markdown using markdown-it with LaTeX support
const parseMarkdown = (
  text: string,
  renderLatex?: ((latex: string, displayMode?: boolean) => string) | null
): string => {
  const latexPlaceholders: string[] = [];
  let processed = text;

  // Extract LaTeX before markdown-it processes it
  // Block math: $$...$$
  processed = processed.replace(/\$\$([^$]+)\$\$/g, (_, latex) => {
    if (!renderLatex) return `$$${latex}$$`;
    const placeholder = `FASTLIT_LATEX_BLOCK_${latexPlaceholders.length}`;
    latexPlaceholders.push(renderLatex(latex.trim(), true));
    return placeholder;
  });

  // Inline math: $...$ (but not escaped \$)
  processed = processed.replace(/(?<!\\)\$([^$\n]+?)\$/g, (_, latex) => {
    if (!renderLatex) return `$${latex}$`;
    const placeholder = `FASTLIT_LATEX_INLINE_${latexPlaceholders.length}`;
    latexPlaceholders.push(renderLatex(latex.trim(), false));
    return placeholder;
  });

  // Apply Streamlit extensions (colors, emojis) before markdown-it
  processed = applyStreamlitExtensions(processed);

  // Render with markdown-it (safe by default — html: false)
  let html = md.render(processed);

  // Restore LaTeX renders
  html = html.replace(/FASTLIT_LATEX_BLOCK_(\d+)/g, (_, idx) => {
    return `<div class="my-2 overflow-x-auto">${latexPlaceholders[parseInt(idx)]}</div>`;
  });
  html = html.replace(/FASTLIT_LATEX_INLINE_(\d+)/g, (_, idx) => {
    return latexPlaceholders[parseInt(idx)];
  });

  return html;
};

export const Markdown: React.FC<NodeComponentProps> = ({ props }) => {
  const resolved = useResolvedText(props.text, props._tpl, props._refs, props._exprs);
  const isStreaming = Boolean(props.isStreaming);
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

  const shouldParseMarkdown = useMemo(
    () => !hasHtml && needsRichMarkdownParsing(resolved),
    [hasHtml, resolved]
  );

  // Blinking cursor appended during active streaming.
  const cursor = isStreaming ? (
    <span
      className="inline-block w-0.5 h-4 bg-current align-middle ml-0.5 animate-pulse"
      aria-hidden="true"
    />
  ) : null;

  const html = useMemo(() => {
    if (hasHtml) {
      return sanitizeHtml(resolved);
    }
    if (!shouldParseMarkdown) {
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
          } catch (err) {
            console.error("KaTeX render error:", err);
            return `<span class="text-red-500">${md.utils.escapeHtml(latex)}</span>`;
          }
        }
      : null;

    // markdown-it output is safe (html: false), but we still sanitize as defense-in-depth
    return sanitizeHtml(parseMarkdown(resolved, latexRenderer));
  }, [hasHtml, resolved, shouldParseMarkdown, katexModule]);

  // Fast path for plain text avoids expensive markdown regex + sanitization.
  if (!hasHtml && !shouldParseMarkdown) {
    return (
      <div className="text-gray-700 mb-2 leading-relaxed whitespace-pre-wrap break-words">
        {resolved}
        {cursor}
      </div>
    );
  }

  // If the content contains HTML tags, sanitize and render
  if (hasHtml) {
    return (
      <div className="text-gray-700 mb-2 leading-relaxed prose prose-sm max-w-none">
        <span dangerouslySetInnerHTML={{ __html: html }} />
        {cursor}
      </div>
    );
  }

  return (
    <div className="text-gray-700 mb-2 leading-relaxed">
      <span dangerouslySetInnerHTML={{ __html: html }} />
      {cursor}
    </div>
  );
};
