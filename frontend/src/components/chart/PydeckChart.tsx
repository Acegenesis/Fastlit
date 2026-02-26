import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { HtmlChartFrame } from "./HtmlChartFrame";

export const PydeckChart: React.FC<NodeComponentProps> = ({ props }) => {
  const { html, height = 500 } = props as { html?: string; height?: number };
  return (
    <HtmlChartFrame
      html={html}
      height={height}
      title="PyDeck chart"
      emptyMessage="No PyDeck chart data received."
      sandbox="allow-scripts allow-same-origin"
    />
  );
};
