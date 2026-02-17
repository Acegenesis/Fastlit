import React, { useMemo } from "react";
import type { NodeComponentProps } from "../../registry/registry";
import katex from "katex";
import "katex/dist/katex.min.css";

export const Latex: React.FC<NodeComponentProps> = ({ props }) => {
  const { text, help } = props;

  const html = useMemo(() => {
    try {
      return katex.renderToString(text as string, {
        throwOnError: false,
        displayMode: true,
      });
    } catch (err) {
      console.error("KaTeX render error:", err);
      return null;
    }
  }, [text]);

  return (
    <div
      className="my-4 text-center overflow-x-auto"
      title={help || undefined}
    >
      {html ? (
        <div dangerouslySetInnerHTML={{ __html: html }} />
      ) : (
        <div className="font-mono text-lg p-4 bg-muted rounded-lg inline-block">
          <code>{text}</code>
        </div>
      )}
    </div>
  );
};
