import React from "react";
import { format, parse, parseISO } from "date-fns";
import { Image as ImageIcon, Link as LinkIcon, ChevronRight } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { normalizeListLikeValue, safeJsonStringify } from "./serialization";
import type { GridResolvedColumn } from "./types";

function parseDateValue(value: any): Date | undefined {
  if (typeof value !== "string" || !value.trim()) return undefined;
  try {
    if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
      return parse(value, "yyyy-MM-dd", new Date());
    }
    return parseISO(value);
  } catch {
    return undefined;
  }
}

function formatDisplayValue(value: any): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "number") {
    return Number.isInteger(value)
      ? value.toLocaleString()
      : value.toLocaleString(undefined, { maximumFractionDigits: 4 });
  }
  if (typeof value === "boolean") return value ? "true" : "false";
  if (Array.isArray(value) || typeof value === "object") return safeJsonStringify(value);
  return String(value);
}

function Sparkline({ data, type }: { data: number[]; type: string }) {
  if (!data.length) return <span className="text-xs text-slate-400">[]</span>;
  const width = 92;
  const height = 30;
  const pad = 2;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const yFor = (value: number) => height - pad - ((value - min) / range) * (height - pad * 2);
  const xFor = (index: number) =>
    data.length === 1 ? width / 2 : pad + (index / (data.length - 1)) * (width - pad * 2);

  if (type === "bar_chart") {
    const barWidth = Math.max(2, (width - pad * 2) / data.length - 1);
    return (
      <svg width={width} height={height}>
        {data.map((value, idx) => (
          <rect
            key={`${idx}-${value}`}
            x={xFor(idx) - barWidth / 2}
            y={yFor(value)}
            width={barWidth}
            height={height - pad - yFor(value)}
            fill="#0ea5e9"
            rx="1"
          />
        ))}
      </svg>
    );
  }

  const path = data
    .map((value, idx) => `${idx === 0 ? "M" : "L"}${xFor(idx)},${yFor(value)}`)
    .join(" ");

  if (type === "area_chart") {
    const areaPath = `${path} L${xFor(data.length - 1)},${height - pad} L${xFor(0)},${height - pad} Z`;
    return (
      <svg width={width} height={height}>
        <path d={areaPath} fill="rgba(14,165,233,0.16)" stroke="none" />
        <path d={path} fill="none" stroke="#0ea5e9" strokeWidth="1.5" strokeLinejoin="round" />
      </svg>
    );
  }

  return (
    <svg width={width} height={height}>
      <path d={path} fill="none" stroke="#0ea5e9" strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}

export function renderGridCell(
  column: GridResolvedColumn,
  value: any,
  rowValues: any[],
  allColumns: GridResolvedColumn[],
  opts?: { compact?: boolean; onOpenJson?: (columnName: string, value: any) => void },
) {
  const type = String(column.type ?? "string").toLowerCase();
  const compact = !!opts?.compact;

  if (type === "progress") {
    const progress = Number(value);
    const safe = Number.isFinite(progress) ? Math.max(0, Math.min(100, progress)) : 0;
    return (
      <div className="flex w-full items-center gap-2">
        <Progress value={safe} className="h-2 flex-1" />
        <span className="w-10 text-right text-xs text-slate-500">{Math.round(safe)}%</span>
      </div>
    );
  }

  if (type === "checkbox" || type === "boolean") {
    return (
      <div className="flex items-center gap-2">
        <Checkbox checked={!!value} disabled className="data-[state=checked]:bg-emerald-600 data-[state=checked]:border-emerald-600" />
        <Badge variant={value ? "secondary" : "outline"} className={cn("px-2 py-0 text-[10px]", value ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "text-slate-500")}>
          {value ? "Active" : "Inactive"}
        </Badge>
      </div>
    );
  }

  if (type === "link") {
    const href = String(value ?? "").trim();
    const linkedColumnIndex = allColumns.findIndex((candidate) => candidate.name === column.displayText);
    const label = linkedColumnIndex >= 0
      ? String((rowValues[allColumns[linkedColumnIndex].originalIndex] ?? href) || column.label)
      : String(column.displayText || href || column.label);
    return href ? (
      <Button type="button" variant="link" className="h-auto justify-start px-0 text-sky-600" asChild>
        <a href={href} target="_blank" rel="noreferrer" onClick={(event) => event.stopPropagation()}>
          <LinkIcon className="mr-1 h-3.5 w-3.5" />
          <span className="truncate">{label}</span>
        </a>
      </Button>
    ) : (
      <span className="text-slate-400">Empty link</span>
    );
  }

  if (type === "image") {
    const src = String(value ?? "").trim();
    return (
      <div className="flex min-w-0 items-center gap-2">
        <Avatar className="h-7 w-7">
          {src ? <AvatarImage src={src} alt="" /> : null}
          <AvatarFallback className="bg-slate-100 text-slate-400">
            <ImageIcon className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
        <span className="truncate">{src || "Empty image URL"}</span>
      </div>
    );
  }

  if (type === "list" || type === "multiselect") {
    const items = normalizeListLikeValue(value);
    const visibleCount = compact ? 2 : 5;
    return (
      <div className={cn("flex min-w-0 items-center gap-1 py-1", compact ? "flex-nowrap overflow-hidden" : "flex-wrap")}>
        {items.length === 0 ? (
          <span className="text-slate-400">[]</span>
        ) : (
          items.slice(0, visibleCount).map((item, idx) => (
            <Badge key={`${idx}-${String(item)}`} variant="secondary" className="max-w-[96px] truncate">
              {String(item)}
            </Badge>
          ))
        )}
        {items.length > visibleCount ? <Badge variant="outline">+{items.length - visibleCount}</Badge> : null}
      </div>
    );
  }

  if (type === "json") {
    const preview = safeJsonStringify(value);
    return (
      <button
        type="button"
        className="flex min-w-0 items-center gap-1 rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-left text-slate-700 transition-colors hover:bg-slate-100 hover:text-slate-900"
        onClick={(event) => {
          event.stopPropagation();
          opts?.onOpenJson?.(column.name, value);
        }}
      >
        <ChevronRight className="h-3.5 w-3.5 shrink-0" />
        <span className="truncate font-mono text-xs">{preview}</span>
      </button>
    );
  }

  if (["line_chart", "bar_chart", "area_chart"].includes(type)) {
    const values = normalizeListLikeValue(value).map((item) => Number(item)).filter((item) => Number.isFinite(item));
    return <Sparkline data={values} type={type} />;
  }

  if (type === "date") {
    const parsed = parseDateValue(value);
    return <Badge variant="outline" className="font-mono font-normal text-slate-600">{parsed ? format(parsed, "yyyy-MM-dd") : formatDisplayValue(value)}</Badge>;
  }

  if (type === "datetime") {
    const parsed = parseDateValue(value);
    return <Badge variant="outline" className="font-mono font-normal text-slate-600">{parsed ? format(parsed, "yyyy-MM-dd HH:mm") : formatDisplayValue(value)}</Badge>;
  }

  if (type === "time") {
    return <Badge variant="outline" className="font-mono font-normal text-slate-600">{formatDisplayValue(value)}</Badge>;
  }

  if (type === "number" || type === "integer") {
    return <span className="font-mono text-right w-full">{formatDisplayValue(value)}</span>;
  }

  return <span className="block truncate text-slate-700">{formatDisplayValue(value) || <span className="text-slate-400">Empty</span>}</span>;
}
