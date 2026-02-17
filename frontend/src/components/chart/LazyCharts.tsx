import React, { Suspense } from "react";
import type { NodeComponentProps } from "../../registry/registry";

// Loading spinner for chart components
const ChartLoading: React.FC = () => (
  <div className="flex items-center justify-center h-64 bg-muted/20 rounded-lg border border-dashed">
    <div className="flex flex-col items-center gap-2 text-muted-foreground">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      <span className="text-sm">Loading chart...</span>
    </div>
  </div>
);

// Lazy loaded chart components
const LazyLineChart = React.lazy(() =>
  import("./LineChart").then((m) => ({ default: m.LineChart }))
);
const LazyBarChart = React.lazy(() =>
  import("./BarChart").then((m) => ({ default: m.BarChart }))
);
const LazyAreaChart = React.lazy(() =>
  import("./AreaChart").then((m) => ({ default: m.AreaChart }))
);
const LazyScatterChart = React.lazy(() =>
  import("./ScatterChart").then((m) => ({ default: m.ScatterChart }))
);
const LazyMap = React.lazy(() =>
  import("./Map").then((m) => ({ default: m.Map }))
);
const LazyPlotlyChart = React.lazy(() =>
  import("./PlotlyChart").then((m) => ({ default: m.PlotlyChart }))
);
const LazyVegaLiteChart = React.lazy(() =>
  import("./VegaLiteChart").then((m) => ({ default: m.VegaLiteChart }))
);
const LazyPyplot = React.lazy(() =>
  import("./Pyplot").then((m) => ({ default: m.Pyplot }))
);
const LazyGraphvizChart = React.lazy(() =>
  import("./GraphvizChart").then((m) => ({ default: m.GraphvizChart }))
);

// Export wrapped components for registry
export const LineChart: React.FC<NodeComponentProps> = (props) => (
  <Suspense fallback={<ChartLoading />}>
    <LazyLineChart {...props} />
  </Suspense>
);

export const BarChart: React.FC<NodeComponentProps> = (props) => (
  <Suspense fallback={<ChartLoading />}>
    <LazyBarChart {...props} />
  </Suspense>
);

export const AreaChart: React.FC<NodeComponentProps> = (props) => (
  <Suspense fallback={<ChartLoading />}>
    <LazyAreaChart {...props} />
  </Suspense>
);

export const ScatterChart: React.FC<NodeComponentProps> = (props) => (
  <Suspense fallback={<ChartLoading />}>
    <LazyScatterChart {...props} />
  </Suspense>
);

export const Map: React.FC<NodeComponentProps> = (props) => (
  <Suspense fallback={<ChartLoading />}>
    <LazyMap {...props} />
  </Suspense>
);

export const PlotlyChart: React.FC<NodeComponentProps> = (props) => (
  <Suspense fallback={<ChartLoading />}>
    <LazyPlotlyChart {...props} />
  </Suspense>
);

export const VegaLiteChart: React.FC<NodeComponentProps> = (props) => (
  <Suspense fallback={<ChartLoading />}>
    <LazyVegaLiteChart {...props} />
  </Suspense>
);

export const Pyplot: React.FC<NodeComponentProps> = (props) => (
  <Suspense fallback={<ChartLoading />}>
    <LazyPyplot {...props} />
  </Suspense>
);

export const GraphvizChart: React.FC<NodeComponentProps> = (props) => (
  <Suspense fallback={<ChartLoading />}>
    <LazyGraphvizChart {...props} />
  </Suspense>
);
