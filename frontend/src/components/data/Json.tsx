import React, { useEffect, useMemo, useState } from "react";
import { Check, ChevronDown, ChevronRight, Copy, FoldVertical, Search, TriangleAlert, UnfoldVertical } from "lucide-react";
import type { NodeComponentProps } from "../../registry/registry";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

interface JsonProps {
  data: any;
  expanded?: boolean | number;
  width?: number | string;
}

function expansionModeLabel(expanded: boolean | number): string {
  if (expanded === true) return "All expanded";
  if (expanded === false) return "Collapsed";
  return `Depth ${expanded}`;
}

function isExpandable(value: any): boolean {
  return Array.isArray(value) ? value.length > 0 : !!value && typeof value === "object" && Object.keys(value).length > 0;
}

function valueSummary(value: any): string {
  if (Array.isArray(value)) return `[${value.length}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).length}}`;
  if (typeof value === "string") return `"${value}"`;
  if (value === null) return "null";
  return String(value);
}

function valueColorClass(value: any): string {
  if (value === null) return "text-slate-400";
  if (typeof value === "string") return "text-emerald-600";
  if (typeof value === "number") return "text-sky-600";
  if (typeof value === "boolean") return "text-amber-600";
  return "text-slate-600";
}

function safeStringify(value: any): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function highlightMatch(text: string, query: string): React.ReactNode {
  if (!query) return text;
  const lower = text.toLowerCase();
  const target = query.toLowerCase();
  const index = lower.indexOf(target);
  if (index < 0) return text;
  const before = text.slice(0, index);
  const match = text.slice(index, index + query.length);
  const after = text.slice(index + query.length);
  return (
    <>
      {before}
      <mark className="rounded bg-amber-100 px-0.5 text-inherit">{match}</mark>
      {after}
    </>
  );
}

async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

function countMatches(value: any, query: string): number {
  if (!query) return 0;
  const target = query.toLowerCase();
  let count = 0;
  if (Array.isArray(value)) {
    for (const item of value) count += countMatches(item, query);
    return count;
  }
  if (value && typeof value === "object") {
    for (const [key, nested] of Object.entries(value)) {
      if (key.toLowerCase().includes(target)) count += 1;
      count += countMatches(nested, query);
    }
    return count;
  }
  if (String(valueSummary(value)).toLowerCase().includes(target)) count += 1;
  return count;
}

function nodeHasMatch(value: any, query: string, nodeKey?: string): boolean {
  const target = query.trim().toLowerCase();
  if (!target) return true;

  if (nodeKey?.toLowerCase().includes(target)) return true;

  if (!isExpandable(value)) {
    return valueSummary(value).toLowerCase().includes(target);
  }

  if (valueSummary(value).toLowerCase().includes(target)) return true;

  if (Array.isArray(value)) {
    return value.some((item) => nodeHasMatch(item, query));
  }

  return Object.entries(value).some(([key, nested]) => nodeHasMatch(nested, query, key));
}

interface JsonNodeProps {
  value: any;
  depth: number;
  nodeKey?: string;
  path: string;
  expansion: boolean | number;
  search: string;
}

const JsonNode: React.FC<JsonNodeProps> = ({ value, depth, nodeKey, path, expansion, search }) => {
  const query = search.trim();
  const queryActive = query.length > 0;
  const selfMatch = useMemo(() => {
    if (!queryActive) return false;
    const target = query.toLowerCase();
    return (nodeKey?.toLowerCase().includes(target) ?? false) || valueSummary(value).toLowerCase().includes(target);
  }, [nodeKey, query, queryActive, value]);
  const branchMatch = useMemo(() => nodeHasMatch(value, query, nodeKey), [nodeKey, query, value]);

  if (!branchMatch) {
    return null;
  }

  const initiallyExpanded =
    queryActive ||
    expansion === true ||
    selfMatch ||
    (typeof expansion === "number" && depth < Math.max(0, expansion));
  const [open, setOpen] = useState(initiallyExpanded);

  useEffect(() => {
    setOpen(initiallyExpanded);
  }, [initiallyExpanded]);

  const expandable = isExpandable(value);
  const isArray = Array.isArray(value);
  const indentStyle = { paddingLeft: `${depth * 16}px` };

  if (!expandable) {
    return (
      <div className={cn("group flex min-w-0 items-start gap-2 py-0.5 text-sm", selfMatch && "rounded bg-amber-50/70")} style={indentStyle}>
        {nodeKey !== undefined ? <span className="shrink-0 text-violet-600">{highlightMatch(`"${nodeKey}"`, search)}:</span> : null}
        <span className={cn("min-w-0 break-words", valueColorClass(value))}>{highlightMatch(valueSummary(value), search)}</span>
      </div>
    );
  }

  const entries = isArray
    ? value.map((item: any, index: number) => [String(index), item] as const)
    : Object.entries(value);
  const visibleEntries = queryActive
    ? entries.filter(([entryKey, entryValue]) => nodeHasMatch(entryValue, query, isArray ? undefined : entryKey))
    : entries;

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <div className={cn("group py-0.5", selfMatch && "rounded bg-amber-50/70")} style={indentStyle}>
        <div className="flex min-w-0 items-center gap-2 text-sm">
          <CollapsibleTrigger asChild>
            <button
              type="button"
              className="inline-flex h-5 w-5 items-center justify-center rounded text-slate-500 hover:bg-slate-100 hover:text-slate-700"
            >
              {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </button>
          </CollapsibleTrigger>
          {nodeKey !== undefined ? <span className="shrink-0 text-violet-600">{highlightMatch(`"${nodeKey}"`, search)}:</span> : null}
          <span className="font-medium text-slate-700">{isArray ? "Array" : "Object"}</span>
          <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-500">{valueSummary(value)}</span>
        </div>
        <CollapsibleContent>
          <div className="mt-1 border-l border-slate-200/80">
            {visibleEntries.map(([entryKey, entryValue]) => (
              <JsonNode
                key={`${path}-${entryKey}`}
                value={entryValue}
                depth={depth + 1}
                nodeKey={isArray ? undefined : entryKey}
                path={isArray ? `${path}[${entryKey}]` : path ? `${path}.${entryKey}` : entryKey}
                expansion={expansion}
                search={search}
              />
            ))}
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
};

export const Json: React.FC<NodeComponentProps> = ({ props }) => {
  const { data, expanded = true, width = "stretch" } = props as JsonProps;
  const [viewerExpansion, setViewerExpansion] = useState<boolean | number>(expanded);
  const [treeReset, setTreeReset] = useState(0);
  const [search, setSearch] = useState("");

  useEffect(() => {
    setViewerExpansion(expanded);
    setTreeReset((value) => value + 1);
  }, [expanded, data]);

  const serialized = useMemo(() => safeStringify(data), [data]);
  const rootLabel = Array.isArray(data) ? "Array" : data && typeof data === "object" ? "Object" : "Value";
  const rootMeta = valueSummary(data);
  const resultCount = useMemo(() => countMatches(data, search), [data, search]);
  const containerStyle = useMemo<React.CSSProperties>(() => {
    if (width === "stretch" || width === undefined) {
      return { width: "100%", maxWidth: "100%" };
    }
    if (typeof width === "number" && Number.isFinite(width)) {
      return { width, maxWidth: "100%" };
    }
    return { width: "auto", maxWidth: "100%" };
  }, [width]);

  const handleCopyJson = async () => {
    const ok = await copyText(serialized);
    if (ok) {
      toast("JSON copied to clipboard", {
        icon: <Check className="h-4 w-4 text-emerald-600" />,
        duration: 2500,
      });
      return;
    }
    toast("Unable to copy JSON", {
      icon: <TriangleAlert className="h-4 w-4 text-amber-600" />,
      duration: 3000,
    });
  };

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm" style={containerStyle}>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-slate-50 px-3 py-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
            <span>{rootLabel}</span>
            <span className="rounded bg-white px-1.5 py-0.5 text-[11px] font-medium text-slate-500 shadow-sm">
              {rootMeta}
            </span>
          </div>
          <div className="text-xs text-slate-500">{expansionModeLabel(viewerExpansion)}</div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-8 gap-1"
            onClick={() => {
              setViewerExpansion(true);
              setTreeReset((value) => value + 1);
            }}
          >
            <UnfoldVertical className="h-4 w-4" />
            Expand
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-8 gap-1"
            onClick={() => {
              setViewerExpansion(false);
              setTreeReset((value) => value + 1);
            }}
          >
            <FoldVertical className="h-4 w-4" />
            Collapse
          </Button>
          <Button type="button" variant="outline" size="sm" className="h-8 gap-1" onClick={handleCopyJson}>
            <Copy className="h-4 w-4" />
            Copy JSON
          </Button>
        </div>
      </div>
      <div className="border-b border-slate-200 bg-white px-3 py-2">
        <div className="relative">
          <Search className="pointer-events-none absolute left-2 top-2.5 h-4 w-4 text-slate-400" />
          <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search keys and values" className="pl-8" />
        </div>
        <div className="mt-2 text-xs text-slate-500">
          {search ? `${resultCount} result${resultCount === 1 ? "" : "s"}` : "Type to search"}
        </div>
      </div>
      <div className="max-h-[560px] overflow-auto bg-[linear-gradient(180deg,#ffffff,#f8fafc)] p-3 font-mono text-sm">
        {search && resultCount === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-200 bg-white/70 px-3 py-6 text-center text-sm text-slate-500">
            No matches found.
          </div>
        ) : (
          <JsonNode key={`json-tree-${treeReset}-${search}`} value={data} depth={0} path="" expansion={viewerExpansion} search={search} />
        )}
      </div>
    </div>
  );
};
