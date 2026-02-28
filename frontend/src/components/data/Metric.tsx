import React, { useMemo } from "react";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import type { NodeComponentProps } from "../../registry/registry";
import { cn } from "@/lib/utils";

interface MetricProps {
  label: string;
  value: string;
  delta?: string | null;
  deltaColor?: "normal" | "inverse" | "off";
  help?: string;
  labelVisibility?: "visible" | "hidden" | "collapsed";
  border?: boolean;
  width?: number | string;
  height?: number | string;
  chartData?: number[] | null;
  chartType?: "line" | "area" | "bar";
  deltaArrow?: "auto" | "up" | "down" | "off";
}

function resolveBoxStyle(width: number | string | undefined, height: number | string | undefined): React.CSSProperties {
  const style: React.CSSProperties = {};
  if (width === "stretch") style.width = "100%";
  else if (width === "content" || width === undefined) style.width = "fit-content";
  else if (typeof width === "number") style.width = width;

  if (height === "stretch") style.height = "100%";
  else if (height === "content" || height === undefined) style.height = "auto";
  else if (typeof height === "number") style.height = height;
  return style;
}

function parseNumericDelta(delta?: string | null): number | null {
  if (!delta) return null;
  const normalized = Number.parseFloat(delta.replace(/[^0-9+\-.]/g, ""));
  return Number.isFinite(normalized) ? normalized : null;
}

function sparklinePoints(data: number[], width: number, height: number): string {
  if (data.length <= 1) {
    const y = height / 2;
    return `0,${y} ${width},${y}`;
  }
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  return data
    .map((value, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${x},${y}`;
    })
    .join(" ");
}

function areaPath(data: number[], width: number, height: number): string {
  const points = sparklinePoints(data, width, height).split(" ");
  if (!points.length) return "";
  const first = points[0];
  const last = points[points.length - 1];
  return `M${first} L${points.slice(1).join(" L")} L${last.split(",")[0]},${height} L0,${height} Z`;
}

function SparkMetricChart({ data, type }: { data: number[]; type: "line" | "area" | "bar" }) {
  if (!data.length) return null;
  if (type === "bar") {
    const max = Math.max(...data) || 1;
    return (
      <div className="mt-3 flex h-12 items-end gap-1">
        {data.map((value, index) => (
          <div
            key={`${index}-${value}`}
            className="flex-1 rounded-t bg-sky-500/70"
            style={{ height: `${Math.max(12, (value / max) * 100)}%` }}
          />
        ))}
      </div>
    );
  }

  const width = 180;
  const height = 48;
  const points = sparklinePoints(data, width, height);
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="mt-3 h-12 w-full overflow-visible">
      <defs>
        <linearGradient id={`metric-area-${type}`} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="rgb(14 165 233 / 0.35)" />
          <stop offset="100%" stopColor="rgb(14 165 233 / 0.04)" />
        </linearGradient>
      </defs>
      {type === "area" ? (
        <path d={areaPath(data, width, height)} fill={`url(#metric-area-${type})`} />
      ) : null}
      <polyline
        fill="none"
        stroke="rgb(14 165 233)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
}

export const Metric: React.FC<NodeComponentProps> = ({ props }) => {
  const {
    label,
    value,
    delta,
    deltaColor = "normal",
    help,
    labelVisibility = "visible",
    border = false,
    width = "content",
    height = "content",
    chartData,
    chartType = "line",
    deltaArrow = "auto",
  } = props as MetricProps;

  const deltaNumber = useMemo(() => parseNumericDelta(delta), [delta]);
  const deltaDirection = deltaArrow === "auto"
    ? deltaNumber === null
      ? "flat"
      : deltaNumber > 0
        ? "up"
        : deltaNumber < 0
          ? "down"
          : "flat"
    : deltaArrow;

  const deltaColorClass = deltaColor === "off"
    ? "text-slate-500"
    : deltaColor === "inverse"
      ? deltaDirection === "up"
        ? "text-rose-600"
        : deltaDirection === "down"
          ? "text-emerald-600"
          : "text-slate-500"
      : deltaDirection === "up"
        ? "text-emerald-600"
        : deltaDirection === "down"
          ? "text-rose-600"
          : "text-slate-500";

  const showArrow = delta && deltaArrow !== "off";

  return (
    <div
      className={cn(
        "flex flex-col justify-between rounded-2xl bg-white/95 p-4 shadow-sm ring-1 ring-slate-200/80",
        border ? "border border-slate-200" : "border border-transparent"
      )}
      style={resolveBoxStyle(width, height)}
      title={help || undefined}
    >
      {labelVisibility !== "collapsed" ? (
        <div className={cn("text-sm font-medium text-slate-500", labelVisibility === "hidden" && "sr-only")}>
          {label}
        </div>
      ) : null}
      <div className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">{value}</div>
      {delta ? (
        <div className={cn("mt-2 flex items-center gap-1.5 text-sm font-medium", deltaColorClass)}>
          {showArrow ? (
            deltaDirection === "up" ? <ArrowUpRight className="h-4 w-4" /> :
            deltaDirection === "down" ? <ArrowDownRight className="h-4 w-4" /> :
            <Minus className="h-4 w-4" />
          ) : null}
          <span>{delta}</span>
        </div>
      ) : null}
      {Array.isArray(chartData) && chartData.length > 0 ? <SparkMetricChart data={chartData} type={chartType} /> : null}
    </div>
  );
};
