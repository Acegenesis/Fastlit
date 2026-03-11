import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { tableFromIPC } from "apache-arrow";
import type { NodeComponentProps } from "../../registry/registry";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { GridToolbar } from "./grid/GridToolbar";
import { GridEmptyState } from "./grid/GridEmptyState";
import { normalizeGridColumnType } from "./grid/columnTypes";
import { renderGridCell } from "./grid/renderers";
import { useGridColumns } from "./grid/useGridColumns";
import { useGridViewState } from "./grid/useGridViewState";
import { applyGridSearchAndFilters } from "./grid/filtering";
import { applyGridSorts, toggleGridSort } from "./grid/sorting";
import { buildCsv, defaultCsvFileName, encodeGridFilters, encodeGridSorts, triggerCsvDownload } from "./grid/serialization";
import { useGridVirtualRows } from "./grid/useGridVirtualRows";
import type { GridColumn, GridPinned, GridResolvedColumn, GridRowModel } from "./grid/types";
import { cn } from "@/lib/utils";
import { useResolvedPropText } from "../../context/WidgetStore";

const DEFAULT_ROW_HEIGHT = 48;
const HEADER_HEIGHT = 48;
const TOOLBAR_HEIGHT = 49;
const FOOTER_HEIGHT = 38;
const PAGINATION_HEIGHT = 44;
const DEFAULT_HEIGHT = 420;
const SELECTION_WIDTH = 48;
const INDEX_WIDTH = 72;
const ARROW_MEDIA_TYPE = "application/vnd.apache.arrow.stream";
const ARROW_INDEX_COLUMN = "__fastlit_index__";
const ARROW_POSITION_COLUMN = "__fastlit_position__";

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
  validateMessage?: string | null;
  validateOn?: string | null;
  options?: string[];
  displayText?: string | null;
  format?: string | null;
  yMin?: number | null;
  yMax?: number | null;
}

interface SelectedCell {
  row: number;
  column: string;
}

interface DataFrameProps {
  columns: Column[];
  rows: any[][];
  arrowData?: string;
  dataTransport?: string;
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
  selectionMode?: string | string[];
  selectedRows?: number[];
  selectedColumns?: string[];
  selectedCells?: SelectedCell[];
  columnConfig?: Record<string, ColumnConfig>;
  indexConfig?: ColumnConfig;
  indexLabel?: string;
  columnOrder?: string[];
  rowHeight?: number;
  placeholder?: string;
  toolbar?: boolean;
  showSearch?: boolean;
  showFilters?: boolean;
  showColumnManager?: boolean;
  showResetView?: boolean;
  showFooterSummary?: boolean;
  downloadable?: boolean;
  persistView?: boolean;
  pagination?: boolean | string;
  paginationMode?: string;
  pageSize?: number;
  exportMaxRows?: number;
  debugDataframe?: boolean;
}

interface DecodedFramePayload {
  rows: any[][];
  index?: any[];
  positions?: number[];
}

interface ServerFramePayload extends DecodedFramePayload {
  offset: number;
  limit: number;
  totalRows: number;
  schemaVersion?: string;
}

interface CachedPageEntry {
  page: number;
  payload: ServerFramePayload;
  touchedAt: number;
}

const ROW_SELECTION_MODES = new Set(["single-row", "multi-row"]);
const COLUMN_SELECTION_MODES = new Set(["single-column", "multi-column"]);
const CELL_SELECTION_MODES = new Set(["single-cell", "multi-cell"]);

function normalizeSelectionModes(selectionMode: string | string[] | undefined): string[] {
  const raw = Array.isArray(selectionMode) ? selectionMode : selectionMode ? [selectionMode] : [];
  return raw.filter(Boolean);
}

function normalizeSelectedCells(value: unknown): SelectedCell[] {
  if (!Array.isArray(value)) return [];
  const seen = new Set<string>();
  const cells: SelectedCell[] = [];
  for (const item of value) {
    const row = typeof (item as SelectedCell)?.row === "number" ? (item as SelectedCell).row : NaN;
    const column = typeof (item as SelectedCell)?.column === "string" ? (item as SelectedCell).column : "";
    if (!Number.isInteger(row) || row < 0 || !column) continue;
    const key = `${row}:${column}`;
    if (seen.has(key)) continue;
    seen.add(key);
    cells.push({ row, column });
  }
  cells.sort((left, right) => left.row - right.row || left.column.localeCompare(right.column));
  return cells;
}

function normalizeSelectionPayload(payload: {
  rows?: number[];
  columns?: string[];
  cells?: SelectedCell[];
}, selectionModes: string[]) {
  const rowMode = selectionModes.find((mode) => ROW_SELECTION_MODES.has(mode));
  const columnMode = selectionModes.find((mode) => COLUMN_SELECTION_MODES.has(mode));
  const cellMode = selectionModes.find((mode) => CELL_SELECTION_MODES.has(mode));

  const rows = Array.from(new Set((payload.rows ?? []).filter((value) => Number.isInteger(value) && value >= 0))).sort((left, right) => left - right);
  const columns = Array.from(new Set((payload.columns ?? []).map((value) => String(value)).filter(Boolean)));
  const cells = normalizeSelectedCells(payload.cells ?? []);

  return {
    rows: rowMode === "single-row" ? rows.slice(0, 1) : rowMode ? rows : [],
    columns: columnMode === "single-column" ? columns.slice(0, 1) : columnMode ? columns : [],
    cells: cellMode === "single-cell" ? cells.slice(0, 1) : cellMode ? cells : [],
  };
}

function schemaSignature(columns: GridColumn[]): string {
  return JSON.stringify(columns.map((column) => ({ name: column.name, type: column.type })));
}

function normalizeColumns(columns: Column[], columnConfig: Record<string, ColumnConfig> = {}): GridColumn[] {
  return columns.map((column) => {
    const cfg = columnConfig[column.name] ?? {};
    return {
      name: column.name,
      type: normalizeGridColumnType(String(cfg.type ?? column.type ?? "text")),
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
      validateMessage: cfg.validateMessage,
      validateOn: cfg.validateOn,
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

function decodeBase64ToUint8Array(value: string): Uint8Array {
  const binary = window.atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let idx = 0; idx < binary.length; idx += 1) {
    bytes[idx] = binary.charCodeAt(idx);
  }
  return bytes;
}

function normalizeArrowValue(value: any): any {
  if (value === null || value === undefined) return null;
  if (typeof value === "bigint") {
    const asNumber = Number(value);
    return Number.isSafeInteger(asNumber) ? asNumber : value.toString();
  }
  if (value instanceof Date) return value.toISOString();
  if (value instanceof Uint8Array) return Array.from(value);
  if (Array.isArray(value)) return value.map((item) => normalizeArrowValue(item));
  if (value instanceof Map) {
    return Object.fromEntries(
      Array.from(value.entries()).map(([key, item]) => [String(key), normalizeArrowValue(item)])
    );
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, any>).map(([key, item]) => [key, normalizeArrowValue(item)])
    );
  }
  return value;
}

function decodeArrowPayload(buffer: Uint8Array, columns: Column[]): DecodedFramePayload {
  const table = tableFromIPC(buffer);
  const rowCount = table.numRows ?? 0;
  const vectors = new Map<string, any>();
  table.schema.fields.forEach((field, index) => {
    vectors.set(field.name, table.getChildAt(index));
  });

  const rows = Array.from({ length: rowCount }, (_, rowIndex) =>
    columns.map((column) => normalizeArrowValue(vectors.get(column.name)?.get(rowIndex)))
  );

  const indexVector = vectors.get(ARROW_INDEX_COLUMN);
  const positionVector = vectors.get(ARROW_POSITION_COLUMN);
  const indexValues = indexVector
    ? Array.from({ length: rowCount }, (_, rowIndex) => normalizeArrowValue(indexVector.get(rowIndex)))
    : undefined;
  const positions = positionVector
    ? Array.from({ length: rowCount }, (_, rowIndex) => {
        const raw = normalizeArrowValue(positionVector.get(rowIndex));
        const numeric = Number(raw);
        return Number.isFinite(numeric) ? numeric : rowIndex;
      })
    : undefined;

  return {
    rows,
    index: indexValues,
    positions,
  };
}

function parseHeaderNumber(value: string | null, fallback: number): number {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

async function parseDataframeResponse(
  response: Response,
  columns: Column[],
  fallbackOffset: number,
  fallbackLimit: number
): Promise<ServerFramePayload> {
  const contentType = response.headers.get("content-type")?.toLowerCase() ?? "";
  if (contentType.includes(ARROW_MEDIA_TYPE)) {
    const payload = decodeArrowPayload(new Uint8Array(await response.arrayBuffer()), columns);
    return {
      offset: parseHeaderNumber(response.headers.get("X-Fastlit-Offset"), fallbackOffset),
      limit: parseHeaderNumber(response.headers.get("X-Fastlit-Limit"), fallbackLimit),
      totalRows: parseHeaderNumber(response.headers.get("X-Fastlit-Total-Rows"), payload.rows.length),
      rows: payload.rows,
      index: payload.index,
      positions: payload.positions,
      schemaVersion: response.headers.get("X-Fastlit-Schema-Version") ?? undefined,
    };
  }
  return response.json() as Promise<ServerFramePayload>;
}

function resolveGridHeight(
  height: number | string | undefined,
  rowCount: number,
  rowHeight: number,
  showToolbar: boolean,
  showFooter: boolean,
  showPagination: boolean
): number {
  if (typeof height === "number" && Number.isFinite(height)) return height;
  const chrome =
    HEADER_HEIGHT +
    (showToolbar ? TOOLBAR_HEIGHT : 0) +
    (showFooter ? FOOTER_HEIGHT : 0) +
    (showPagination ? PAGINATION_HEIGHT : 0) +
    2;
  const content = chrome + Math.max(rowHeight, rowCount * rowHeight);
  return Math.min(DEFAULT_HEIGHT, Math.max(chrome + rowHeight, content));
}

function resolveRowHeight(rowHeight: number | null | undefined): number {
  return typeof rowHeight === "number" && Number.isFinite(rowHeight) && rowHeight > 0
    ? rowHeight
    : DEFAULT_ROW_HEIGHT;
}

function resolveOuterStyle(width: number | string | undefined, useContainerWidth: boolean | undefined): React.CSSProperties {
  if (useContainerWidth || width === "stretch" || width === undefined) {
    return { width: "100%", maxWidth: "100%", minWidth: 0 };
  }
  if (typeof width === "number" && Number.isFinite(width)) {
    return { width, maxWidth: "100%", minWidth: 0 };
  }
  return { width: "auto", maxWidth: "100%", minWidth: 0 };
}

function readOnlyIndexColumn(hasIndex: boolean) {
  return hasIndex ? INDEX_WIDTH : 0;
}

export const DataFrame: React.FC<NodeComponentProps> = ({ nodeId, props, sendEvent }) => {
  const {
    columns = [],
    rows = [],
    arrowData,
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
    selectedColumns = [],
    selectedCells = [],
    columnConfig = {},
    indexConfig = {},
    indexLabel,
    columnOrder = [],
    rowHeight,
    toolbar = !isStatic,
    showSearch = true,
    showFilters = true,
    showColumnManager = true,
    showResetView = true,
    showFooterSummary = true,
    downloadable = !isStatic,
    persistView = true,
    pagination = false,
    paginationMode,
    pageSize = 25,
    exportMaxRows = 100000,
    debugDataframe = false,
  } = props as DataFrameProps;
  const resolvedPlaceholder = useResolvedPropText(props as Record<string, any>, "placeholder");
  const isArrowDebug = nodeId.startsWith("k:arrow_demo_df_");
  const resolvedPaginationMode = useMemo(() => {
    const raw = String(paginationMode ?? (typeof pagination === "string" ? pagination : "text"))
      .trim()
      .toLowerCase();
    if (raw === "text" || raw === "number" || raw === "icon") return raw;
    return "text";
  }, [pagination, paginationMode]);
  const paginationEnabled = (typeof pagination === "boolean" ? pagination : true) && !isStatic;
  const showTextPagination = paginationEnabled && resolvedPaginationMode === "text";
  const showNumberPagination = paginationEnabled && resolvedPaginationMode === "number";
  const showIconPagination = paginationEnabled && resolvedPaginationMode === "icon";
  const resolvedPageSize = Number.isFinite(Number(pageSize))
    ? Math.max(1, Math.floor(Number(pageSize)))
    : 25;

  const decodedPreview = useMemo(() => {
    if (!arrowData) return null;
    try {
      return decodeArrowPayload(decodeBase64ToUint8Array(arrowData), columns);
    } catch {
      return null;
    }
  }, [arrowData, columns]);

  const initialRows = decodedPreview?.rows ?? rows;
  const initialIndex = decodedPreview?.index ?? index;
  const initialPositions = decodedPreview?.positions ?? positions;

  const parentRef = useRef<HTMLDivElement>(null);
  const headerScrollRef = useRef<HTMLDivElement>(null);
  const scrollPersistTimerRef = useRef<number | null>(null);
  const resizeStateRef = useRef<{ columnName: string; startX: number; startWidth: number } | null>(null);
  const [serverOffset, setServerOffset] = useState(0);
  const [serverRows, setServerRows] = useState<any[][]>(initialRows);
  const [serverIndex, setServerIndex] = useState<any[] | undefined>(initialIndex);
  const [serverPositions, setServerPositions] = useState<number[] | undefined>(initialPositions);
  const [serverTotalRows, setServerTotalRows] = useState<number>(
    typeof totalRows === "number" ? totalRows : initialRows.length
  );
  const [loadingWindow, setLoadingWindow] = useState(false);
  const [selectedRowPositions, setSelectedRowPositions] = useState<number[]>(Array.isArray(selectedRows) ? [...selectedRows] : []);
  const [selectedColumnNames, setSelectedColumnNames] = useState<string[]>(Array.isArray(selectedColumns) ? [...selectedColumns] : []);
  const [selectedCellValues, setSelectedCellValues] = useState<SelectedCell[]>(normalizeSelectedCells(selectedCells));
  const [currentPage, setCurrentPage] = useState(1);
  const [pageCache, setPageCache] = useState<Record<number, CachedPageEntry>>({});
  const [pageError, setPageError] = useState<string | null>(null);
  const [serverSchemaVersion, setServerSchemaVersion] = useState<string | undefined>(undefined);
  const [columnSelectionAnchor, setColumnSelectionAnchor] = useState<string | null>(null);
  const [cellSelectionAnchor, setCellSelectionAnchor] = useState<SelectedCell | null>(null);
  const fetchAbortRef = useRef<AbortController | null>(null);
  const pageControllersRef = useRef<Map<number, AbortController>>(new Map());
  const inFlightPagesRef = useRef<Set<string>>(new Set());
  const lastQueryKeyRef = useRef<string | null>(null);
  const currentPageRef = useRef(1);
  const didMountServerPagingRef = useRef(false);
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
  const effectiveSearch = showSearch ? viewState.search : "";
  const effectiveFilters = showFilters ? viewState.filters : [];
  const toolbarVisible = toolbar && (showSearch || showFilters || showColumnManager || showResetView || downloadable);

  const selectionModes = useMemo(() => normalizeSelectionModes(selectionMode), [selectionMode]);
  const rowSelectionMode = selectionModes.find((mode) => ROW_SELECTION_MODES.has(mode));
  const columnSelectionMode = selectionModes.find((mode) => COLUMN_SELECTION_MODES.has(mode));
  const cellSelectionMode = selectionModes.find((mode) => CELL_SELECTION_MODES.has(mode));
  const allowsRowSelection = selectable && !!rowSelectionMode;
  const allowsColumnSelection = selectable && !!columnSelectionMode;
  const allowsCellSelection = selectable && !!cellSelectionMode;
  const selectionColumnVisible = allowsRowSelection && rowSelectionMode !== "single-row";
  const isServerPaged = !!sourceId && (typeof totalRows === "number" ? totalRows : initialRows.length) > initialRows.length;
  const footerVisible = !isStatic && (showFooterSummary || truncated || (isServerPaged && loadingWindow));
  const effectiveIndex = isServerPaged ? serverIndex : initialIndex;
  const hasIndex = Array.isArray(effectiveIndex) && effectiveIndex.length > 0;
  const effectiveRowHeight = resolveRowHeight(rowHeight);

  useEffect(() => {
    if (isArrowDebug) {
      console.log("[Fastlit][ArrowDF:reset-window]", {
        nodeId,
        sourceId,
        totalRows,
        initialRows: initialRows.length,
      });
    }
    setServerOffset(0);
    setServerRows(initialRows);
    setServerIndex(initialIndex);
    setServerPositions(initialPositions);
    setServerTotalRows(typeof totalRows === "number" ? totalRows : initialRows.length);
    setPageCache({});
    setPageError(null);
    setServerSchemaVersion(undefined);
  }, [initialIndex, initialPositions, initialRows, isArrowDebug, nodeId, sourceId, totalRows]);

  useEffect(() => {
    setSelectedRowPositions(Array.isArray(selectedRows) ? [...selectedRows] : []);
  }, [selectedRows]);

  useEffect(() => {
    setSelectedColumnNames(Array.isArray(selectedColumns) ? [...selectedColumns] : []);
  }, [selectedColumns]);

  useEffect(() => {
    setSelectedCellValues(normalizeSelectedCells(selectedCells));
  }, [selectedCells]);

  useEffect(() => {
    currentPageRef.current = currentPage;
  }, [currentPage]);

  const baseRowModels = useMemo(
    () => normalizeRows(initialRows, initialIndex, initialPositions),
    [initialIndex, initialPositions, initialRows]
  );
  const currentWindowModels = useMemo(
    () => normalizeRows(serverRows, serverIndex, serverPositions),
    [serverIndex, serverPositions, serverRows]
  );

  const { resolvedColumns, columnIndexMap, totalWidth } = useGridColumns({
    columns: baseColumns,
    rows: isServerPaged ? serverRows : initialRows,
    viewState,
  });

  const filteredLocalRows = useMemo(() => {
    if (isServerPaged) return currentWindowModels;
    const searched = applyGridSearchAndFilters(baseRowModels, effectiveSearch, effectiveFilters, columnIndexMap);
    return applyGridSorts(searched, viewState.sorts, columnIndexMap);
  }, [baseRowModels, columnIndexMap, currentWindowModels, effectiveFilters, effectiveSearch, isServerPaged, viewState.sorts]);

  const localTotalRows = filteredLocalRows.length;
  const totalRowsForPagination = isServerPaged ? serverTotalRows : localTotalRows;
  const totalPages = paginationEnabled ? Math.max(1, Math.ceil(totalRowsForPagination / resolvedPageSize)) : 1;

  useEffect(() => {
    if (!paginationEnabled) return;
    setCurrentPage((previous) => Math.min(Math.max(1, previous), totalPages));
  }, [paginationEnabled, totalPages]);

  const localPageRows = useMemo(() => {
    if (!paginationEnabled || isServerPaged) return filteredLocalRows;
    const pageOffset = (currentPage - 1) * resolvedPageSize;
    return filteredLocalRows.slice(pageOffset, pageOffset + resolvedPageSize);
  }, [currentPage, filteredLocalRows, isServerPaged, paginationEnabled, resolvedPageSize]);

  const displayRows = isServerPaged
    ? currentWindowModels
    : paginationEnabled
      ? localPageRows
      : filteredLocalRows;
  const effectiveTotalRows = isServerPaged ? serverTotalRows : localTotalRows;
  const virtualRowCount = paginationEnabled
    ? displayRows.length
    : isServerPaged
      ? effectiveTotalRows
      : displayRows.length;
  const paginationStartRow = paginationEnabled && effectiveTotalRows > 0
    ? (currentPage - 1) * resolvedPageSize + 1
    : 0;
  const paginationEndRow = paginationEnabled
    ? Math.min(effectiveTotalRows, currentPage * resolvedPageSize)
    : 0;
  const paginationItems = useMemo(() => {
    if (!paginationEnabled) return [] as Array<number | "ellipsis" | "empty">;
    const slotCount = 7;

    if (totalPages <= slotCount) {
      const pages = Array.from({ length: totalPages }, (_, idx) => idx + 1) as Array<number | "ellipsis" | "empty">;
      while (pages.length < slotCount) pages.push("empty");
      return pages;
    }

    if (currentPage <= 4) {
      return [1, 2, 3, 4, 5, "ellipsis", totalPages];
    }
    if (currentPage >= totalPages - 3) {
      return [1, "ellipsis", totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
    }
    return [1, "ellipsis", currentPage - 1, currentPage, currentPage + 1, "ellipsis", totalPages];
  }, [currentPage, paginationEnabled, totalPages]);
  const outerStyle = resolveOuterStyle(width, useContainerWidth);
  const containerHeight = resolveGridHeight(
    height,
    Math.max(displayRows.length, 1),
    effectiveRowHeight,
    toolbarVisible && !isStatic,
    footerVisible,
    paginationEnabled
  );
  const rowVirtualizer = useGridVirtualRows({ rowCount: virtualRowCount, parentRef, rowHeight: effectiveRowHeight });
  const virtualItems = rowVirtualizer.getVirtualItems();
  const virtualRangeKey = virtualItems.length
    ? `${virtualItems[0]!.index}:${virtualItems[virtualItems.length - 1]!.index}`
    : "empty";
  const shouldVirtualize = !paginationEnabled && (isServerPaged || displayRows.length > 100);
  const selectedSet = useMemo(() => new Set(selectedRowPositions), [selectedRowPositions]);
  const selectedColumnSet = useMemo(() => new Set(selectedColumnNames), [selectedColumnNames]);
  const selectedCellSet = useMemo(
    () => new Set(selectedCellValues.map((cell) => `${cell.row}:${cell.column}`)),
    [selectedCellValues]
  );

  useEffect(() => {
    if (!persistView || !parentRef.current) return;
    parentRef.current.scrollTop = viewState.scrollTop;
    parentRef.current.scrollLeft = viewState.scrollLeft;
    if (headerScrollRef.current) {
      headerScrollRef.current.scrollLeft = viewState.scrollLeft;
    }
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
    params.set("search", effectiveSearch);
    params.set("sort", encodeGridSorts(viewState.sorts));
    params.set("filters", encodeGridFilters(effectiveFilters));
    return params.toString();
  }, [effectiveFilters, effectiveSearch, viewState.sorts]);

  const viewQueryKey = useMemo(
    () => `${sourceId ?? ""}::${resolvedPageSize}::${queryString}`,
    [queryString, resolvedPageSize, sourceId]
  );

  useEffect(() => {
    if (!paginationEnabled) return;
    if (lastQueryKeyRef.current === viewQueryKey) return;
    lastQueryKeyRef.current = viewQueryKey;
    setCurrentPage(1);
    setPageCache({});
    setPageError(null);
    for (const controller of pageControllersRef.current.values()) {
      controller.abort();
    }
    pageControllersRef.current.clear();
    inFlightPagesRef.current.clear();
  }, [paginationEnabled, viewQueryKey]);

  const requestKey = useMemo(
    () => `${sourceId ?? ""}::${windowSize}::${resolvedPageSize}::${queryString}`,
    [queryString, resolvedPageSize, sourceId, windowSize]
  );
  const [activeRequestKey, setActiveRequestKey] = useState(requestKey);

  const applyServerPayload = useCallback((payload: ServerFramePayload) => {
    setServerOffset(payload.offset ?? 0);
    setServerRows(Array.isArray(payload.rows) ? payload.rows : []);
    setServerIndex(Array.isArray(payload.index) ? payload.index : undefined);
    setServerPositions(Array.isArray(payload.positions) ? payload.positions.map((value: any) => Number(value)) : undefined);
    setServerTotalRows(typeof payload.totalRows === "number" ? payload.totalRows : 0);
    setServerSchemaVersion(payload.schemaVersion ?? undefined);
  }, []);

  const updateCachedPage = useCallback((page: number, payload: ServerFramePayload) => {
    setPageCache((current) => {
      const now = Date.now();
      const next: Record<number, CachedPageEntry> = {
        ...current,
        [page]: {
          page,
          payload,
          touchedAt: now,
        },
      };
      const entries = Object.values(next).sort((left, right) => right.touchedAt - left.touchedAt);
      const trimmed = entries.slice(0, 5);
      return Object.fromEntries(trimmed.map((entry) => [entry.page, entry]));
    });
  }, []);

  const fetchServerPage = useCallback(async (page: number, prefetch = false) => {
    if (!sourceId || !isServerPaged || !paginationEnabled) return null;
    const pageKey = `${viewQueryKey}::${page}`;
    if (inFlightPagesRef.current.has(pageKey)) return null;
    const cached = pageCache[page];
    if (cached) {
      updateCachedPage(page, cached.payload);
      return cached.payload;
    }

    const pageOffset = Math.max(0, (page - 1) * resolvedPageSize);
    const controller = new AbortController();
    pageControllersRef.current.set(page, controller);
    inFlightPagesRef.current.add(pageKey);
    if (!prefetch) {
      setLoadingWindow(true);
      setPageError(null);
    }

    try {
      const response = await fetch(
        `/_fastlit/dataframe/${encodeURIComponent(sourceId)}?offset=${pageOffset}&limit=${resolvedPageSize}&format=arrow&${queryString}`,
        { signal: controller.signal }
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await parseDataframeResponse(response, columns, pageOffset, resolvedPageSize);
      updateCachedPage(page, payload);
      if (!prefetch && currentPageRef.current === page) {
        applyServerPayload(payload);
      }
      return payload;
    } catch (error) {
      if (!controller.signal.aborted && !prefetch) {
        const message = error instanceof Error ? error.message : String(error);
        setPageError(message);
      }
      return null;
    } finally {
      pageControllersRef.current.delete(page);
      inFlightPagesRef.current.delete(pageKey);
      if (!prefetch && !controller.signal.aborted) {
        setLoadingWindow(false);
      }
    }
  }, [
    applyServerPayload,
    columns,
    isServerPaged,
    pageCache,
    paginationEnabled,
    queryString,
    resolvedPageSize,
    sourceId,
    updateCachedPage,
    viewQueryKey,
  ]);

  useEffect(() => {
    if (!isArrowDebug) return;
    console.log("[Fastlit][ArrowDF:state]", {
      nodeId,
      sourceId,
      isServerPaged,
      totalRows,
      serverTotalRows,
      initialRows: initialRows.length,
      serverRows: serverRows.length,
      requestKey,
      activeRequestKey,
    });
  }, [
    activeRequestKey,
    initialRows.length,
    isArrowDebug,
    isServerPaged,
    nodeId,
    requestKey,
    serverRows.length,
    serverTotalRows,
    sourceId,
    totalRows,
  ]);

  useEffect(() => {
    if (paginationEnabled) return;
    if (!isServerPaged || !sourceId) return;
    if (activeRequestKey !== requestKey) return;
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
    if (isArrowDebug) {
      console.log("[Fastlit][ArrowDF:fetch-window]", {
        nodeId,
        sourceId,
        fetchOffset,
        fetchLimit,
        requestKey,
        needStart,
        needEnd,
        haveStart,
        haveEnd,
      });
    }
    fetch(`/_fastlit/dataframe/${encodeURIComponent(sourceId)}?offset=${fetchOffset}&limit=${fetchLimit}&format=arrow&${queryString}`, {
      signal: controller.signal,
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return parseDataframeResponse(res, columns, fetchOffset, fetchLimit);
      })
      .then((payload) => {
        if (isArrowDebug) {
          console.log("[Fastlit][ArrowDF:fetch-window:response]", {
            nodeId,
            sourceId,
            offset: payload.offset,
            totalRows: payload.totalRows,
            rows: Array.isArray(payload.rows) ? payload.rows.length : 0,
          });
        }
        setServerOffset(payload.offset ?? fetchOffset);
        setServerRows(Array.isArray(payload.rows) ? payload.rows : []);
        setServerIndex(Array.isArray(payload.index) ? payload.index : undefined);
        setServerPositions(Array.isArray(payload.positions) ? payload.positions.map((value: any) => Number(value)) : undefined);
        setServerTotalRows(typeof payload.totalRows === "number" ? payload.totalRows : 0);
      })
      .catch((error) => {
        if (isArrowDebug) {
          console.log("[Fastlit][ArrowDF:fetch-window:error]", {
            nodeId,
            sourceId,
            error: error instanceof Error ? error.message : String(error),
          });
        }
        return undefined;
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingWindow(false);
      });
  }, [activeRequestKey, columns, effectiveTotalRows, isArrowDebug, isServerPaged, nodeId, paginationEnabled, queryString, requestKey, serverOffset, serverRows.length, sourceId, virtualItems, virtualRangeKey, windowSize]);

  useEffect(() => {
    if (paginationEnabled) return;
    if (!isServerPaged || !sourceId) return;
    if (!didMountServerPagingRef.current) {
      didMountServerPagingRef.current = true;
      return;
    }
    fetchAbortRef.current?.abort();
    const controller = new AbortController();
    fetchAbortRef.current = controller;
    setActiveRequestKey("");
    setLoadingWindow(true);
    if (isArrowDebug) {
      console.log("[Fastlit][ArrowDF:refetch-initial-window]", {
        nodeId,
        sourceId,
        windowSize,
        requestKey,
      });
    }
    fetch(`/_fastlit/dataframe/${encodeURIComponent(sourceId)}?offset=0&limit=${windowSize}&format=arrow&${queryString}`, {
      signal: controller.signal,
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return parseDataframeResponse(res, columns, 0, windowSize);
      })
      .then((payload) => {
        if (isArrowDebug) {
          console.log("[Fastlit][ArrowDF:refetch-initial-window:response]", {
            nodeId,
            sourceId,
            offset: payload.offset,
            totalRows: payload.totalRows,
            rows: Array.isArray(payload.rows) ? payload.rows.length : 0,
          });
        }
        setServerOffset(payload.offset ?? 0);
        setServerRows(Array.isArray(payload.rows) ? payload.rows : []);
        setServerIndex(Array.isArray(payload.index) ? payload.index : undefined);
        setServerPositions(Array.isArray(payload.positions) ? payload.positions.map((value: any) => Number(value)) : undefined);
        setServerTotalRows(typeof payload.totalRows === "number" ? payload.totalRows : 0);
      })
      .catch((error) => {
        if (isArrowDebug) {
          console.log("[Fastlit][ArrowDF:refetch-initial-window:error]", {
            nodeId,
            sourceId,
            error: error instanceof Error ? error.message : String(error),
          });
        }
        return undefined;
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setActiveRequestKey(requestKey);
          setLoadingWindow(false);
        }
      });
  }, [columns, isArrowDebug, isServerPaged, nodeId, paginationEnabled, queryString, requestKey, sourceId, windowSize]);

  useEffect(() => {
    if (!paginationEnabled || !isServerPaged || !sourceId) return;
    const cached = pageCache[currentPage];
    if (cached) {
      applyServerPayload(cached.payload);
      updateCachedPage(currentPage, cached.payload);
    } else {
      void fetchServerPage(currentPage);
    }

    const neighbors = [currentPage - 1, currentPage + 1].filter((page) => page >= 1 && page <= totalPages);
    for (const neighbor of neighbors) {
      if (pageCache[neighbor]) {
        updateCachedPage(neighbor, pageCache[neighbor]!.payload);
        continue;
      }
      void fetchServerPage(neighbor, true);
    }
  }, [
    applyServerPayload,
    currentPage,
    fetchServerPage,
    isServerPaged,
    pageCache,
    paginationEnabled,
    sourceId,
    totalPages,
    updateCachedPage,
  ]);

  const emitSelection = useCallback((payload: {
    rows?: number[];
    columns?: string[];
    cells?: SelectedCell[];
  }) => {
    const normalized = normalizeSelectionPayload(payload, selectionModes);
    setSelectedRowPositions(normalized.rows);
    setSelectedColumnNames(normalized.columns);
    setSelectedCellValues(normalized.cells);
    sendEvent(nodeId, {
      selection: {
        rows: normalized.rows,
        columns: normalized.columns,
        cells: normalized.cells,
      },
    });
  }, [nodeId, selectionModes, sendEvent]);

  const toggleRowSelection = useCallback((rowPosition: number) => {
    if (!allowsRowSelection) return;
    if (rowSelectionMode === "single-row") {
      emitSelection({
        rows: [rowPosition],
        columns: selectedColumnNames,
        cells: selectedCellValues,
      });
      return;
    }
    const next = selectedSet.has(rowPosition)
      ? selectedRowPositions.filter((value) => value !== rowPosition)
      : [...selectedRowPositions, rowPosition];
    emitSelection({
      rows: next,
      columns: selectedColumnNames,
      cells: selectedCellValues,
    });
  }, [
    allowsRowSelection,
    emitSelection,
    rowSelectionMode,
    selectedCellValues,
    selectedColumnNames,
    selectedRowPositions,
    selectedSet,
  ]);

  const toggleColumnSelection = useCallback((columnName: string, event: React.MouseEvent<HTMLDivElement>) => {
    if (!allowsColumnSelection) return;
    if (columnSelectionMode === "single-column") {
      setColumnSelectionAnchor(columnName);
      emitSelection({
        rows: selectedRowPositions,
        columns: [columnName],
        cells: selectedCellValues,
      });
      return;
    }
    const orderedNames = resolvedColumns.map((column) => column.name);
    let next = [...selectedColumnNames];
    if (event.shiftKey && columnSelectionAnchor) {
      const start = orderedNames.indexOf(columnSelectionAnchor);
      const end = orderedNames.indexOf(columnName);
      if (start >= 0 && end >= 0) {
        const [from, to] = start <= end ? [start, end] : [end, start];
        next = orderedNames.slice(from, to + 1);
      }
    } else if (event.metaKey || event.ctrlKey) {
      next = selectedColumnSet.has(columnName)
        ? selectedColumnNames.filter((value) => value !== columnName)
        : [...selectedColumnNames, columnName];
    } else {
      next = [columnName];
    }
    setColumnSelectionAnchor(columnName);
    emitSelection({
      rows: selectedRowPositions,
      columns: next,
      cells: selectedCellValues,
    });
  }, [
    allowsColumnSelection,
    columnSelectionAnchor,
    columnSelectionMode,
    emitSelection,
    resolvedColumns,
    selectedCellValues,
    selectedColumnNames,
    selectedColumnSet,
    selectedRowPositions,
  ]);

  const toggleCellSelection = useCallback((rowPosition: number, columnName: string, event: React.MouseEvent<HTMLDivElement>) => {
    if (!allowsCellSelection) return;
    const target: SelectedCell = { row: rowPosition, column: columnName };
    let next = [target];

    if (cellSelectionMode === "multi-cell" && event.shiftKey && cellSelectionAnchor) {
      const visiblePositions = displayRows.map((row) => row.originalPosition);
      const rowStart = visiblePositions.indexOf(cellSelectionAnchor.row);
      const rowEnd = visiblePositions.indexOf(rowPosition);
      const colStart = resolvedColumns.findIndex((column) => column.name === cellSelectionAnchor.column);
      const colEnd = resolvedColumns.findIndex((column) => column.name === columnName);
      if (rowStart >= 0 && rowEnd >= 0 && colStart >= 0 && colEnd >= 0) {
        const [fromRow, toRow] = rowStart <= rowEnd ? [rowStart, rowEnd] : [rowEnd, rowStart];
        const [fromCol, toCol] = colStart <= colEnd ? [colStart, colEnd] : [colEnd, colStart];
        next = [];
        for (let rowIdx = fromRow; rowIdx <= toRow; rowIdx += 1) {
          const currentRow = displayRows[rowIdx];
          if (!currentRow) continue;
          for (let colIdx = fromCol; colIdx <= toCol; colIdx += 1) {
            const currentColumn = resolvedColumns[colIdx];
            if (!currentColumn) continue;
            next.push({ row: currentRow.originalPosition, column: currentColumn.name });
          }
        }
      }
    } else if (cellSelectionMode === "multi-cell" && (event.metaKey || event.ctrlKey)) {
      const key = `${rowPosition}:${columnName}`;
      next = selectedCellSet.has(key)
        ? selectedCellValues.filter((cell) => `${cell.row}:${cell.column}` !== key)
        : [...selectedCellValues, target];
    }

    setCellSelectionAnchor(target);
    emitSelection({
      rows: selectedRowPositions,
      columns: selectedColumnNames,
      cells: next,
    });
  }, [
    allowsCellSelection,
    cellSelectionAnchor,
    cellSelectionMode,
    displayRows,
    emitSelection,
    resolvedColumns,
    selectedCellSet,
    selectedCellValues,
    selectedColumnNames,
    selectedRowPositions,
  ]);

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

  const sortSignature = JSON.stringify(viewState.sorts);
  const previousSortSignatureRef = useRef(sortSignature);
  useEffect(() => {
    if (previousSortSignatureRef.current === sortSignature) return;
    previousSortSignatureRef.current = sortSignature;
    if (!selectable) return;
    if (!allowsRowSelection && !allowsCellSelection) return;
    emitSelection({
      rows: [],
      columns: selectedColumnNames,
      cells: [],
    });
  }, [allowsCellSelection, allowsRowSelection, emitSelection, selectable, selectedColumnNames, sortSignature]);

  const handleDownload = useCallback(async () => {
    if (!displayRows.length && !isServerPaged) return;
    if (!isServerPaged || !sourceId) {
      triggerCsvDownload(defaultCsvFileName(isStatic ? "fastlit-table" : "fastlit-dataframe"), buildCsv(resolvedColumns, displayRows));
      return;
    }
    if (serverTotalRows > exportMaxRows) {
      toast("Export limit reached", {
        description: `The current query has ${serverTotalRows.toLocaleString()} rows. Fastlit export is capped at ${exportMaxRows.toLocaleString()} rows.`,
      });
      return;
    }

    const collected: GridRowModel[] = [];
    let offset = 0;
    const chunkSize = 5000;
    while (offset < serverTotalRows) {
      const response = await fetch(`/_fastlit/dataframe/${encodeURIComponent(sourceId)}?offset=${offset}&limit=${chunkSize}&format=arrow&${queryString}`);
      if (!response.ok) break;
      const payload = await parseDataframeResponse(response, columns, offset, chunkSize);
      const rowsChunk = normalizeRows(payload.rows ?? [], payload.index, payload.positions);
      collected.push(...rowsChunk);
      offset += rowsChunk.length;
      if (!rowsChunk.length) break;
    }
    triggerCsvDownload(defaultCsvFileName(isStatic ? "fastlit-table" : "fastlit-dataframe"), buildCsv(resolvedColumns, collected));
  }, [columns, displayRows, exportMaxRows, isServerPaged, isStatic, queryString, resolvedColumns, serverTotalRows, sourceId]);

  if (!resolvedColumns.length) {
    return <GridEmptyState message={resolvedPlaceholder || (isStatic ? "Empty table" : "Empty DataFrame")} />;
  }

  const contentWidth = totalWidth + (selectionColumnVisible ? SELECTION_WIDTH : 0) + readOnlyIndexColumn(hasIndex);
  const resolveVirtualRowModel = useCallback((virtualIndex: number) => {
    if (!isServerPaged) {
      return displayRows[virtualIndex] ?? null;
    }
    const localIndex = virtualIndex - serverOffset;
    if (localIndex < 0 || localIndex >= currentWindowModels.length) {
      return null;
    }
    return currentWindowModels[localIndex] ?? null;
  }, [currentWindowModels, displayRows, isServerPaged, serverOffset]);

  const renderLoadingRow = (virtualIndex: number, layoutStyle?: React.CSSProperties) => (
    <div
      key={`loading-${virtualIndex}`}
      className={cn(
        "left-0 top-0 flex w-full border-b border-slate-100",
        virtualIndex % 2 === 0 ? "bg-white" : "bg-slate-50/60",
        shouldVirtualize && "absolute"
      )}
      style={layoutStyle}
    >
      {selectionColumnVisible ? (
        <div className="sticky left-0 z-20 border-r border-slate-100 bg-inherit" style={{ width: SELECTION_WIDTH, minWidth: SELECTION_WIDTH }} />
      ) : null}
      {hasIndex ? (
        <div
          className="sticky z-10 border-r border-slate-100 bg-inherit"
          style={{ width: INDEX_WIDTH, minWidth: INDEX_WIDTH, left: selectionColumnVisible ? SELECTION_WIDTH : 0 }}
        />
      ) : null}
      {resolvedColumns.map((column) => {
        const style: React.CSSProperties = { width: column.widthPx, minWidth: column.widthPx };
        if (column.pinned === "left") {
          style.position = "sticky";
          style.left = (column.leftOffset ?? 0) + (selectionColumnVisible ? SELECTION_WIDTH : 0) + readOnlyIndexColumn(hasIndex);
          style.zIndex = 10;
          style.background = virtualIndex % 2 === 0 ? "rgba(255,255,255,0.96)" : "rgba(248,250,252,0.96)";
        } else if (column.pinned === "right") {
          style.position = "sticky";
          style.right = column.rightOffset ?? 0;
          style.zIndex = 10;
          style.background = virtualIndex % 2 === 0 ? "rgba(255,255,255,0.96)" : "rgba(248,250,252,0.96)";
        }
        return (
          <div key={`loading-${virtualIndex}-${column.name}`} className="flex min-w-0 items-center border-r border-slate-100 px-4 py-2 last:border-r-0" style={style}>
            <div className="h-4 w-full animate-pulse rounded bg-slate-200/80" />
          </div>
        );
      })}
    </div>
  );

  const renderRow = (row: GridRowModel, rowIndex: number, layoutStyle?: React.CSSProperties) => {
    const isSelected = selectedSet.has(row.originalPosition);
    const background = isSelected ? "bg-sky-50" : rowIndex % 2 === 0 ? "bg-white" : "bg-slate-50/60";
    return (
      <div
        key={row.rowId}
        className={cn("left-0 top-0 flex w-full border-b border-slate-100", background, selectable && "cursor-pointer", shouldVirtualize && "absolute")}
        style={layoutStyle}
        onClick={() => {
          if (allowsCellSelection) return;
          toggleRowSelection(row.originalPosition);
        }}
      >
        {selectionColumnVisible ? (
          <div className="sticky left-0 z-20 flex items-center justify-center border-r border-slate-100 bg-inherit" style={{ width: SELECTION_WIDTH, minWidth: SELECTION_WIDTH }} onClick={(event) => event.stopPropagation()}>
            <Checkbox checked={isSelected} onCheckedChange={() => toggleRowSelection(row.originalPosition)} />
          </div>
        ) : null}
        {hasIndex ? (
          <div
            className="sticky z-10 flex items-center border-r border-slate-100 bg-inherit px-4 font-mono text-xs text-slate-500"
            style={{ width: INDEX_WIDTH, minWidth: INDEX_WIDTH, left: selectionColumnVisible ? SELECTION_WIDTH : 0 }}
            onClick={(event) => {
              event.stopPropagation();
              toggleRowSelection(row.originalPosition);
            }}
          >
            {String(row.indexValue ?? row.originalPosition)}
          </div>
        ) : null}
        {resolvedColumns.map((column) => {
          const cellKey = `${row.originalPosition}:${column.name}`;
          const isColumnSelected = selectedColumnSet.has(column.name);
          const isCellSelected = selectedCellSet.has(cellKey);
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
            <div
              key={`${row.rowId}-${column.name}`}
              className={cn(
                "flex min-w-0 items-center border-r border-slate-100 px-4 py-2 text-sm last:border-r-0",
                isCellSelected && "ring-1 ring-inset ring-sky-500 bg-sky-100/80",
                !isCellSelected && isColumnSelected && "bg-sky-50/80"
              )}
              style={style}
              title={String(row.cells[column.originalIndex] ?? "")}
              onClick={(event) => {
                event.stopPropagation();
                if (allowsCellSelection) {
                  toggleCellSelection(row.originalPosition, column.name, event);
                  return;
                }
                toggleRowSelection(row.originalPosition);
              }}
            >
              {renderGridCell(column, row.cells[column.originalIndex], row.cells, resolvedColumns, { compact: true, placeholder: resolvedPlaceholder })}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div role="grid" aria-rowcount={effectiveTotalRows} className="w-full min-w-0 overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm ring-1 ring-slate-950/[0.03]" style={outerStyle}>
      {toolbarVisible && !isStatic ? (
        <GridToolbar
          columns={baseColumns}
          viewState={viewState}
          downloadable={downloadable}
          showSearch={showSearch}
          showFilters={showFilters}
          showColumnManager={showColumnManager}
          showResetView={showResetView}
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

      <div ref={headerScrollRef} className="overflow-hidden">
        <div className="flex border-b border-slate-200/80 bg-slate-50/90 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500" style={{ height: HEADER_HEIGHT, width: contentWidth, minWidth: "100%" }}>
          {selectionColumnVisible ? (
            <div className="sticky left-0 z-30 flex items-center justify-center border-r border-slate-200/80 bg-slate-100/95" style={{ width: SELECTION_WIDTH, minWidth: SELECTION_WIDTH }}>
              Sel
            </div>
          ) : null}
          {hasIndex ? (
            <div className="sticky z-20 flex items-center border-r border-slate-200/80 bg-slate-100/95 px-3 text-[11px] text-slate-500" style={{ width: INDEX_WIDTH, minWidth: INDEX_WIDTH, left: selectionColumnVisible ? SELECTION_WIDTH : 0 }}>
              {indexLabel || indexConfig.label || "Index"}
            </div>
          ) : null}
          {resolvedColumns.map((column) => {
            const isSorted = viewState.sorts.find((item) => item.column === column.name);
            const isColumnSelected = selectedColumnSet.has(column.name);
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
                role="columnheader"
                aria-sort={isSorted ? (isSorted.direction === "asc" ? "ascending" : "descending") : "none"}
                className={cn(
                  "relative flex items-center gap-2 border-r border-slate-200/80 px-3 last:border-r-0",
                  isColumnSelected && "bg-sky-100/80 text-sky-700"
                )}
                style={style}
                title={column.help ?? column.name}
                onClick={(event) => {
                  if (allowsColumnSelection) {
                    toggleColumnSelection(column.name, event);
                    return;
                  }
                  if (!isStatic) {
                    updateViewState((current) => ({ ...current, sorts: toggleGridSort(current.sorts, column.name, event.shiftKey) }));
                  }
                }}
              >
                <span className="truncate">{column.label}</span>
                {isSorted ? (
                  <span className="text-[10px] text-sky-600">
                    {isSorted.direction === "asc" ? "ASC" : "DESC"} {viewState.sorts.findIndex((item) => item.column === column.name) + 1}
                  </span>
                ) : null}
                {column.resizable ? (
                  <div role="separator" aria-orientation="vertical" className="absolute right-0 top-0 h-full w-3 cursor-col-resize" onMouseDown={(event) => startResize(event, column)}>
                    <div className="absolute right-1 top-2 bottom-2 w-px rounded-full bg-slate-300 hover:bg-sky-500" />
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      </div>

      {!displayRows.length ? (
        <div className="p-4">
          <GridEmptyState message="No rows match the current view." />
        </div>
      ) : (
        <div
          ref={parentRef}
          className="overflow-auto"
          style={{
            height:
              containerHeight -
              HEADER_HEIGHT -
              (toolbarVisible && !isStatic ? TOOLBAR_HEIGHT : 0) -
              (footerVisible ? FOOTER_HEIGHT : 0) -
              (paginationEnabled ? PAGINATION_HEIGHT : 0),
          }}
          onScroll={(event) => {
            const target = event.currentTarget;
            if (headerScrollRef.current) {
              headerScrollRef.current.scrollLeft = target.scrollLeft;
            }
            persistScrollState(target.scrollTop, target.scrollLeft);
          }}
        >
          {shouldVirtualize ? (
          <div style={{ height: `${rowVirtualizer.getTotalSize()}px`, width: contentWidth, minWidth: "100%", position: "relative" }}>
              {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                const row = resolveVirtualRowModel(virtualRow.index);
                if (!row) {
                  return renderLoadingRow(virtualRow.index, {
                    height: `${virtualRow.size}px`,
                    transform: `translateY(${virtualRow.start}px)`,
                    position: "absolute",
                  });
                }
                return renderRow(row, virtualRow.index, {
                  height: `${virtualRow.size}px`,
                  transform: `translateY(${virtualRow.start}px)`,
                  position: "absolute",
                });
              })}
            </div>
          ) : (
            <div style={{ width: contentWidth, minWidth: "100%" }}>
              {displayRows.map((row, rowIndex) => renderRow(row, rowIndex))}
            </div>
          )}
        </div>
      )}

      {paginationEnabled ? (
        <div className="flex h-11 items-center justify-between border-t border-slate-200/80 bg-slate-50/90 px-3">
          <span className="text-xs text-slate-600">
            {paginationStartRow > 0
              ? `Rows ${paginationStartRow}-${paginationEndRow} of ${effectiveTotalRows.toLocaleString()}`
              : "Rows 0-0 of 0"}
          </span>
          <div className="flex items-center gap-2 rounded-lg border border-slate-200/90 bg-white/90 px-2 py-1 shadow-sm">
            <Badge variant="outline" className="font-normal">{`Page ${currentPage}/${totalPages}`}</Badge>
            {showTextPagination ? (
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious
                      href="#"
                      aria-disabled={currentPage <= 1}
                      tabIndex={currentPage <= 1 ? -1 : undefined}
                      className={cn(currentPage <= 1 && "pointer-events-none opacity-50")}
                      onClick={(event) => {
                        event.preventDefault();
                        if (currentPage <= 1) return;
                        setCurrentPage((previous) => Math.max(1, previous - 1));
                      }}
                    />
                  </PaginationItem>
                  <PaginationItem>
                    <PaginationNext
                      href="#"
                      aria-disabled={currentPage >= totalPages}
                      tabIndex={currentPage >= totalPages ? -1 : undefined}
                      className={cn(currentPage >= totalPages && "pointer-events-none opacity-50")}
                      onClick={(event) => {
                        event.preventDefault();
                        if (currentPage >= totalPages) return;
                        setCurrentPage((previous) => Math.min(totalPages, previous + 1));
                      }}
                    />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            ) : null}
            {showIconPagination ? (
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious
                      href="#"
                      aria-disabled={currentPage <= 1}
                      tabIndex={currentPage <= 1 ? -1 : undefined}
                      className={cn(
                        "h-9 w-9 p-0 [&>span]:sr-only",
                        currentPage <= 1 && "pointer-events-none opacity-50"
                      )}
                      onClick={(event) => {
                        event.preventDefault();
                        if (currentPage <= 1) return;
                        setCurrentPage((previous) => Math.max(1, previous - 1));
                      }}
                    />
                  </PaginationItem>
                  <PaginationItem>
                    <PaginationNext
                      href="#"
                      aria-disabled={currentPage >= totalPages}
                      tabIndex={currentPage >= totalPages ? -1 : undefined}
                      className={cn(
                        "h-9 w-9 p-0 [&>span]:sr-only",
                        currentPage >= totalPages && "pointer-events-none opacity-50"
                      )}
                      onClick={(event) => {
                        event.preventDefault();
                        if (currentPage >= totalPages) return;
                        setCurrentPage((previous) => Math.min(totalPages, previous + 1));
                      }}
                    />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            ) : null}
            {showNumberPagination ? (
              <div className="w-[320px]">
                <Pagination>
                  <PaginationContent className="grid w-full grid-cols-7 justify-items-center">
                {paginationItems.map((item, idx) => {
                  if (item === "empty") {
                    return (
                      <PaginationItem key={`empty-${idx}`} className="h-9 w-9" />
                    );
                  }
                  if (item === "ellipsis") {
                    return (
                      <PaginationItem key={`ellipsis-${idx}`}>
                        <PaginationEllipsis />
                      </PaginationItem>
                    );
                  }
                  const page = Number(item);
                  const isActive = page === currentPage;
                  return (
                    <PaginationItem key={`page-${item}`}>
                    <PaginationLink
                      key={`page-${item}`}
                      href="#"
                      isActive={isActive}
                      className={cn(
                        "h-9 w-9 min-w-9 p-0",
                        isActive ? "bg-slate-900 text-white hover:bg-slate-900" : "border border-slate-200"
                      )}
                      onClick={(event) => {
                        event.preventDefault();
                        setCurrentPage(page);
                      }}
                    >
                      {page}
                    </PaginationLink>
                    </PaginationItem>
                  );
                })}
                  </PaginationContent>
                </Pagination>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

      {pageError ? (
        <div className="border-t border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {`Data request failed: ${pageError}`}
        </div>
      ) : null}

      {footerVisible ? (
        <div className="flex flex-wrap items-center gap-2 border-t border-slate-200/80 bg-slate-50/90 px-3 py-2 text-xs text-slate-500">
          {showFooterSummary ? (
            <>
              <Badge variant="outline" className="font-normal">{effectiveTotalRows.toLocaleString()} rows</Badge>
              <Badge variant="outline" className="font-normal">{resolvedColumns.length} columns</Badge>
            </>
          ) : null}
          {isServerPaged && loadingWindow ? <span className="ml-2 text-sky-600">(loading window...)</span> : null}
          {truncated ? <span className="ml-2 text-amber-700">(preview truncated)</span> : null}
        </div>
      ) : null}

      {debugDataframe ? (
        <div className="border-t border-dashed border-slate-200 bg-slate-50/60 px-3 py-2 font-mono text-[11px] text-slate-600">
          {`query=${viewQueryKey} page=${currentPage}/${totalPages} cachePages=${Object.keys(pageCache).sort((left, right) => Number(left) - Number(right)).join(",") || "none"} source=${sourceId ?? "local"} schema=${serverSchemaVersion ?? "n/a"}`}
        </div>
      ) : null}
    </div>
  );
};

export const Table: React.FC<NodeComponentProps> = ({ nodeId, props, sendEvent }) => {
  return <DataFrame nodeId={nodeId} props={{ ...props, static: true, toolbar: false, downloadable: false, persistView: false }} sendEvent={sendEvent} />;
};
