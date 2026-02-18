import React, { useEffect, useRef } from "react";
import type { NodeComponentProps } from "../../registry/registry";

export const BokehChart: React.FC<NodeComponentProps> = ({ props }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { data, height = 400 } = props;

  useEffect(() => {
    if (!containerRef.current || !data) return;

    // Attempt to render using Bokeh if it's loaded globally
    const Bokeh = (window as any).Bokeh;
    if (Bokeh && data?.doc) {
      containerRef.current.innerHTML = "";
      try {
        Bokeh.embed.embed_item(data, containerRef.current);
        return;
      } catch {
        // Fall through to JSON display
      }
    }

    // Fallback: show JSON representation
    containerRef.current.innerHTML = `<pre style="overflow:auto;max-height:${height}px;font-size:12px;background:#f6f8fa;padding:1em;border-radius:6px;">${JSON.stringify(data, null, 2)}</pre>`;
  }, [data, height]);

  return (
    <div
      className="mb-4 rounded-lg border overflow-hidden"
      style={{ minHeight: height }}
      ref={containerRef}
    />
  );
};
