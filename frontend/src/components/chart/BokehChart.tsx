import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { HtmlChartFrame } from "./HtmlChartFrame";

export const BokehChart: React.FC<NodeComponentProps> = ({ props }) => {
  const { html, height = 450 } = props as { html?: string; height?: number };
  return (
    <HtmlChartFrame
      html={html}
      height={height}
      title="Bokeh chart"
      emptyMessage="No Bokeh chart data received."
    />
  );
};
