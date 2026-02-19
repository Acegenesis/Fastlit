import React, { Suspense, useState, useEffect, useRef } from "react";
import type { NodeComponentProps } from "../../registry/registry";

// Spinner shown while the lazy bundle loads
const ChartLoading: React.FC = () => (
  <div className="flex items-center justify-center h-64 bg-muted/20 rounded-lg border border-dashed">
    <div className="flex flex-col items-center gap-2 text-muted-foreground">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      <span className="text-sm">Loading chart…</span>
    </div>
  </div>
);

// Skeleton shown until the component scrolls into view
const ChartSkeleton: React.FC<{ height: number }> = ({ height }) => (
  <div
    className="bg-muted/10 rounded-lg border border-dashed animate-pulse"
    style={{ height }}
  />
);

/**
 * Returns a ref + boolean: the boolean flips to true once the element
 * enters the viewport (with a 300px lookahead).  After that it never
 * reverts, so the chart stays mounted.
 */
function useInViewport(rootMargin = "300px") {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    // Fallback for browsers without IntersectionObserver
    if (typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          obs.disconnect();
        }
      },
      { rootMargin }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [rootMargin]);

  return { ref, visible };
}

/**
 * Defers rendering children until they scroll near the viewport.
 * Shows a sized skeleton placeholder until then.
 */
const DeferredChart: React.FC<{ children: React.ReactNode; height: number }> = ({
  children,
  height,
}) => {
  const { ref, visible } = useInViewport("300px");
  return (
    <div ref={ref}>
      {visible ? children : <ChartSkeleton height={height} />}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Lazy imports — each becomes a separate bundle chunk
// ---------------------------------------------------------------------------
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
const LazyBokehChart = React.lazy(() =>
  import("./BokehChart").then((m) => ({ default: m.BokehChart }))
);
const LazyPydeckChart = React.lazy(() =>
  import("./PydeckChart").then((m) => ({ default: m.PydeckChart }))
);

// ---------------------------------------------------------------------------
// Exported wrappers — light charts load immediately, heavy ones are deferred
// ---------------------------------------------------------------------------

// Recharts-based — small shared bundle, load immediately
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
export const Pyplot: React.FC<NodeComponentProps> = (props) => (
  <Suspense fallback={<ChartLoading />}>
    <LazyPyplot {...props} />
  </Suspense>
);
// Bokeh and PyDeck use iframes — very lightweight wrappers, no heavy bundle
export const BokehChart: React.FC<NodeComponentProps> = (props) => (
  <Suspense fallback={<ChartLoading />}>
    <LazyBokehChart {...props} />
  </Suspense>
);
export const PydeckChart: React.FC<NodeComponentProps> = (props) => (
  <Suspense fallback={<ChartLoading />}>
    <LazyPydeckChart {...props} />
  </Suspense>
);

// Heavy charts — deferred until near viewport
export const PlotlyChart: React.FC<NodeComponentProps> = (props) => (
  <DeferredChart height={props.props?.height ?? 400}>
    <Suspense fallback={<ChartLoading />}>
      <LazyPlotlyChart {...props} />
    </Suspense>
  </DeferredChart>
);
export const VegaLiteChart: React.FC<NodeComponentProps> = (props) => (
  <DeferredChart height={props.props?.spec?.height ?? 300}>
    <Suspense fallback={<ChartLoading />}>
      <LazyVegaLiteChart {...props} />
    </Suspense>
  </DeferredChart>
);
export const GraphvizChart: React.FC<NodeComponentProps> = (props) => (
  <DeferredChart height={240}>
    <Suspense fallback={<ChartLoading />}>
      <LazyGraphvizChart {...props} />
    </Suspense>
  </DeferredChart>
);
