import React, { useEffect, useRef } from "react";
import embed from "vega-embed";
import type { NodeComponentProps } from "../../registry/registry";

interface VegaLiteChartProps {
  spec: any;
  useContainerWidth?: boolean;
  theme?: string;
}

export const VegaLiteChart: React.FC<NodeComponentProps> = ({ props }) => {
  const { spec = {}, useContainerWidth = true } = props as VegaLiteChartProps;
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !spec) return;

    // Add default width/height if not specified
    const fullSpec = {
      ...spec,
      width: useContainerWidth ? "container" : spec.width || 400,
      height: spec.height || 300,
    };

    embed(containerRef.current, fullSpec, {
      actions: {
        export: true,
        source: false,
        compiled: false,
        editor: false,
      },
    }).catch((err) => {
      console.error("Vega-Lite embed error:", err);
    });

    // Cleanup
    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = "";
      }
    };
  }, [spec, useContainerWidth]);

  if (!spec || Object.keys(spec).length === 0) {
    return (
      <div className="text-gray-400 text-sm italic p-4 border border-gray-200 rounded">
        No chart specification provided
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={useContainerWidth ? "w-full" : "inline-block"}
    />
  );
};
