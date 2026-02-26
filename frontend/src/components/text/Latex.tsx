import React, { useEffect, useMemo, useState } from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { loadKatex } from "../../utils/katexLoader";

export const Latex: React.FC<NodeComponentProps> = ({ props }) => {
  const { text, help } = props;
  const [katexModule, setKatexModule] = useState<Awaited<ReturnType<typeof loadKatex>> | null>(
    null
  );

  useEffect(() => {
    let cancelled = false;
    loadKatex()
      .then((mod) => {
        if (!cancelled) setKatexModule(mod);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  const html = useMemo(() => {
    if (!katexModule) return null;
    try {
      return katexModule.renderToString(text as string, {
        throwOnError: false,
        displayMode: true,
      });
    } catch (err) {
      console.error("KaTeX render error:", err);
      return null;
    }
  }, [katexModule, text]);

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
