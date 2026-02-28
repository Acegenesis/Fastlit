import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { GridToolbar } from "./grid/GridToolbar";
import { GridEmptyState } from "./grid/GridEmptyState";
import { renderGridCell } from "./grid/renderers";
import { useGridColumns } from "./grid/useGridColumns";
import { useGridViewState } from "./grid/useGridViewState";
import { applyGridSearchAndFilters } from "./grid/filtering";
import { applyGridSorts, toggleGridSort } from "./grid/sorting";
import { buildCsv, defaultCsvFileName, encodeGridFilters, encodeGridSorts, triggerCsvDownload } from "./grid/serialization";
import { useGridVirtualRows } from "./grid/useGridVirtualRows";
import type { GridColumn, GridPinned, GridResolvedColumn, GridRowModel } from "./grid/types";
import { cn } from "@/lib/utils";

const DEFAULT_ROW_HEIGHT = 48;
const HEADER_HEIGHT = 48;
const TOOLBAR_HEIGHT = 49;
const DEFAULT_HEIGHT = 420;
const SELECTION_WIDTH = 48;
const INDEX_WIDTH = 72;

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
  pinned?: GridPinned;
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

interface DataFrameProps {
  columns: Column[];
  rows: any[][];
  index?: any[];
  positions?: number[];
  width?: number | string;
  height?: number | string;
  useContainerWidth?: boolean;
  static?: boolean;
  totalRows?: number;
  truncated?: boolean;
  sourceId?: string;
  windowSize?: number;
  selectable?: boolean;
  selectionMode?: "single-row" | "multi-row";
  selectedRows?: number[];
  columnConfig?: Record<string, ColumnConfig>;
  columnOrder?: string[];
  rowHeight?: number;
  placeholder?: string;
  toolbar?: boolean;
  downloadable?: boolean;
  persistView?: boolean;
}

function schemaSignature(columns: GridColumn[]): string {
  return JSON.stringify(columns.map((column) => ({ name: column.name, type: column.type })));
}

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

function normalizeRows(rows: any[][], indexValues?: any[], positions?: number[]): GridRowModel[] {
  return Array.isArray(rows)
    ? rows.map((row, idx) => ({
        rowId: String(positions?.[idx] ?? idx),
        originalPosition: Number.isFinite(Number(positions?.[idx])) ? Number(positions?.[idx]) : idx,
        indexValue: indexValues?.[idx],
        cells: Array.isArray(row) ? [...row] : [],
      }))
    : [];
}

function resolveGridHeight(height: number | string | undefined, rowCount: number, rowHeight: number, showToolbar: boolean): number {
  if (typeof height === "number" && Number.isFinite(height)) return height;
  const chrome = HEADER_HEIGHT + (showToolbar ? TOOLBAR_HEIGHT : 0) + 2;
  const content = chrome + Math.max(rowHeight, rowCount * rowHeight);
  return Math.min(DEFAULT_HEIGHT, Math.max(chrome + rowHeight, content));
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

function readOnlyIndexColumn(hasIndex: boolean) {
  return hasIndex ? INDEX_WIDTH : 0;
}

export const DataFrame: React.FC<NodeComponentProps> = ({ nodeId, props, sendEvent }) => {
  const {
    columns = [],
    rows = [],
    index,
    positions,
    width,
    height,
    useContainerWidth = true,
    static: isStatic = false,
    totalRows,
    truncated = false,
    sourceId,
    windowSize = 300,
    selectable = false,
    selectionMode = "multi-row",
    selectedRows = [],
    columnConfig = {},
    columnOrder = [],
    rowHeight = DEFAULT_ROW_HEIGHT,
    placeholder,
    toolbar = !isStatic,
    downloadable = !isStatic,
    persistView = true,
  } = props as DataFrameProps;

  const parentRef = useRef<HTMLDivElement>(null);
  const scrollPersistTimerRef = useRef<number | null>(null);
  const resizeStateRef = useRef<{ columnName: string; startX: number; startWidth: number } | null>(null);
  const [serverOffset, setServerOffset] = useState(0);
  const [serverRows, setServerRows] = useState<any[][]>(rows);
  const [serverIndex, setServerIndex] = useState<any[] | undefined>(index);
  const [serverPositions, setServerPositions] = useState<number[] | undefined>(positions);
  const [serverTotalRows, setServerTotalRows] = useState<number>(typeof totalRows === "number" ? totalRows : rows.length);
  const [loadingWindow, setLoadingWindow] = useState(false);
  const [selectedRowPositions, setSelectedRowPositions] = useState<number[]>(Array.isArray(selectedRows) ? [...selectedRows] : []);
  const fetchAbortRef = useRef<AbortController | null>(null);
  const baseColumns = useMemo(() => normalizeColumns(columns, columnConfig), [columnConfig, columns]);
  const initialColumnOrder = useMemo(
    () => (columnOrder.length ? [...columnOrder] : baseColumns.map((column) => column.name)),
    [baseColumns, columnOrder]
  );
  const { viewState, updateViewState, resetViewState } = useGridViewState({
    nodeId,
    widgetKind: isStatic ? "table" : "dataframe",
    schemaSignature: schemaSignature(baseColumns),
    enabled: !!persistView,
    initialColumnOrder,
  });

  const selectionColumnVisible = selectable && selectionMode !== "single-row";
  const hasIndex = Array.isArray(index) && index.length > 0;
  const isServerPaged = !!sourceId && (typeof totalRows === "number" ? totalRows : rows.length) > rows.length;

  useEffect(() => {
    setServerOffset(0);
    setServerRows(rows);
    setServerIndex(index);
    setServerPositions(positions);
    setServerTotalRows(typeof totalRows === "number" ? totalRows : rows.length);
  }, [index, positions, rows, sourceId, totalRows]);

  useEffect(() => {
    setSelectedRowPositions(Array.isArray(selectedRows) ? [...selectedRows] : []);
  }, [selectedRows]);

  const baseRowModels = useMemo(() => normalizeRows(rows, index, positions), [index, positions, rows]);
  const currentWindowModels = useMemo(
    () => normalizeRows(serverRows, serverIndex, serverPositions),
    [serverIndex, serverPositions, serverRows]
  );

  const { resolvedColumns, columnIndexMap, totalWidth } = useGridColumns({
    columns: baseColumns,
    rows: isServerPaged ? serverRows : rows,
    viewState,
  });

  const filteredLocalRows = useMemo(() => {
    if (isServerPaged) return currentWindowModels;
    const searched = applyGridSearchAndFilters(baseRowModels, viewState.search, viewState.filters, columnIndexMap);
    return applyGridSorts(searched, viewState.sorts, columnIndexMap);
  }, [baseRowModels, columnIndexMap, currentWindowModels, isServerPaged, viewState.filters, viewState.search, viewState.sorts]);

  const displayRows = isServerPaged ? currentWindowModels : filteredLocalRows;
  const effectiveTotalRows = isServerPaged ? serverTotalRows : displayRows.length;
  const outerStyle = resolveOuterStyle(width, useContainerWidth);
  const containerHeight = resolveGridHeight(height, Math.max(displayRows.length, 1), rowHeight, toolbar && !isStatic);
  const rowVirtualizer = useGridVirtualRows({ rowCount: displayRows.length, parentRef, rowHeight });
  const shouldVirtualize = isServerPaged || displayRows.length > 100;
  const selectedSet = useMemo(() => new Set(selectedRowPositions), [selectedRowPositions]);

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

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    params.set("search", viewState.search);
    params.set("sort", encodeGridSorts(viewState.sorts));
    params.set("filters", encodeGridFilters(viewState.filters));
    return params.toString();
  }, [viewState.filters, viewState.search, viewState.sorts]);

  useEffect(() => {
    if (!isServerPaged || !sourceId) return;
    const virtualItems = rowVirtualizer.getVirtualItems();
    if (virtualItems.length === 0) return;

    const first = virtualItems[0]!.index;
    const last = virtualItems[virtualItems.length - 1]!.index;
    const needStart = Math.max(0, first - Math.floor(windowSize * 0.5));
    const needEnd = Math.min(effectiveTotalRows, last + Math.floor(windowSize * 1.5));
    const haveStart = serverOffset;
    const haveEnd = serverOffset + serverRows.length;
    if (needStart >= haveStart && needEnd <= haveEnd) return;

    const fetchOffset = needStart;
    const fetchLimit = Math.max(windowSize, needEnd - needStart);
    fetchAbortRef.current?.abort();
    const controller = new AbortController();
    fetchAbortRef.current = controller;
    setLoadingWindow(true);
    fetch(`/_fastlit/dataframe/${encodeURIComponent(sourceId)}?offset=${fetchOffset}&limit=${fetchLimit}&${queryString}`, {
      signal: controller.signal,
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((payload) => {
        setServerOffset(payload.offset ?? fetchOffset);
        setServerRows(Array.isArray(payload.rows) ? payload.rows : []);
        setServerIndex(Array.isArray(payload.index) ? payload.index : undefined);
        setServerPositions(Array.isArray(payload.positions) ? payload.positions.map((value: any) => Number(value)) : undefined);
        setServerTotalRows(typeof payload.totalRows === "number" ? payload.totalRows : 0);
      })
      .catch(() => undefined)
      .finally(() => {
        if (!controller.signal.aborted) setLoadingWindow(false);
      });
  }, [effectiveTotalRows, isServerPaged, queryString, rowVirtualizer, serverOffset, serverRows.length, sourceId, windowSize]);

  useEffect(() => {
    if (!isServerPaged || !sourceId) return;
    fetchAbortRef.current?.abort();
    const controller = new AbortController();
    fetchAbortRef.current = controller;
    setLoadingWindow(true);
    fetch(`/_fastlit/dataframe/${encodeURIComponent(sourceId)}?offset=0&limit=${windowSize}&${queryString}`, {
      signal: controller.signal,
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((payload) => {
        setServerOffset(payload.offset ?? 0);
        setServerRows(Array.isArray(payload.rows) ? payload.rows : []);
        setServerIndex(Array.isArray(payload.index) ? payload.index : undefined);
        setServerPositions(Array.isArray(payload.positions) ? payload.positions.map((value: any) => Number(value)) : undefined);
        setServerTotalRows(typeof payload.totalRows === "number" ? payload.totalRows : 0);
      })
      .catch(() => undefined)
      .finally(() => {
        if (!controller.signal.aborted) setLoadingWindow(false);
      });
  }, [isServerPaged, queryString, sourceId, windowSize]);

  const emitSelection = useCallback((positionsToSelect: number[]) => {
    const normalized = Array.from(new Set(positionsToSelect))
      .filter((value) => Number.isInteger(value) && value >= 0)
      .sort((left, right) => left - right);
    setSelectedRowPositions(normalized);
    sendEvent(nodeId, normalized.join(","));
  }, [nodeId, sendEvent]);

  const toggleSelection = useCallback((rowPosition: number) => {
    if (!selectable) return;
    if (selectionMode === "single-row") {
      emitSelection([rowPosition]);
      return;
    }
    const next = selectedSet.has(rowPosition)
      ? selectedRowPositions.filter((value) => value !== rowPosition)
      : [...selectedRowPositions, rowPosition];
    emitSelection(next);
  }, [emitSelection, selectable, selectedRowPositions, selectedSet, selectionMode]);

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

  const handleDownload = useCallback(async () => {
    if (!displayRows.length && !isServerPaged) return;
    if (!isServerPaged || !sourceId) {
      triggerCsvDownload(defaultCsvFileName(isStatic ? "fastlit-table" : "fastlit-dataframe"), buildCsv(resolvedColumns, displayRows));
      return;
    }

    const collected: GridRowModel[] = [];
    let offset = 0;
    const chunkSize = 5000;
    while (offset < serverTotalRows) {
      const response = await fetch(`/_fastlit/dataframe/${encodeURIComponent(sourceId)}?offset=${offset}&limit=${chunkSize}&${queryString}`);
      if (!response.ok) break;
      const payload = await response.json();
      const rowsChunk = normalizeRows(payload.rows ?? [], payload.index, payload.positions);
      collected.push(...rowsChunk);
      offset += rowsChunk.length;
      if (!rowsChunk.length) break;
    }
    triggerCsvDownload(defaultCsvFileName(isStatic ? "fastlit-table" : "fastlit-dataframe"), buildCsv(resolvedColumns, collected));
  }, [displayRows, isServerPaged, isStatic, queryString, resolvedColumns, serverTotalRows, sourceId]);

  if (!resolvedColumns.length) {
    return <GridEmptyState message={placeholder || (isStatic ? "Empty table" : "Empty DataFrame")} />;
  }

  const contentWidth = totalWidth + (selectionColumnVisible ? SELECTION_WIDTH : 0) + readOnlyIndexColumn(hasIndex);
  const renderRow = (row: GridRowModel, rowIndex: number, layoutStyle?: React.CSSProperties) => {
    const isSelected = selectedSet.has(row.originalPosition);
    const background = isSelected ? "bg-sky-50" : rowIndex % 2 === 0 ? "bg-white" : "bg-slate-50/60";
    return (
      <div
        key={row.rowId}
        className={cn("left-0 top-0 flex w-full border-b border-slate-100", background, selectable && "cursor-pointer", shouldVirtualize && "absolute")}
        style={layoutStyle}
        onClick={() => toggleSelection(row.originalPosition)}
      >
        {selectionColumnVisible ? (
          <div className="sticky left-0 z-20 flex items-center justify-center border-r border-slate-100 bg-inherit" style={{ width: SELECTION_WIDTH, minWidth: SELECTION_WIDTH }} onClick={(event) => event.stopPropagation()}>
            <Checkbox checked={isSelected} onCheckedChange={() => toggleSelection(row.originalPosition)} />
          </div>
        ) : null}
        {hasIndex ? (
          <div className="sticky z-10 flex items-center border-r border-slate-100 bg-inherit px-4 font-mono text-xs text-slate-500" style={{ width: INDEX_WIDTH, minWidth: INDEX_WIDTH, left: selectionColumnVisible ? SELECTION_WIDTH : 0 }}>
            {String(row.indexValue ?? row.originalPosition)}
          </div>
        ) : null}
        {resolvedColumns.map((column) => {
          const style: React.CSSProperties = { width: column.widthPx, minWidth: column.widthPx };
          if (column.pinned === "left") {
            style.position = "sticky";
            style.left = (column.leftOffset ?? 0) + (selectionColumnVisible ? SELECTION_WIDTH : 0) + readOnlyIndexColumn(hasIndex);
            style.zIndex = 10;
            style.background = isSelected ? "rgb(240 249 255 / 0.96)" : rowIndex % 2 === 0 ? "rgba(255,255,255,0.96)" : "rgba(248,250,252,0.96)";
          } else if (column.pinned === "right") {
            style.position = "sticky";
            style.right = column.rightOffset ?? 0;
            style.zIndex = 10;
            style.background = isSelected ? "rgb(240 249 255 / 0.96)" : rowIndex % 2 === 0 ? "rgba(255,255,255,0.96)" : "rgba(248,250,252,0.96)";
          }
          return (
            <div key={`${row.rowId}-${column.name}`} className="flex min-w-0 items-center border-r border-slate-100 px-4 py-2 text-sm last:border-r-0" style={style} title={String(row.cells[column.originalIndex] ?? "")}>
              {renderGridCell(column, row.cells[column.originalIndex], row.cells, resolvedColumns, { compact: true })}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm ring-1 ring-slate-950/[0.03]" style={outerStyle}>
      {toolbar && !isStatic ? (
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
        {selectionColumnVisible ? (
          <div className="sticky left-0 z-30 flex items-center justify-center border-r border-slate-200/80 bg-slate-100/95" style={{ width: SELECTION_WIDTH, minWidth: SELECTION_WIDTH }}>
            Sel
          </div>
        ) : null}
        {hasIndex ? (
          <div className="sticky z-20 flex items-center border-r border-slate-200/80 bg-slate-100/95 px-3 text-[11px] text-slate-500" style={{ width: INDEX_WIDTH, minWidth: INDEX_WIDTH, left: selectionColumnVisible ? SELECTION_WIDTH : 0 }}>
            Index
          </div>
        ) : null}
        {resolvedColumns.map((column) => {
          const isSorted = viewState.sorts.find((item) => item.column === column.name);
          const style: React.CSSProperties = { width: column.widthPx, minWidth: column.widthPx };
          if (column.pinned === "left") {
            style.position = "sticky";
            style.left = (column.leftOffset ?? 0) + (selectionColumnVisible ? SELECTION_WIDTH : 0) + readOnlyIndexColumn(hasIndex);
            style.zIndex = 20;
            style.background = "rgba(248, 250, 252, 0.98)";
          } else if (column.pinned === "right") {
            style.position = "sticky";
            style.right = column.rightOffset ?? 0;
            style.zIndex = 20;
            style.background = "rgba(248, 250, 252, 0.98)";
          }
          return (
            <div
              key={column.name}
              className="relative flex items-center gap-2 border-r border-slate-200/80 px-3 last:border-r-0"
              style={style}
              title={column.help ?? column.name}
              onClick={(event) => !isStatic && updateViewState((current) => ({ ...current, sorts: toggleGridSort(current.sorts, column.name, event.shiftKey) }))}
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
      </div>

      {!displayRows.length ? (
        <div className="p-4">
          <GridEmptyState message={placeholder || "No rows match the current view."} />
        </div>
      ) : (
        <div
          ref={parentRef}
          className="overflow-auto"
          style={{ height: containerHeight - HEADER_HEIGHT - (toolbar && !isStatic ? TOOLBAR_HEIGHT : 0) }}
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

      {!isStatic ? (
        <div className="flex flex-wrap items-center gap-2 border-t border-slate-200/80 bg-slate-50/90 px-3 py-2 text-xs text-slate-500">
          <Badge variant="outline" className="font-normal">{effectiveTotalRows.toLocaleString()} rows</Badge>
          <Badge variant="outline" className="font-normal">{resolvedColumns.length} columns</Badge>
          {isServerPaged && loadingWindow ? <span className="ml-2 text-sky-600">(loading window...)</span> : null}
          {truncated ? <span className="ml-2 text-amber-700">(preview truncated)</span> : null}
        </div>
      ) : null}
    </div>
  );
};

export const Table: React.FC<NodeComponentProps> = ({ nodeId, props, sendEvent }) => {
  return <DataFrame nodeId={nodeId} props={{ ...props, static: true, toolbar: false, downloadable: false, persistView: false }} sendEvent={sendEvent} />;
};
