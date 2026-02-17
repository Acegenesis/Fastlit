import React, { useRef, useMemo } from "react";
import type { NodeComponentProps } from "../../registry/registry";

// Token-based syntax highlighting to avoid breaking HTML
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

    // Comments
    if (remaining.startsWith("#") || remaining.startsWith("//")) {
      const end = code.indexOf("\n", i);
      const value = end === -1 ? remaining : code.slice(i, end);
      tokens.push({ type: "comment", value });
      i += value.length;
      continue;
    }

    // Strings
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

    // Numbers
    const numMatch = remaining.match(/^\d+\.?\d*/);
    if (numMatch && (i === 0 || !/\w/.test(code[i - 1]))) {
      tokens.push({ type: "number", value: numMatch[0] });
      i += numMatch[0].length;
      continue;
    }

    // Words (keywords or identifiers)
    const wordMatch = remaining.match(/^[a-zA-Z_]\w*/);
    if (wordMatch) {
      const word = wordMatch[0];
      const type = keywords.has(word) ? "keyword" : "text";
      tokens.push({ type, value: word });
      i += word.length;
      continue;
    }

    // Other characters
    tokens.push({ type: "text", value: remaining[0] });
    i++;
  }

  return tokens;
};

const escapeHtml = (text: string): string =>
  text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

const highlightCode = (code: string, language: string | null): string => {
  if (!language) return escapeHtml(code);

  const tokens = tokenize(code, language);
  return tokens.map((t) => {
    const escaped = escapeHtml(t.value);
    switch (t.type) {
      case "string": return `<span class="text-green-400">${escaped}</span>`;
      case "comment": return `<span class="text-gray-500 italic">${escaped}</span>`;
      case "number": return `<span class="text-orange-400">${escaped}</span>`;
      case "keyword": return `<span class="text-purple-400 font-semibold">${escaped}</span>`;
      default: return escaped;
    }
  }).join("");
};

export const Code: React.FC<NodeComponentProps> = ({ props }) => {
  const { code, language, lineNumbers, wrapLines } = props;
  const codeRef = useRef<HTMLPreElement>(null);

  const lines = useMemo(() => (code || "").split("\n"), [code]);
  const highlighted = useMemo(() => highlightCode(code || "", language), [code, language]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code || "");
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <div className="mb-3 relative group">
      {/* Language badge & copy button */}
      <div className="absolute top-2 right-2 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        {language && (
          <span className="px-2 py-0.5 text-xs bg-gray-700 text-gray-300 rounded">
            {language}
          </span>
        )}
        <button
          onClick={handleCopy}
          className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 rounded"
        >
          Copy
        </button>
      </div>

      <div className="bg-gray-900 rounded-lg overflow-hidden">
        <div className={`overflow-x-auto ${wrapLines ? "" : "overflow-x-auto"}`}>
          {lineNumbers ? (
            <table className="w-full">
              <tbody>
                {lines.map((line: string, idx: number) => (
                  <tr key={idx}>
                    <td className="py-0 px-3 text-right text-gray-500 select-none border-r border-gray-700 text-sm font-mono">
                      {idx + 1}
                    </td>
                    <td className="py-0 px-4">
                      <pre
                        className={`text-sm font-mono text-gray-100 ${
                          wrapLines ? "whitespace-pre-wrap" : "whitespace-pre"
                        }`}
                        dangerouslySetInnerHTML={{
                          __html: highlightCode(line, language) || "&nbsp;",
                        }}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <pre
              ref={codeRef}
              className={`p-4 text-sm font-mono text-gray-100 ${
                wrapLines ? "whitespace-pre-wrap" : "whitespace-pre"
              }`}
              dangerouslySetInnerHTML={{ __html: highlighted }}
            />
          )}
        </div>
      </div>
    </div>
  );
};
