import React, { useId, useMemo } from "react";
import DOMPurify from "dompurify";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import type { NodeComponentProps } from "../../registry/registry";
import { cn } from "@/lib/utils";

interface MetricProps {
  label: string;
  value: string;
  delta?: string | null;
  deltaColor?: string;
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
  else if (typeof width === "number") {
    style.width = width;
    style.maxWidth = "100%";
  }

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

function sanitizeUrl(url: string): string | null {
  const trimmed = url.trim();
  if (!trimmed) return null;
  try {
    const parsed = new URL(trimmed, window.location.origin);
    const protocol = parsed.protocol.toLowerCase();
    if (protocol === "http:" || protocol === "https:" || protocol === "mailto:" || protocol === "tel:") {
      return parsed.href;
    }
  } catch {
    return null;
  }
  return null;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function inlineMarkdownToHtml(text: string): string {
  let html = escapeHtml(text);
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_match, alt, rawUrl) => {
    const safeUrl = sanitizeUrl(rawUrl);
    if (!safeUrl) return escapeHtml(alt);
    return `<img src="${safeUrl}" alt="${escapeHtml(alt)}" class="inline-block h-[1em] w-auto align-[-0.125em]" />`;
  });
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_match, label, rawUrl) => {
    const safeUrl = sanitizeUrl(rawUrl);
    if (!safeUrl) return escapeHtml(label);
    return `<a href="${safeUrl}" target="_blank" rel="noreferrer" class="underline underline-offset-2">${escapeHtml(label)}</a>`;
  });
  html = html.replace(/`([^`]+)`/g, "<code class=\"rounded bg-slate-100 px-1 py-0.5 font-mono text-[0.92em]\">$1</code>");
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/__([^_]+)__/g, "<strong>$1</strong>");
  html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  html = html.replace(/_([^_]+)_/g, "<em>$1</em>");
  html = html.replace(/~~([^~]+)~~/g, "<del>$1</del>");
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ["strong", "em", "del", "code", "a", "img"],
    ALLOWED_ATTR: ["href", "target", "rel", "class", "src", "alt"],
  });
}

function InlineMarkdown({
  text,
  className,
}: {
  text: string;
  className?: string;
}) {
  const html = useMemo(() => inlineMarkdownToHtml(text), [text]);
  return <span className={className} dangerouslySetInnerHTML={{ __html: html }} />;
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

function resolveDeltaTone(deltaColor: string | undefined, deltaDirection: string, hasDelta: boolean) {
  const normalizedColor = String(deltaColor || "normal").toLowerCase();
  const namedPalette: Record<string, { text: string; stroke: string }> = {
    red: { text: "text-rose-600", stroke: "rgb(225 29 72)" },
    orange: { text: "text-orange-600", stroke: "rgb(234 88 12)" },
    yellow: { text: "text-amber-600", stroke: "rgb(217 119 6)" },
    green: { text: "text-emerald-600", stroke: "rgb(5 150 105)" },
    blue: { text: "text-sky-600", stroke: "rgb(2 132 199)" },
    violet: { text: "text-violet-600", stroke: "rgb(124 58 237)" },
    gray: { text: "text-slate-500", stroke: "rgb(100 116 139)" },
    grey: { text: "text-slate-500", stroke: "rgb(100 116 139)" },
  };

  if (normalizedColor in namedPalette) {
    return namedPalette[normalizedColor];
  }
  if (!hasDelta || normalizedColor === "off" || deltaDirection === "flat") {
    return { text: "text-slate-500", stroke: "rgb(100 116 139)" };
  }
  if (normalizedColor === "inverse") {
    return deltaDirection === "up"
      ? { text: "text-rose-600", stroke: "rgb(225 29 72)" }
      : { text: "text-emerald-600", stroke: "rgb(5 150 105)" };
  }
  return deltaDirection === "down"
    ? { text: "text-rose-600", stroke: "rgb(225 29 72)" }
    : { text: "text-emerald-600", stroke: "rgb(5 150 105)" };
}

function SparkMetricChart({
  data,
  type,
  strokeColor,
}: {
  data: number[];
  type: "line" | "area" | "bar";
  strokeColor: string;
}) {
  if (!data.length) return null;
  const gradientId = useId().replace(/:/g, "");
  if (type === "bar") {
    const max = Math.max(...data) || 1;
    return (
      <div className="mt-3 flex h-12 items-end gap-1">
        {data.map((value, index) => (
          <div
            key={`${index}-${value}`}
            className="flex-1 rounded-t"
            style={{ height: `${Math.max(12, (value / max) * 100)}%`, backgroundColor: strokeColor }}
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
        <linearGradient id={`metric-area-${type}-${gradientId}`} x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stopColor={strokeColor} stopOpacity="0.6" />
          <stop offset="100%" stopColor={strokeColor} stopOpacity="0" />
        </linearGradient>
      </defs>
      {type === "area" ? (
        <path d={areaPath(data, width, height)} fill={`url(#metric-area-${type}-${gradientId})`} />
      ) : null}
      <polyline
        fill="none"
        stroke={strokeColor}
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
    width = "stretch",
    height = "content",
    chartData,
    chartType = "line",
    deltaArrow = "auto",
  } = props as MetricProps;

  const deltaNumber = useMemo(() => parseNumericDelta(delta), [delta]);
  const hasDelta = delta !== null && delta !== undefined && delta !== "";
  const deltaDirection = deltaArrow === "auto"
    ? deltaNumber === null
      ? "flat"
      : deltaNumber > 0
        ? "up"
        : deltaNumber < 0
          ? "down"
          : "flat"
    : deltaArrow;
  const tone = useMemo(
    () => resolveDeltaTone(deltaColor, String(deltaDirection), hasDelta),
    [deltaColor, deltaDirection, hasDelta]
  );
  const showArrow = hasDelta && deltaArrow !== "off";

  return (
    <div
      className={cn(
        "flex flex-col justify-between overflow-hidden rounded-2xl bg-white/95 p-4 shadow-sm ring-1 ring-slate-200/80",
        border ? "border border-slate-200" : "border border-transparent"
      )}
      style={resolveBoxStyle(width, height)}
      title={help || undefined}
    >
      {labelVisibility !== "collapsed" ? (
        <div className={cn("text-sm font-medium text-slate-500", labelVisibility === "hidden" && "invisible")}>
          <InlineMarkdown text={label} />
        </div>
      ) : null}
      <div className="mt-1 break-words text-3xl font-semibold tracking-tight text-slate-900">
        <InlineMarkdown text={value} />
      </div>
      {hasDelta ? (
        <div className={cn("mt-2 flex items-center gap-1.5 text-sm font-medium", tone.text)}>
          {showArrow ? (
            deltaDirection === "up" ? <ArrowUpRight className="h-4 w-4" /> :
            deltaDirection === "down" ? <ArrowDownRight className="h-4 w-4" /> :
            <Minus className="h-4 w-4" />
          ) : null}
          <InlineMarkdown text={delta || ""} />
        </div>
      ) : null}
      {Array.isArray(chartData) && chartData.length > 0 ? (
        <SparkMetricChart
          data={chartData}
          type={chartType}
          strokeColor={tone.stroke}
        />
      ) : null}
    </div>
  );
};
