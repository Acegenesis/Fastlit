import React from "react";
import Plot from "react-plotly.js";
import type { NodeComponentProps } from "../../registry/registry";

interface PlotlyChartProps {
  spec: {
    data: any[];
    layout?: any;
    config?: any;
  };
  useContainerWidth?: boolean;
  theme?: string;
}

export const PlotlyChart: React.FC<NodeComponentProps> = ({ props }) => {
  const {
    spec = { data: [], layout: {} },
    useContainerWidth = true,
    theme,
  } = props as PlotlyChartProps;

  // Apply Streamlit-like theme
  const themedLayout = {
    ...spec.layout,
    autosize: useContainerWidth,
    margin: spec.layout?.margin || { l: 50, r: 50, t: 50, b: 50 },
    paper_bgcolor: "transparent",
    plot_bgcolor: theme === "streamlit" ? "#fafafa" : "transparent",
    font: {
      family: "Inter, system-ui, sans-serif",
      size: 12,
      color: "#374151",
    },
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    ...spec.config,
  };

  return (
    <div style={{ width: useContainerWidth ? "100%" : undefined }}>
      <Plot
        data={spec.data}
        layout={themedLayout}
        config={config}
        style={{ width: "100%", height: "100%" }}
        useResizeHandler={useContainerWidth}
      />
    </div>
  );
};
