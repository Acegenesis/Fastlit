import React, { useRef, useCallback } from "react";
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
  selectable?: boolean;
}

export const PlotlyChart: React.FC<NodeComponentProps> = ({ nodeId, props, sendEvent }) => {
  const {
    spec = { data: [], layout: {} },
    useContainerWidth = true,
    theme,
    selectable = false,
  } = props as PlotlyChartProps;

  // D1: Preserve zoom/pan between reruns by storing the relayout state
  const viewportRef = useRef<Record<string, any>>({});

  const handleRelayout = useCallback((eventData: any) => {
    // Merge new viewport state (zoom, pan, range axes) into our store
    viewportRef.current = { ...viewportRef.current, ...eventData };
  }, []);

  // D2: Cross-filtering — send selected point indices to Python
  const handleSelected = useCallback(
    (eventData: any) => {
      if (!selectable || !eventData?.points) return;
      const indices = eventData.points.map((p: any) => p.pointIndex ?? p.pointNumber);
      sendEvent(nodeId, indices);
    },
    [selectable, nodeId, sendEvent]
  );

  // D1: Merge stored viewport into layout so Plotly restores zoom on rerender
  const themedLayout = {
    ...spec.layout,
    ...viewportRef.current,  // restore zoom/pan
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
        onRelayout={handleRelayout}
        onSelected={selectable ? handleSelected : undefined}
      />
    </div>
  );
};
