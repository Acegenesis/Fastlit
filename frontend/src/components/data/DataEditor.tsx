import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CalendarIcon, ChevronDown, Plus, Trash2 } from "lucide-react";
import { format, parseISO } from "date-fns";
import type { NodeComponentProps } from "../../registry/registry";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { GridToolbar } from "./grid/GridToolbar";
import { GridEmptyState } from "./grid/GridEmptyState";
import { renderGridCell } from "./grid/renderers";
import { useGridColumns } from "./grid/useGridColumns";
import { useGridViewState } from "./grid/useGridViewState";
import { applyGridSearchAndFilters } from "./grid/filtering";
import { applyGridSorts, toggleGridSort } from "./grid/sorting";
import { buildCsv, defaultCsvFileName, normalizeListLikeValue, safeJsonStringify, triggerCsvDownload } from "./grid/serialization";
import { useGridVirtualRows } from "./grid/useGridVirtualRows";
import type { GridColumn, GridResolvedColumn, GridRowModel } from "./grid/types";
import { cn } from "@/lib/utils";

interface Column {
  name: string;
  type: string;
}

interface ColumnConfig {
  type?: string;
  label?: string;
  width?: string | number | null;
  minWidth?: number | null;
  maxWidth?: number | null;
  resizable?: boolean | null;
  pinned?: "left" | "right" | null;
  help?: string | null;
  hidden?: boolean;
  disabled?: boolean;
  required?: boolean;
  default?: any;
  min?: number | string | null;
  max?: number | string | null;
  step?: number | string | null;
  maxChars?: number | null;
  validate?: string | null;
  options?: string[];
  displayText?: string | null;
  format?: string | null;
  yMin?: number | null;
  yMax?: number | null;
}

interface DataEditorProps {
  columns: Column[];
  rows: any[][];
  index?: any[];
  height?: number | string;
  width?: number | string;
  useContainerWidth?: boolean;
  editable?: boolean;
  numRows?: "fixed" | "dynamic";
  disabledColumns?: string[];
  columnConfig?: Record<string, ColumnConfig>;
  columnOrder?: string[];
  rerunOnChange?: boolean;
  totalRows?: number;
  truncated?: boolean;
  rowHeight?: number;
  placeholder?: string;
  toolbar?: boolean;
  downloadable?: boolean;
  persistView?: boolean;
}

const DEFAULT_ROW_HEIGHT = 50;
const HEADER_HEIGHT = 48;
const TOOLBAR_HEIGHT = 49;
const FOOTER_HEIGHT = 38;
const DEFAULT_HEIGHT = 420;
const INDEX_WIDTH = 72;
const ACTIONS_WIDTH = 60;
const EMPTY_SELECT_VALUE = "__fastlit_empty__";
const LIVE_COMMIT_DEBOUNCE_MS = 250;

function normalizeColumns(columns: Column[], columnConfig: Record<string, ColumnConfig> = {}): GridColumn[] {
  return columns.map((column) => {
    const cfg = columnConfig[column.name] ?? {};
    return {
      name: column.name,
      type: String(cfg.type ?? column.type ?? "string").toLowerCase(),
      label: cfg.label ?? column.name,
      help: cfg.help,
      hidden: cfg.hidden,
      disabled: cfg.disabled,
      required: cfg.required,
      width: cfg.width,
      minWidth: cfg.minWidth,
      maxWidth: cfg.maxWidth,
      resizable: cfg.resizable,
      pinned: cfg.pinned ?? null,
      options: cfg.options,
      displayText: cfg.displayText,
      format: cfg.format,
      default: cfg.default,
      min: cfg.min,
      max: cfg.max,
      step: cfg.step,
      maxChars: cfg.maxChars,
      validate: cfg.validate,
      yMin: cfg.yMin,
      yMax: cfg.yMax,
    };
  });
}

function schemaSignature(columns: GridColumn[]): string {
  return JSON.stringify(columns.map((column) => ({ name: column.name, type: column.type })));
}

function normalizeRows(rows: any[][], indexValues?: any[]): GridRowModel[] {
  return Array.isArray(rows)
    ? rows.map((row, idx) => ({
        rowId: String(idx),
        originalPosition: idx,
        indexValue: indexValues?.[idx],
        cells: Array.isArray(row) ? [...row] : [],
      }))
    : [];
}

function resolveOuterStyle(width: number | string | undefined, useContainerWidth: boolean | undefined): React.CSSProperties {
  if (useContainerWidth || width === "stretch" || width === undefined) {
    return { width: "100%", maxWidth: "100%" };
  }
  if (typeof width === "number" && Number.isFinite(width)) {
    return { width, maxWidth: width };
  }
  return { width: "auto", maxWidth: "100%" };
}

function resolveGridHeight(height: number | string | undefined, rowCount: number, rowHeight: number, showToolbar: boolean): number {
  if (typeof height === "number" && Number.isFinite(height)) return height;
  const chrome = HEADER_HEIGHT + FOOTER_HEIGHT + (showToolbar ? TOOLBAR_HEIGHT : 0) + 2;
  const content = chrome + Math.max(rowHeight, rowCount * rowHeight);
  return Math.min(DEFAULT_HEIGHT, Math.max(chrome + rowHeight, content));
}

function parseDateValue(value: any): Date | undefined {
  if (typeof value !== "string" || !value.trim()) return undefined;
  try {
    return parseISO(value);
  } catch {
    return undefined;
  }
}

function formatDateLabel(value: any): string {
  const parsed = parseDateValue(value);
  if (!parsed) return "Select date";
  try {
    return format(parsed, "yyyy-MM-dd");
  } catch {
    return String(value);
  }
}

function serializeEditorValue(value: any, type: string): string {
  if (value === null || value === undefined) return "";
  if (["list", "line_chart", "bar_chart", "area_chart", "json", "multiselect"].includes(type)) {
    return safeJsonStringify(value);
  }
  return String(value);
}

function parseBooleanLike(value: any): boolean {
  if (typeof value === "boolean") return value;
  if (typeof value === "number") return value !== 0;
  const lowered = String(value ?? "").trim().toLowerCase();
  return lowered === "true" || lowered === "1" || lowered === "yes" || lowered === "on";
}

function clampNumber(value: number, column: GridResolvedColumn): number {
  let next = value;
  if (column.min !== undefined && column.min !== null && column.min !== "") {
    const min = Number(column.min);
    if (Number.isFinite(min)) next = Math.max(next, min);
  }
  if (column.max !== undefined && column.max !== null && column.max !== "") {
    const max = Number(column.max);
    if (Number.isFinite(max)) next = Math.min(next, max);
  }
  return next;
}

function parseCellValue(raw: string, column: GridResolvedColumn, previousValue: any): any {
  const trimmed = raw.trim();
  if (column.required && trimmed === "") return previousValue;
  if (column.maxChars && trimmed.length > column.maxChars) return previousValue;
  if (column.validate && trimmed) {
    try {
      const matcher = new RegExp(column.validate);
      if (!matcher.test(trimmed)) return previousValue;
    } catch {
      return previousValue;
    }
  }

  switch (column.type) {
    case "number":
    case "integer":
    case "progress": {
      if (trimmed === "") return null;
      const parsed = Number(trimmed);
      if (!Number.isFinite(parsed)) return previousValue;
      const clamped = clampNumber(parsed, column);
      return column.type === "integer" ? Math.trunc(clamped) : clamped;
    }
    case "checkbox":
    case "boolean":
      return parseBooleanLike(trimmed);
    case "date":
    case "time":
    case "datetime":
      return trimmed === "" ? null : trimmed;
    case "list":
    case "line_chart":
    case "bar_chart":
    case "area_chart":
    case "multiselect":
      return normalizeListLikeValue(raw);
    case "json":
      if (!trimmed) return null;
      try {
        return JSON.parse(trimmed);
      } catch {
        return previousValue;
      }
    default:
      return raw;
  }
}

function nextIndexValue(current: any[]): any {
  if (!current.length) return 0;
  if (current.every((value) => typeof value === "number" && Number.isFinite(value))) {
    return Math.max(...current) + 1;
  }
  return `row-${current.length + 1}`;
}

function createDefaultCellValue(column: GridResolvedColumn): any {
  if (column.default !== undefined && column.default !== null) return column.default;
  if (["checkbox", "boolean"].includes(column.type)) return false;
  if (["list", "multiselect", "line_chart", "bar_chart", "area_chart"].includes(column.type)) return [];
  if (["number", "integer", "progress"].includes(column.type)) return null;
  if (column.type === "json") return {};
  return "";
}

function indexColumnWidth(hasIndex: boolean): number {
  return hasIndex ? INDEX_WIDTH : 0;
}

function draftKey(rowId: string, columnName: string): string {
  return `${rowId}:${columnName}`;
}

interface JsonPopoverEditorProps {
  label: string;
  value: any;
  disabled: boolean;
  onCommit: (next: any) => void;
}

const JsonPopoverEditor: React.FC<JsonPopoverEditorProps> = ({ label, value, disabled, onCommit }) => {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(safeJsonStringify(value));

  useEffect(() => {
    setDraft(safeJsonStringify(value));
  }, [value]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button type="button" variant="outline" size="sm" className="h-8 w-full justify-between overflow-hidden px-2" disabled={disabled}>
          <span className="truncate text-left">{label}</span>
          <ChevronDown className="h-3.5 w-3.5 shrink-0 text-slate-400" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[28rem] max-w-[90vw] p-3" align="start">
        <div className="space-y-2">
          <Textarea value={draft} onChange={(event) => setDraft(event.target.value)} className="min-h-[180px] font-mono text-xs" />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" size="sm" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              type="button"
              size="sm"
              onClick={() => {
                try {
                  onCommit(draft.trim() ? JSON.parse(draft) : null);
                  setOpen(false);
                } catch {
                  // keep editor open on invalid JSON
                }
              }}
            >
              Apply
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
};

interface ListPopoverEditorProps {
  label: string;
  value: any;
  disabled: boolean;
  onCommit: (next: any[]) => void;
}

const ListPopoverEditor: React.FC<ListPopoverEditorProps> = ({ label, value, disabled, onCommit }) => {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(safeJsonStringify(value));

  useEffect(() => {
    setDraft(safeJsonStringify(value));
  }, [value]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button type="button" variant="outline" size="sm" className="h-8 w-full justify-between overflow-hidden px-2" disabled={disabled}>
          <span className="truncate text-left">{label}</span>
          <ChevronDown className="h-3.5 w-3.5 shrink-0 text-slate-400" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[24rem] max-w-[90vw] p-3" align="start">
        <div className="space-y-2">
          <Textarea value={draft} onChange={(event) => setDraft(event.target.value)} className="min-h-[120px] font-mono text-xs" />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" size="sm" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              type="button"
              size="sm"
              onClick={() => {
                onCommit(normalizeListLikeValue(draft));
                setOpen(false);
              }}
            >
              Apply
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
};

interface MultiselectPopoverEditorProps {
  value: any;
  options: string[];
  disabled: boolean;
  onCommit: (next: string[]) => void;
}

const MultiselectPopoverEditor: React.FC<MultiselectPopoverEditorProps> = ({ value, options, disabled, onCommit }) => {
  const [open, setOpen] = useState(false);
  const selected = useMemo(() => new Set(normalizeListLikeValue(value).map((item) => String(item))), [value]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button type="button" variant="outline" size="sm" className="h-8 w-full justify-between overflow-hidden px-2" disabled={disabled}>
          <span className="flex min-w-0 flex-wrap items-center gap-1 overflow-hidden">
            {selected.size
              ? Array.from(selected)
                  .slice(0, 3)
                  .map((item) => (
                    <Badge key={item} variant="secondary" className="truncate">
                      {item}
                    </Badge>
                  ))
              : <span className="text-slate-400">Select</span>}
          </span>
          <ChevronDown className="h-3.5 w-3.5 shrink-0 text-slate-400" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-64 p-3" align="start">
        <div className="space-y-2">
          <div className="max-h-60 space-y-2 overflow-auto">
            {options.map((option) => {
              const checked = selected.has(option);
              return (
                <label key={option} className="flex items-center gap-2 text-sm">
                  <Checkbox
                    checked={checked}
                    onCheckedChange={(next) => {
                      const updated = new Set(selected);
                      if (next) updated.add(option);
                      else updated.delete(option);
                      onCommit(Array.from(updated));
                    }}
                  />
                  <span>{option}</span>
                </label>
              );
            })}
          </div>
          <div className="flex justify-end">
            <Button type="button" size="sm" variant="outline" onClick={() => setOpen(false)}>
              Close
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
};

export const DataEditor: React.FC<NodeComponentProps> = ({ nodeId, props, sendEvent }) => {
  const {
    columns = [],
    rows = [],
    index,
    height,
    width,
    useContainerWidth = true,
    editable = true,
    numRows = "fixed",
    disabledColumns = [],
    columnConfig = {},
    columnOrder = [],
    rerunOnChange = true,
    totalRows,
    truncated = false,
    rowHeight = DEFAULT_ROW_HEIGHT,
    placeholder,
    toolbar = true,
    downloadable = true,
    persistView = true,
  } = props as DataEditorProps;

  const parentRef = useRef<HTMLDivElement>(null);
  const scrollPersistTimerRef = useRef<number | null>(null);
  const resizeStateRef = useRef<{ columnName: string; startX: number; startWidth: number } | null>(null);
  const liveCommitTimersRef = useRef<Map<string, number>>(new Map());
  const nextRowIdRef = useRef(0);
  const baseColumns = useMemo(() => normalizeColumns(columns, columnConfig), [columnConfig, columns]);
  const initialColumnOrder = useMemo(
    () => (columnOrder.length ? [...columnOrder] : baseColumns.map((column) => column.name)),
    [baseColumns, columnOrder]
  );
  const { viewState, updateViewState, resetViewState } = useGridViewState({
    nodeId,
    widgetKind: "data_editor",
    schemaSignature: schemaSignature(baseColumns),
    enabled: !!persistView,
    initialColumnOrder,
  });

  const [localRows, setLocalRows] = useState<GridRowModel[]>(() => normalizeRows(rows, index));
  const [localIndex, setLocalIndex] = useState<any[]>(() => (Array.isArray(index) ? [...index] : []));
  const [draftValues, setDraftValues] = useState<Record<string, string>>({});
  const localRowsRef = useRef<GridRowModel[]>(normalizeRows(rows, index));
  const localIndexRef = useRef<any[]>(Array.isArray(index) ? [...index] : []);

  useEffect(() => {
    const normalized = normalizeRows(rows, index);
    nextRowIdRef.current = normalized.length;
    localRowsRef.current = normalized;
    setLocalRows(normalized);
    const normalizedIndex = Array.isArray(index) ? [...index] : [];
    localIndexRef.current = normalizedIndex;
    setLocalIndex(normalizedIndex);
    setDraftValues({});
  }, [index, rows]);

  const hasIndex = Array.isArray(index) && index.length > 0;
  const isDynamic = numRows === "dynamic";
  const outerStyle = resolveOuterStyle(width, useContainerWidth);
  const { resolvedColumns, columnIndexMap, totalWidth } = useGridColumns({
    columns: baseColumns,
    rows: localRows.map((row) => row.cells),
    viewState,
  });

  const displayRows = useMemo(() => {
    const searched = applyGridSearchAndFilters(localRows, viewState.search, viewState.filters, columnIndexMap);
    return applyGridSorts(searched, viewState.sorts, columnIndexMap);
  }, [columnIndexMap, localRows, viewState.filters, viewState.search, viewState.sorts]);

  const containerHeight = resolveGridHeight(height, Math.max(displayRows.length, 1), rowHeight, toolbar);
  const rowVirtualizer = useGridVirtualRows({ rowCount: displayRows.length, parentRef, rowHeight });
  const shouldVirtualize = displayRows.length > 100;
  const contentWidth = totalWidth + indexColumnWidth(hasIndex) + (isDynamic ? ACTIONS_WIDTH : 0);

  useEffect(() => {
    if (!persistView || !parentRef.current) return;
    parentRef.current.scrollTop = viewState.scrollTop;
    parentRef.current.scrollLeft = viewState.scrollLeft;
  }, [persistView, viewState.scrollLeft, viewState.scrollTop]);

  const persistScrollState = useCallback((top: number, left: number) => {
    if (!persistView) return;
    if (scrollPersistTimerRef.current !== null) {
      window.clearTimeout(scrollPersistTimerRef.current);
    }
    scrollPersistTimerRef.current = window.setTimeout(() => {
      updateViewState((current) => ({ ...current, scrollTop: top, scrollLeft: left }));
    }, 120);
  }, [persistView, updateViewState]);

  const emitRows = useCallback((nextRows: GridRowModel[], nextIndex: any[], commit: boolean) => {
    const payload: Record<string, any> = {
      rows: nextRows.map((row) => row.cells),
    };
    if (hasIndex) {
      payload.index = nextIndex;
    }
    sendEvent(nodeId, payload, commit && rerunOnChange ? undefined : { noRerun: true });
  }, [hasIndex, nodeId, rerunOnChange, sendEvent]);

  const setLocalCellValue = useCallback((rowId: string, columnName: string, nextValue: any) => {
    const columnIndex = columnIndexMap[columnName];
    if (columnIndex === undefined) return;
    const nextRows = localRowsRef.current.map((row) => {
      if (row.rowId !== rowId) return row;
      const cells = [...row.cells];
      cells[columnIndex] = nextValue;
      return { ...row, cells };
    });
    localRowsRef.current = nextRows;
    setLocalRows(nextRows);
  }, [columnIndexMap]);

  const updateCell = useCallback((rowId: string, columnName: string, nextValue: any, commit: boolean) => {
    const columnIndex = columnIndexMap[columnName];
    if (columnIndex === undefined) return;
    const nextRows = localRowsRef.current.map((row) => {
      if (row.rowId !== rowId) return row;
      const cells = [...row.cells];
      cells[columnIndex] = nextValue;
      return { ...row, cells };
    });
    localRowsRef.current = nextRows;
    setLocalRows(nextRows);
    emitRows(nextRows, localIndexRef.current, commit);
  }, [columnIndexMap, emitRows]);

  const clearLiveCommitTimer = useCallback((cellKey: string) => {
    const timer = liveCommitTimersRef.current.get(cellKey);
    if (timer !== undefined) {
      window.clearTimeout(timer);
      liveCommitTimersRef.current.delete(cellKey);
    }
  }, []);

  const scheduleLiveCommit = useCallback((row: GridRowModel, column: GridResolvedColumn, nextValue: any) => {
    const cellKey = draftKey(row.rowId, column.name);
    setLocalCellValue(row.rowId, column.name, nextValue);
    clearLiveCommitTimer(cellKey);
    const timer = window.setTimeout(() => {
      liveCommitTimersRef.current.delete(cellKey);
      updateCell(row.rowId, column.name, nextValue, true);
    }, LIVE_COMMIT_DEBOUNCE_MS);
    liveCommitTimersRef.current.set(cellKey, timer);
  }, [clearLiveCommitTimer, setLocalCellValue, updateCell]);

  const deleteRow = useCallback((rowId: string) => {
    const currentRows = localRowsRef.current;
    const removedIndex = currentRows.findIndex((row) => row.rowId === rowId);
    if (removedIndex >= 0) {
      const nextRows = currentRows.filter((row) => row.rowId !== rowId);
      const currentIndex = localIndexRef.current;
      const nextIndex = hasIndex ? currentIndex.filter((_, idx) => idx !== removedIndex) : currentIndex;
      localRowsRef.current = nextRows;
      setLocalRows(nextRows);
      if (hasIndex) {
        localIndexRef.current = nextIndex;
        setLocalIndex(nextIndex);
      }
      emitRows(nextRows, nextIndex, true);
    }
  }, [emitRows, hasIndex]);

  const addRow = useCallback(() => {
    const currentRows = localRowsRef.current;
    const currentIndex = localIndexRef.current;
    const nextRowId = `new-${nextRowIdRef.current}`;
    nextRowIdRef.current += 1;
    const cells = resolvedColumns.map((column) => createDefaultCellValue(column));
    const nextRow: GridRowModel = {
      rowId: nextRowId,
      originalPosition: currentRows.length,
      indexValue: hasIndex ? nextIndexValue(currentIndex) : undefined,
      cells,
    };
    const nextRows = [...currentRows, nextRow];
    const nextIndex = hasIndex ? [...currentIndex, nextRow.indexValue] : currentIndex;
    localRowsRef.current = nextRows;
    setLocalRows(nextRows);
    if (hasIndex) {
      localIndexRef.current = nextIndex;
      setLocalIndex(nextIndex);
    }
    emitRows(nextRows, nextIndex, true);
  }, [emitRows, hasIndex, resolvedColumns]);

  const startResize = useCallback((event: React.MouseEvent<HTMLDivElement>, column: GridResolvedColumn) => {
    if (!column.resizable) return;
    event.preventDefault();
    event.stopPropagation();
    resizeStateRef.current = {
      columnName: column.name,
      startX: event.clientX,
      startWidth: column.widthPx,
    };
  }, []);

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      const state = resizeStateRef.current;
      if (!state) return;
      const delta = event.clientX - state.startX;
      updateViewState((current) => ({
        ...current,
        manualWidths: {
          ...current.manualWidths,
          [state.columnName]: Math.max(110, state.startWidth + delta),
        },
      }));
    };
    const handleMouseUp = () => {
      resizeStateRef.current = null;
    };
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [updateViewState]);

  const handleDownload = useCallback(() => {
    triggerCsvDownload(defaultCsvFileName("fastlit-data-editor"), buildCsv(resolvedColumns, displayRows));
  }, [displayRows, resolvedColumns]);

  const commitDraft = useCallback((row: GridRowModel, column: GridResolvedColumn) => {
    const key = draftKey(row.rowId, column.name);
    clearLiveCommitTimer(key);
    const raw = draftValues[key] ?? serializeEditorValue(row.cells[column.originalIndex], column.type);
    const nextValue = parseCellValue(raw, column, row.cells[column.originalIndex]);
    setDraftValues((current) => {
      const next = { ...current };
      delete next[key];
      return next;
    });
    updateCell(row.rowId, column.name, nextValue, true);
  }, [clearLiveCommitTimer, draftValues, updateCell]);

  useEffect(() => {
    return () => {
      for (const timer of liveCommitTimersRef.current.values()) {
        window.clearTimeout(timer);
      }
      liveCommitTimersRef.current.clear();
    };
  }, []);

  const renderEditorCell = useCallback((row: GridRowModel, column: GridResolvedColumn) => {
    const cellKey = draftKey(row.rowId, column.name);
    const value = row.cells[column.originalIndex];
    const disabled = !editable || disabledColumns.includes(column.name) || !!column.disabled;
    const draft = draftValues[cellKey] ?? serializeEditorValue(value, column.type);

    if (disabled) {
      return renderGridCell(column, value, row.cells, resolvedColumns, { compact: true });
    }

    if (["checkbox", "boolean"].includes(column.type)) {
      return (
        <Checkbox
          checked={parseBooleanLike(value)}
          onCheckedChange={(checked) => updateCell(row.rowId, column.name, Boolean(checked), true)}
        />
      );
    }

    if (column.type === "selectbox") {
      const options = Array.isArray(column.options) ? column.options : [];
      const currentValue = value === null || value === undefined || value === "" ? EMPTY_SELECT_VALUE : String(value);
      return (
        <Select
          value={currentValue}
          onValueChange={(next) => updateCell(row.rowId, column.name, next === EMPTY_SELECT_VALUE ? null : next, true)}
        >
          <SelectTrigger className="h-8 w-full min-w-0">
            <SelectValue placeholder="Select" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={EMPTY_SELECT_VALUE}>Empty</SelectItem>
            {options.map((option) => (
              <SelectItem key={option} value={option}>
                {option}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      );
    }

    if (column.type === "date") {
      const selectedDate = parseDateValue(value);
      return (
        <Popover>
          <PopoverTrigger asChild>
            <Button type="button" variant="outline" size="sm" className="h-8 w-full justify-start px-2 text-left font-normal">
              <CalendarIcon className="mr-2 h-3.5 w-3.5 text-slate-400" />
              <span className="truncate">{formatDateLabel(value)}</span>
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="start">
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={(date) => updateCell(row.rowId, column.name, date ? format(date, "yyyy-MM-dd") : null, true)}
            />
          </PopoverContent>
        </Popover>
      );
    }

    if (column.type === "multiselect") {
      return (
        <MultiselectPopoverEditor
          value={value}
          options={Array.isArray(column.options) ? column.options : []}
          disabled={disabled}
          onCommit={(next) => updateCell(row.rowId, column.name, next, true)}
        />
      );
    }

    if (column.type === "json") {
      return (
        <JsonPopoverEditor
          label={value === null || value === undefined ? "Edit JSON" : "JSON"}
          value={value}
          disabled={disabled}
          onCommit={(next) => updateCell(row.rowId, column.name, next, true)}
        />
      );
    }

    if (["list", "line_chart", "bar_chart", "area_chart"].includes(column.type)) {
      const label = Array.isArray(value) && value.length ? `${value.length} items` : "Edit list";
      return (
        <ListPopoverEditor
          label={label}
          value={value}
          disabled={disabled}
          onCommit={(next) => updateCell(row.rowId, column.name, next, true)}
        />
      );
    }

    const inputType = column.type === "number" || column.type === "integer" || column.type === "progress"
      ? "number"
      : column.type === "time"
        ? "time"
        : column.type === "datetime"
          ? "datetime-local"
          : "text";

    return (
      <Input
        value={draft}
        type={inputType}
        className="h-8 min-w-0"
        min={column.min ?? undefined}
        max={column.max ?? undefined}
        step={column.step ?? undefined}
        maxLength={column.maxChars ?? undefined}
        onChange={(event) => {
          const nextValue = event.target.value;
          setDraftValues((current) => ({ ...current, [cellKey]: nextValue }));
          const parsed = parseCellValue(nextValue, column, value);
          if (rerunOnChange) {
            scheduleLiveCommit(row, column, parsed);
          } else {
            updateCell(row.rowId, column.name, parsed, false);
          }
        }}
        onBlur={() => commitDraft(row, column)}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            commitDraft(row, column);
          } else if (event.key === "Escape") {
            clearLiveCommitTimer(cellKey);
            setDraftValues((current) => {
              const next = { ...current };
              delete next[cellKey];
              return next;
            });
          }
        }}
      />
    );
  }, [clearLiveCommitTimer, commitDraft, disabledColumns, draftValues, editable, resolvedColumns, rerunOnChange, scheduleLiveCommit, updateCell]);

  if (!resolvedColumns.length) {
    return <GridEmptyState message={placeholder || "Empty editor"} />;
  }

  const renderRow = (row: GridRowModel, rowIndex: number, layoutStyle?: React.CSSProperties) => {
    const background = rowIndex % 2 === 0 ? "bg-white" : "bg-slate-50/60";
    return (
      <div
        key={row.rowId}
        className={cn("left-0 top-0 flex w-full border-b border-slate-100", background, shouldVirtualize && "absolute")}
        style={layoutStyle}
      >
        {hasIndex ? (
          <div className="sticky z-10 flex items-center border-r border-slate-100 bg-inherit px-4 font-mono text-xs text-slate-500" style={{ width: INDEX_WIDTH, minWidth: INDEX_WIDTH, left: 0 }}>
            {String(row.indexValue ?? row.originalPosition)}
          </div>
        ) : null}
        {resolvedColumns.map((column) => {
          const style: React.CSSProperties = { width: column.widthPx, minWidth: column.widthPx };
          if (column.pinned === "left") {
            style.position = "sticky";
            style.left = (column.leftOffset ?? 0) + indexColumnWidth(hasIndex);
            style.zIndex = 10;
            style.background = rowIndex % 2 === 0 ? "rgba(255,255,255,0.96)" : "rgba(248,250,252,0.96)";
          } else if (column.pinned === "right") {
            style.position = "sticky";
            style.right = (column.rightOffset ?? 0) + (isDynamic ? ACTIONS_WIDTH : 0);
            style.zIndex = 10;
            style.background = rowIndex % 2 === 0 ? "rgba(255,255,255,0.96)" : "rgba(248,250,252,0.96)";
          }
          return (
            <div key={`${row.rowId}-${column.name}`} className="flex min-w-0 items-center border-r border-slate-100 px-3 py-2 text-sm last:border-r-0" style={style}>
              {renderEditorCell(row, column)}
            </div>
          );
        })}
        {isDynamic ? (
          <div className="sticky right-0 z-10 flex items-center justify-center border-l border-slate-100 bg-inherit px-2" style={{ width: ACTIONS_WIDTH, minWidth: ACTIONS_WIDTH }}>
            <Button type="button" size="icon" variant="ghost" className="h-8 w-8 text-slate-500 hover:text-red-600" onClick={() => deleteRow(row.rowId)}>
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ) : null}
      </div>
    );
  };

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm ring-1 ring-slate-950/[0.03]" style={outerStyle}>
      {toolbar ? (
        <GridToolbar
          columns={baseColumns}
          viewState={viewState}
          downloadable={downloadable}
          onSearchChange={(value) => updateViewState((current) => ({ ...current, search: value }))}
          onReset={resetViewState}
          onDownload={downloadable ? handleDownload : undefined}
          onHiddenColumnsChange={(hiddenColumns) => updateViewState((current) => ({ ...current, hiddenColumns }))}
          onColumnOrderChange={(columnOrderValue) => updateViewState((current) => ({ ...current, columnOrder: columnOrderValue }))}
          onPinnedChange={(columnName, pinned) => updateViewState((current) => ({
            ...current,
            pinnedColumns: { ...current.pinnedColumns, [columnName]: pinned },
          }))}
          onSortsChange={(sorts) => updateViewState((current) => ({ ...current, sorts }))}
          onFiltersChange={(filters) => updateViewState((current) => ({ ...current, filters }))}
        />
      ) : null}

      <div className="flex border-b border-slate-200/80 bg-slate-50/90 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500" style={{ height: HEADER_HEIGHT }}>
        {hasIndex ? (
          <div className="sticky z-20 flex items-center border-r border-slate-200/80 bg-slate-100/95 px-3 text-[11px] text-slate-500" style={{ width: INDEX_WIDTH, minWidth: INDEX_WIDTH, left: 0 }}>
            Index
          </div>
        ) : null}
        {resolvedColumns.map((column) => {
          const isSorted = viewState.sorts.find((item) => item.column === column.name);
          const style: React.CSSProperties = { width: column.widthPx, minWidth: column.widthPx };
          if (column.pinned === "left") {
            style.position = "sticky";
            style.left = (column.leftOffset ?? 0) + indexColumnWidth(hasIndex);
            style.zIndex = 20;
            style.background = "rgba(248, 250, 252, 0.98)";
          } else if (column.pinned === "right") {
            style.position = "sticky";
            style.right = (column.rightOffset ?? 0) + (isDynamic ? ACTIONS_WIDTH : 0);
            style.zIndex = 20;
            style.background = "rgba(248, 250, 252, 0.98)";
          }
          return (
            <div
              key={column.name}
              className="relative flex items-center gap-2 border-r border-slate-200/80 px-3 last:border-r-0"
              style={style}
              title={column.help ?? column.name}
              onClick={(event) => updateViewState((current) => ({ ...current, sorts: toggleGridSort(current.sorts, column.name, event.shiftKey) }))}
            >
              <span className="truncate">{column.label}</span>
              {isSorted ? <span className="text-[10px] text-sky-600">{isSorted.direction === "asc" ? "ASC" : "DESC"}</span> : null}
              {column.resizable ? (
                <div role="separator" aria-orientation="vertical" className="absolute right-0 top-0 h-full w-3 cursor-col-resize" onMouseDown={(event) => startResize(event, column)}>
                  <div className="absolute right-1 top-2 bottom-2 w-px rounded-full bg-slate-300 hover:bg-sky-500" />
                </div>
              ) : null}
            </div>
          );
        })}
        {isDynamic ? (
          <div className="sticky right-0 z-20 flex items-center justify-center border-l border-slate-200/80 bg-slate-100/95 px-3 text-[11px] text-slate-500" style={{ width: ACTIONS_WIDTH, minWidth: ACTIONS_WIDTH }}>
            Row
          </div>
        ) : null}
      </div>

      {!displayRows.length ? (
        <div className="p-4">
          <GridEmptyState message={placeholder || "No rows match the current view."} />
        </div>
      ) : (
        <div
          ref={parentRef}
          className="overflow-auto"
          style={{ height: containerHeight - HEADER_HEIGHT - FOOTER_HEIGHT - (toolbar ? TOOLBAR_HEIGHT : 0) }}
          onScroll={(event) => {
            const target = event.currentTarget;
            persistScrollState(target.scrollTop, target.scrollLeft);
          }}
        >
          {shouldVirtualize ? (
            <div style={{ height: `${rowVirtualizer.getTotalSize()}px`, width: contentWidth, position: "relative" }}>
              {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                const row = displayRows[virtualRow.index];
                if (!row) return null;
                return renderRow(row, virtualRow.index, {
                  height: `${virtualRow.size}px`,
                  transform: `translateY(${virtualRow.start}px)`,
                  position: "absolute",
                });
              })}
            </div>
          ) : (
            <div style={{ width: contentWidth }}>
              {displayRows.map((row, rowIndex) => renderRow(row, rowIndex))}
            </div>
          )}
        </div>
      )}

      <div className="flex items-center justify-between gap-3 border-t border-slate-200/80 bg-slate-50/90 px-3 py-2 text-xs text-slate-500">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline" className="font-normal">{(typeof totalRows === "number" ? totalRows : localRows.length).toLocaleString()} rows</Badge>
          <Badge variant="outline" className="font-normal">{resolvedColumns.length} columns</Badge>
          {truncated ? <span className="ml-2 text-amber-700">(preview truncated)</span> : null}
        </div>
        {isDynamic ? (
          <Button type="button" size="sm" variant="outline" className="h-8 gap-1 border-slate-200 bg-white shadow-sm" onClick={addRow}>
            <Plus className="h-4 w-4" />
            Add row
          </Button>
        ) : null}
      </div>
    </div>
  );
};
