/**
 * Shared token-based syntax highlighting utility.
 * Used by Code.tsx (st.code) and Markdown.tsx (fenced code blocks).
 */

type Token = { type: "text" | "string" | "comment" | "number" | "keyword"; value: string };

const KEYWORDS: Record<string, Set<string>> = {
  python: new Set(["def", "class", "import", "from", "return", "if", "else", "elif", "for", "while", "try", "except", "finally", "with", "as", "lambda", "yield", "raise", "pass", "break", "continue", "and", "or", "not", "in", "is", "None", "True", "False", "self"]),
  javascript: new Set(["function", "const", "let", "var", "return", "if", "else", "for", "while", "try", "catch", "finally", "class", "extends", "import", "export", "from", "default", "async", "await", "new", "this", "super", "null", "undefined", "true", "false"]),
  typescript: new Set(["function", "const", "let", "var", "return", "if", "else", "for", "while", "try", "catch", "finally", "class", "extends", "import", "export", "from", "default", "async", "await", "new", "this", "super", "null", "undefined", "true", "false", "interface", "type", "enum", "implements", "private", "public", "protected", "readonly"]),
};

const tokenize = (code: string, language: string | null): Token[] => {
  const tokens: Token[] = [];
  const lang = language?.toLowerCase() || "";
  const keywords = KEYWORDS[lang] || new Set<string>();
  let i = 0;

  while (i < code.length) {
    const remaining = code.slice(i);

    if (remaining.startsWith("#") || remaining.startsWith("//")) {
      const end = code.indexOf("\n", i);
      const value = end === -1 ? remaining : code.slice(i, end);
      tokens.push({ type: "comment", value });
      i += value.length;
      continue;
    }

    const quote = remaining[0];
    if (quote === '"' || quote === "'" || quote === "`") {
      let j = 1;
      while (j < remaining.length) {
        if (remaining[j] === "\\") j += 2;
        else if (remaining[j] === quote) { j++; break; }
        else j++;
      }
      tokens.push({ type: "string", value: remaining.slice(0, j) });
      i += j;
      continue;
    }

    const numMatch = remaining.match(/^\d+\.?\d*/);
    if (numMatch && (i === 0 || !/\w/.test(code[i - 1]))) {
      tokens.push({ type: "number", value: numMatch[0] });
      i += numMatch[0].length;
      continue;
    }

    const wordMatch = remaining.match(/^[a-zA-Z_]\w*/);
    if (wordMatch) {
      const word = wordMatch[0];
      const type = keywords.has(word) ? "keyword" : "text";
      tokens.push({ type, value: word });
      i += word.length;
      continue;
    }

    tokens.push({ type: "text", value: remaining[0] });
    i++;
  }

  return tokens;
};

export const escapeHtml = (text: string): string =>
  text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

export const highlightCode = (code: string, language: string | null): string => {
  if (!language) return escapeHtml(code);

  const tokens = tokenize(code, language);
  return tokens.map((t) => {
    const escaped = escapeHtml(t.value);
    switch (t.type) {
      case "string":  return `<span class="text-green-400">${escaped}</span>`;
      case "comment": return `<span class="text-gray-500 italic">${escaped}</span>`;
      case "number":  return `<span class="text-orange-400">${escaped}</span>`;
      case "keyword": return `<span class="text-purple-400 font-semibold">${escaped}</span>`;
      default:        return escaped;
    }
  }).join("");
};
