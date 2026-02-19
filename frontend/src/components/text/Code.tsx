import React, { useRef, useMemo } from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { highlightCode } from "../../utils/highlight";

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
