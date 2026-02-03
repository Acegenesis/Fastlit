import React, { useEffect, useState } from "react";
import type { NodeComponentProps } from "../../registry/registry";

interface GraphvizChartProps {
  dot: string;
  useContainerWidth?: boolean;
}

export const GraphvizChart: React.FC<NodeComponentProps> = ({ props }) => {
  const { dot, useContainerWidth = true } = props as GraphvizChartProps;
  const [svg, setSvg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!dot) return;

    // Dynamically import and render
    const renderGraph = async () => {
      try {
        const hpccWasm = await import("@hpcc-js/wasm");
        const graphviz = await hpccWasm.Graphviz.load();
        const result = graphviz.dot(dot);
        setSvg(result);
        setError(null);
      } catch (err) {
        console.error("Graphviz render error:", err);
        setError(err instanceof Error ? err.message : "Failed to render graph");
        setSvg(null);
      }
    };

    renderGraph();
  }, [dot]);

  if (!dot) {
    return (
      <div className="text-gray-400 text-sm italic p-4 border border-gray-200 rounded">
        No graph to display
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-500 text-sm p-4 border border-red-200 rounded bg-red-50">
        Error rendering graph: {error}
      </div>
    );
  }

  if (!svg) {
    return (
      <div className="text-gray-400 text-sm p-4 border border-gray-200 rounded">
        Rendering graph...
      </div>
    );
  }

  return (
    <div
      className={`${useContainerWidth ? "w-full" : "inline-block"} overflow-auto`}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
};
