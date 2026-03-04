import React, { useEffect, useMemo, useRef, useState } from "react";
import { ArrowDownWideNarrow, ArrowUpWideNarrow, Download, Eye, EyeOff, Filter, Pin, RotateCcw, Search, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import type { GridColumn, GridFilter, GridPinned, GridSort, GridViewState } from "./types";
import { filterOptionsForType } from "./filtering";

interface GridToolbarProps {
  columns: GridColumn[];
  viewState: GridViewState;
  downloadable?: boolean;
  showSearch?: boolean;
  showFilters?: boolean;
  showColumnManager?: boolean;
  showResetView?: boolean;
  onSearchChange: (value: string) => void;
  onReset: () => void;
  onDownload?: () => void;
  onHiddenColumnsChange: (next: string[]) => void;
  onColumnOrderChange: (next: string[]) => void;
  onPinnedChange: (column: string, pinned: GridPinned) => void;
  onSortsChange: (next: GridSort[]) => void;
  onFiltersChange: (next: GridFilter[]) => void;
}

function createFilter(columns: GridColumn[]): GridFilter {
  const first = columns[0];
  const firstOp = first ? filterOptionsForType(first.type)[0]?.value ?? "contains" : "contains";
  return {
    id: String(Date.now()),
    column: first?.name ?? "",
    op: firstOp,
    value: "",
  };
}

export const GridToolbar: React.FC<GridToolbarProps> = ({
  columns,
  viewState,
  downloadable = true,
  showSearch = true,
  showFilters = true,
  showColumnManager = true,
  showResetView = true,
  onSearchChange,
  onReset,
  onDownload,
  onHiddenColumnsChange,
  onColumnOrderChange,
  onPinnedChange,
  onSortsChange,
  onFiltersChange,
}) => {
  const toolbarRef = useRef<HTMLDivElement>(null);
  const [compactButtons, setCompactButtons] = useState(false);
  const hidden = new Set(viewState.hiddenColumns);
  const showClearSort = showResetView && viewState.sorts.length > 0;
  const hasLeadingControls = showSearch || showFilters || showColumnManager;
  const hasTrailingControls = showClearSort || showResetView || downloadable;
  const visibleButtonCount = useMemo(
    () =>
      (showFilters ? 1 : 0) +
      (showColumnManager ? 1 : 0) +
      (showClearSort ? 1 : 0) +
      (showResetView ? 1 : 0) +
      (downloadable && onDownload ? 1 : 0),
    [downloadable, onDownload, showClearSort, showColumnManager, showFilters, showResetView]
  );

  useEffect(() => {
    const node = toolbarRef.current;
    if (!node || typeof ResizeObserver === "undefined") {
      return undefined;
    }

    const updateCompactMode = () => {
      const width = node.clientWidth;
      const threshold = (showSearch ? 420 : 180) + visibleButtonCount * 96;
      setCompactButtons(width > 0 && width < threshold);
    };

    updateCompactMode();
    const observer = new ResizeObserver(updateCompactMode);
    observer.observe(node);
    return () => observer.disconnect();
  }, [showSearch, visibleButtonCount]);

  if (!hasLeadingControls && !hasTrailingControls) {
    return null;
  }

  return (
    <div ref={toolbarRef} className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200/80 bg-slate-50/80 px-4 py-3 backdrop-blur-sm">
      <div className="flex min-w-0 flex-1 items-center gap-2">
        {showSearch ? (
          <div className={`relative flex-1 ${compactButtons ? "min-w-[160px] max-w-none" : "min-w-[220px] max-w-[360px]"}`}>
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              value={viewState.search}
              onChange={(event) => onSearchChange(event.target.value)}
              placeholder={compactButtons ? "Search..." : "Search rows..."}
              className="border-slate-200 bg-white pl-8 shadow-sm"
            />
          </div>
        ) : null}

        {showFilters ? (
          <Popover>
            <PopoverTrigger asChild>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className={`relative border-slate-200 bg-white shadow-sm ${compactButtons ? "h-9 w-9 px-0" : "gap-1"}`}
                aria-label="Filters"
                title="Filters"
              >
                <Filter className="h-4 w-4" />
                {compactButtons ? <span className="sr-only">Filters</span> : "Filters"}
                {viewState.filters.length ? (
                  <Badge
                    variant="secondary"
                    className={compactButtons ? "absolute -right-1 -top-1 h-4 min-w-4 px-1 py-0 text-[9px]" : "ml-1 px-1.5 py-0 text-[10px]"}
                  >
                    {viewState.filters.length}
                  </Badge>
                ) : null}
              </Button>
            </PopoverTrigger>
            <PopoverContent align="start" className="w-[420px] space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-slate-900">Filters</p>
                  <p className="text-xs text-slate-500">Apply typed filters to the current view.</p>
                </div>
                <Button type="button" variant="outline" size="sm" onClick={() => onFiltersChange([...viewState.filters, createFilter(columns)])}>
                  Add filter
                </Button>
              </div>
              <Separator />
              {!viewState.filters.length ? <p className="text-sm text-slate-500">No filters configured.</p> : null}
              <div className="space-y-3">
                {viewState.filters.map((filter) => {
                  const column = columns.find((item) => item.name === filter.column) ?? columns[0];
                  const type = column?.type ?? "string";
                  const ops = filterOptionsForType(type);
                  return (
                    <div key={filter.id} className="rounded-lg border border-slate-200 p-3">
                      <div className="grid grid-cols-3 gap-2">
                        <div className="space-y-1">
                          <Label>Column</Label>
                          <Select
                            value={filter.column}
                            onValueChange={(value) => {
                              const nextColumn = columns.find((item) => item.name === value) ?? column;
                              const nextOp = filterOptionsForType(nextColumn?.type ?? "string")[0]?.value ?? "contains";
                              onFiltersChange(
                                viewState.filters.map((item) =>
                                  item.id === filter.id ? { ...item, column: value, op: nextOp, value: "" } : item
                                )
                              );
                            }}
                          >
                            <SelectTrigger><SelectValue placeholder="Column" /></SelectTrigger>
                            <SelectContent>
                              {columns.map((item) => (
                                <SelectItem key={item.name} value={item.name}>{item.label || item.name}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-1">
                          <Label>Operator</Label>
                          <Select
                            value={filter.op}
                            onValueChange={(value) => {
                              onFiltersChange(
                                viewState.filters.map((item) => item.id === filter.id ? { ...item, op: value } : item)
                              );
                            }}
                          >
                            <SelectTrigger><SelectValue placeholder="Operator" /></SelectTrigger>
                            <SelectContent>
                              {ops.map((op) => (
                                <SelectItem key={op.value} value={op.value}>{op.label}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-1">
                          <Label>Value</Label>
                          <Input
                            value={Array.isArray(filter.value) ? String(filter.value[0] ?? "") : String(filter.value ?? "")}
                            onChange={(event) => {
                              const nextValue = filter.op === "between"
                                ? [event.target.value, Array.isArray(filter.value) ? filter.value[1] ?? "" : ""]
                                : event.target.value;
                              onFiltersChange(
                                viewState.filters.map((item) => item.id === filter.id ? { ...item, value: nextValue } : item)
                              );
                            }}
                            placeholder={filter.op === "between" ? "Min / start" : "Value"}
                            disabled={["is_empty", "not_empty", "is_true", "is_false"].includes(filter.op)}
                          />
                          {filter.op === "between" ? (
                            <Input
                              value={Array.isArray(filter.value) ? String(filter.value[1] ?? "") : ""}
                              onChange={(event) => {
                                const nextValue = [Array.isArray(filter.value) ? filter.value[0] ?? "" : "", event.target.value];
                                onFiltersChange(
                                  viewState.filters.map((item) => item.id === filter.id ? { ...item, value: nextValue } : item)
                                );
                              }}
                              placeholder="Max / end"
                            />
                          ) : null}
                        </div>
                      </div>
                      <div className="mt-2 flex justify-end">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => onFiltersChange(viewState.filters.filter((item) => item.id !== filter.id))}
                        >
                          <X className="mr-1 h-4 w-4" />
                          Remove
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </PopoverContent>
          </Popover>
        ) : null}

        {showColumnManager ? (
          <Popover>
            <PopoverTrigger asChild>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className={`border-slate-200 bg-white shadow-sm ${compactButtons ? "h-9 w-9 px-0" : "gap-1"}`}
                aria-label="Columns"
                title="Columns"
              >
                <Eye className="h-4 w-4" />
                {compactButtons ? <span className="sr-only">Columns</span> : "Columns"}
              </Button>
            </PopoverTrigger>
            <PopoverContent align="start" className="w-[360px] space-y-3">
              <div>
                <p className="text-sm font-semibold text-slate-900">Columns</p>
                <p className="text-xs text-slate-500">Show, hide, pin and reorder visible columns.</p>
              </div>
              <Separator />
              <div className="space-y-2">
                {viewState.columnOrder.map((columnName, index) => {
                  const column = columns.find((item) => item.name === columnName);
                  if (!column) return null;
                  const pinned = viewState.pinnedColumns[column.name] ?? column.pinned ?? null;
                  return (
                    <div key={column.name} className="rounded-md border border-slate-200 p-2">
                      <div className="flex items-center justify-between gap-2">
                        <label className="flex min-w-0 items-center gap-2 text-sm text-slate-700">
                          <Checkbox
                            checked={!hidden.has(column.name)}
                            onCheckedChange={(checked) => {
                              const next = checked === true
                                ? viewState.hiddenColumns.filter((item) => item !== column.name)
                                : [...viewState.hiddenColumns, column.name];
                              onHiddenColumnsChange(Array.from(new Set(next)));
                            }}
                          />
                          <span className="truncate">{column.label || column.name}</span>
                        </label>
                        <div className="flex items-center gap-1">
                          <Button
                            type="button"
                            size="icon"
                            variant="ghost"
                            className="h-7 w-7"
                            disabled={index === 0}
                            onClick={() => {
                              const next = [...viewState.columnOrder];
                              [next[index - 1], next[index]] = [next[index], next[index - 1]];
                              onColumnOrderChange(next);
                            }}
                          >
                            <ArrowUpWideNarrow className="h-4 w-4" />
                          </Button>
                          <Button
                            type="button"
                            size="icon"
                            variant="ghost"
                            className="h-7 w-7"
                            disabled={index === viewState.columnOrder.length - 1}
                            onClick={() => {
                              const next = [...viewState.columnOrder];
                              [next[index], next[index + 1]] = [next[index + 1], next[index]];
                              onColumnOrderChange(next);
                            }}
                          >
                            <ArrowDownWideNarrow className="h-4 w-4" />
                          </Button>
                          <Select value={pinned ?? "none"} onValueChange={(value) => onPinnedChange(column.name, value === "none" ? null : (value as GridPinned))}>
                            <SelectTrigger className="h-7 w-[96px] text-xs">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">Unpinned</SelectItem>
                              <SelectItem value="left">Pin left</SelectItem>
                              <SelectItem value="right">Pin right</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </PopoverContent>
          </Popover>
        ) : null}
      </div>

      <div className="flex items-center gap-2">
        {showClearSort ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className={`border-slate-200 bg-white shadow-sm ${compactButtons ? "h-9 w-9 px-0" : "gap-1"}`}
            onClick={() => onSortsChange([])}
            aria-label="Clear sort"
            title="Clear sort"
          >
            <ArrowUpWideNarrow className="h-4 w-4" />
            {compactButtons ? <span className="sr-only">Clear sort</span> : "Clear sort"}
          </Button>
        ) : null}
        {showResetView ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className={`border-slate-200 bg-white shadow-sm ${compactButtons ? "h-9 w-9 px-0" : "gap-1"}`}
            onClick={onReset}
            aria-label="Reset view"
            title="Reset view"
          >
            <RotateCcw className="h-4 w-4" />
            {compactButtons ? <span className="sr-only">Reset view</span> : "Reset view"}
          </Button>
        ) : null}
        {downloadable && onDownload ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className={`border-slate-200 bg-white shadow-sm ${compactButtons ? "h-9 w-9 px-0" : "gap-1"}`}
            onClick={onDownload}
            aria-label="CSV export"
            title="CSV export"
          >
            <Download className="h-4 w-4" />
            {compactButtons ? <span className="sr-only">CSV</span> : "CSV"}
          </Button>
        ) : null}
      </div>
    </div>
  );
};
