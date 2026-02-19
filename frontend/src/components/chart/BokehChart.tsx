import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

export const BokehChart: React.FC<NodeComponentProps> = ({ props }) => {
  const { html, height = 450 } = props;

  if (!html) {
    return (
      <div className="mb-4 p-4 text-sm text-gray-500 bg-gray-50 rounded-lg border">
        No Bokeh chart data received.
      </div>
    );
  }

  return (
    <div className="mb-4 w-full rounded-lg overflow-hidden border border-gray-200">
      <iframe
        srcDoc={html}
        style={{ width: "100%", height, border: "none", display: "block" }}
        sandbox="allow-scripts allow-same-origin"
        title="Bokeh chart"
      />
    </div>
  );
};
