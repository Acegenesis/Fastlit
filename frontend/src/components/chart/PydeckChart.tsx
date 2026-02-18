import React, { useEffect, useRef } from "react";
import type { NodeComponentProps } from "../../registry/registry";

export const PydeckChart: React.FC<NodeComponentProps> = ({ props }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { data, height = 500 } = props;

  useEffect(() => {
    if (!containerRef.current || !data) return;

    // Attempt to render using deck.gl if loaded globally
    const deck = (window as any).deck;
    if (deck && data) {
      try {
        // deck.gl JSON API
        const deckInstance = new deck.DeckGL({
          container: containerRef.current,
          ...data,
        });
        return () => {
          deckInstance.finalize();
        };
      } catch {
        // Fall through to JSON display
      }
    }

    // Fallback: display JSON spec
    if (containerRef.current) {
      containerRef.current.innerHTML = `<pre style="overflow:auto;max-height:${height}px;font-size:12px;background:#f6f8fa;padding:1em;border-radius:6px;">${JSON.stringify(data, null, 2)}</pre>`;
    }
  }, [data, height]);

  return (
    <div
      className="mb-4 rounded-lg border overflow-hidden"
      style={{ height }}
      ref={containerRef}
    />
  );
};
