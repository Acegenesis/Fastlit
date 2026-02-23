import React, { useEffect, useMemo, useRef, useState } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import type { NodeComponentProps } from "../../registry/registry";

interface Column {
  name: string;
  type: string;
}

interface DataFrameProps {
  columns: Column[];
  rows: any[][];
  index?: any[];
  height?: number;
  useContainerWidth?: boolean;
  static?: boolean;
  totalRows?: number;
  truncated?: boolean;
  sourceId?: string;
  windowSize?: number;
  selectable?: boolean;
  selectionMode?: "single-row" | "multi-row";
  selectedRows?: number[];
}

const ROW_HEIGHT = 36;
const HEADER_HEIGHT = 40;
const DEFAULT_HEIGHT = 400;
const MIN_COL_WIDTH = 100;

export const DataFrame: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const {
    columns = [],
    rows = [],
    index,
    height,
    useContainerWidth = true,
    totalRows,
    truncated = false,
    sourceId,
    windowSize = 300,
    selectable = false,
    selectionMode = "multi-row",
    selectedRows = [],
  } = props as DataFrameProps;

  const parentRef = useRef<HTMLDivElement>(null);
  const [serverOffset, setServerOffset] = useState(0);
  const [serverRows, setServerRows] = useState<any[][]>(rows);
  const [serverIndex, setServerIndex] = useState<any[] | undefined>(index);
  const [loadingWindow, setLoadingWindow] = useState(false);
  const [selectedRowPositions, setSelectedRowPositions] = useState<number[]>(
    Array.isArray(selectedRows) ? selectedRows : []
  );
  const fetchAbortRef = useRef<AbortController | null>(null);
  const isServerPaged = !!sourceId && (totalRows ?? rows.length) > rows.length;
  const isSelectable = !!selectable;
  const isMultiRowSelection = selectionMode !== "single-row";
  const selectionColumnVisible = isSelectable && isMultiRowSelection;

  const selectedSet = useMemo(
    () => new Set(selectedRowPositions),
    [selectedRowPositions]
  );

  useEffect(() => {
    setSelectedRowPositions(Array.isArray(selectedRows) ? selectedRows : []);
  }, [nodeId, selectedRows]);

  useEffect(() => {
    if (!isServerPaged) {
      setServerOffset(0);
      setServerRows(rows);
      setServerIndex(index);
      return;
    }
    setServerOffset(0);
    setServerRows(rows);
    setServerIndex(index);
  }, [isServerPaged, rows, index, sourceId]);

  // Calculate column widths based on content
  const columnWidths = useMemo(() => {
    const widths: number[] = [];
    const hasIndex = index && index.length > 0;
    if (selectionColumnVisible) {
      widths.push(44);
    }

    // Index column width
    if (hasIndex) {
      const maxIndexLen = Math.max(
        5, // minimum
        ...index.map((v) => String(v ?? "").length)
      );
      widths.push(Math.max(MIN_COL_WIDTH * 0.6, maxIndexLen * 10));
    }

    // Data columns
    for (let colIdx = 0; colIdx < columns.length; colIdx++) {
      const col = columns[colIdx];
      let maxLen = col.name.length;

      // Sample first 100 rows for width calculation
      const sampleRows = (isServerPaged ? serverRows : rows).slice(0, 100);
      for (const row of sampleRows) {
        const cellValue = row[colIdx];
        const cellStr = formatCell(cellValue, col.type);
        maxLen = Math.max(maxLen, cellStr.length);
      }

      // Estimate width: ~8px per char + padding
      const estimatedWidth = Math.min(300, Math.max(MIN_COL_WIDTH, maxLen * 9 + 24));
      widths.push(estimatedWidth);
    }

    return widths;
  }, [columns, rows, index, isServerPaged, serverRows, selectionColumnVisible]);

  // Total width
  const totalWidth = columnWidths.reduce((sum, w) => sum + w, 0);

  // Container height
  const effectiveRowCount = isServerPaged
    ? (typeof totalRows === "number" ? totalRows : rows.length)
    : rows.length;
  const containerHeight = height ?? Math.min(DEFAULT_HEIGHT, HEADER_HEIGHT + effectiveRowCount * ROW_HEIGHT + 2);

  // Virtualizer for rows
  const rowVirtualizer = useVirtualizer({
    count: effectiveRowCount,
    getScrollElement: () => parentRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 5,
  });

  const hasIndex = (isServerPaged ? serverIndex : index) && (isServerPaged ? serverIndex : index)!.length > 0;

  const emitSelection = (rowsToSelect: number[]) => {
    const normalized = Array.from(new Set(rowsToSelect))
      .filter((n) => Number.isInteger(n) && n >= 0)
      .sort((a, b) => a - b);
    setSelectedRowPositions(normalized);
    sendEvent(nodeId, normalized);
  };

  const toggleRowSelection = (rowPosition: number) => {
    if (!isSelectable) return;
    if (isMultiRowSelection) {
      const next = selectedSet.has(rowPosition)
        ? selectedRowPositions.filter((p) => p !== rowPosition)
        : [...selectedRowPositions, rowPosition];
      emitSelection(next);
      return;
    }
    emitSelection([rowPosition]);
  };

  useEffect(() => {
    if (!isServerPaged || !sourceId) return;
    const virtualItems = rowVirtualizer.getVirtualItems();
    if (virtualItems.length === 0) return;

    const first = virtualItems[0]!.index;
    const last = virtualItems[virtualItems.length - 1]!.index;
    const needStart = Math.max(0, first - Math.floor(windowSize * 0.5));
    const needEnd = Math.min(effectiveRowCount, last + Math.floor(windowSize * 1.5));
    const haveStart = serverOffset;
    const haveEnd = serverOffset + serverRows.length;

    if (needStart >= haveStart && needEnd <= haveEnd) {
      return;
    }

    const fetchOffset = needStart;
    const fetchLimit = Math.max(windowSize, needEnd - needStart);
    fetchAbortRef.current?.abort();
    const controller = new AbortController();
    fetchAbortRef.current = controller;
    setLoadingWindow(true);
    fetch(
      `/_fastlit/dataframe/${encodeURIComponent(sourceId)}?offset=${fetchOffset}&limit=${fetchLimit}`,
      { signal: controller.signal }
    )
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((payload) => {
        setServerOffset(payload.offset ?? fetchOffset);
        setServerRows(Array.isArray(payload.rows) ? payload.rows : []);
        setServerIndex(Array.isArray(payload.index) ? payload.index : undefined);
      })
      .catch(() => undefined)
      .finally(() => {
        if (!controller.signal.aborted) setLoadingWindow(false);
      });
  }, [isServerPaged, sourceId, rowVirtualizer, serverOffset, serverRows.length, effectiveRowCount, windowSize]);

  if (columns.length === 0) {
    return (
      <div className="text-gray-400 text-sm italic p-4 border border-gray-200 rounded">
        Empty DataFrame
      </div>
    );
  }

  return (
    <div
      className={`border border-gray-200 rounded-lg overflow-hidden bg-white ${
        useContainerWidth ? "w-full" : ""
      }`}
      style={{ maxWidth: useContainerWidth ? "100%" : totalWidth + 2 }}
    >
      {/* Header */}
      <div
        className="flex bg-gray-50 border-b border-gray-200 font-medium text-sm text-gray-700"
        style={{ height: HEADER_HEIGHT }}
      >
        {selectionColumnVisible && (
          <div
            className="flex items-center justify-center px-2 border-r border-gray-200 bg-gray-100 text-gray-500 text-xs"
            style={{ width: columnWidths[0], minWidth: columnWidths[0] }}
          >
            Sel
          </div>
        )}
        {hasIndex && (
          <div
            className="flex items-center px-3 border-r border-gray-200 bg-gray-100 text-gray-500 text-xs"
            style={{
              width: columnWidths[selectionColumnVisible ? 1 : 0],
              minWidth: columnWidths[selectionColumnVisible ? 1 : 0],
            }}
          >
            #
          </div>
        )}
        {columns.map((col, colIdx) => (
          <div
            key={col.name}
            className="flex items-center px-3 border-r border-gray-200 last:border-r-0 truncate"
            style={{
              width: columnWidths[colIdx + (selectionColumnVisible ? 1 : 0) + (hasIndex ? 1 : 0)],
              minWidth: columnWidths[colIdx + (selectionColumnVisible ? 1 : 0) + (hasIndex ? 1 : 0)],
            }}
            title={col.name}
          >
            {col.name}
          </div>
        ))}
      </div>

      {/* Virtualized rows */}
      <div
        ref={parentRef}
        className="overflow-auto"
        style={{ height: containerHeight - HEADER_HEIGHT }}
      >
        <div
          style={{
            height: `${rowVirtualizer.getTotalSize()}px`,
            width: totalWidth,
            position: "relative",
          }}
        >
          {rowVirtualizer.getVirtualItems().map((virtualRow) => {
            const rowPosition = virtualRow.index;
            const rowData = isServerPaged
              ? serverRows[virtualRow.index - serverOffset]
              : rows[virtualRow.index];
            const rowIndex = isServerPaged
              ? serverIndex?.[virtualRow.index - serverOffset]
              : index?.[virtualRow.index];
            const isSelected = selectedSet.has(rowPosition);
            const baseBg = isSelected
              ? "bg-blue-50 dark:bg-blue-900/20"
              : (virtualRow.index % 2 === 0 ? "bg-white" : "bg-gray-50/50");
            const colOffset = (selectionColumnVisible ? 1 : 0) + (hasIndex ? 1 : 0);

            return (
              <div
                key={virtualRow.index}
                className={`flex absolute top-0 left-0 w-full border-b border-gray-100 ${baseBg} ${
                  isSelectable ? "cursor-pointer" : ""
                } hover:bg-blue-50/50 transition-colors`}
                style={{
                  height: `${virtualRow.size}px`,
                  transform: `translateY(${virtualRow.start}px)`,
                }}
                onClick={() => toggleRowSelection(rowPosition)}
              >
                {selectionColumnVisible && (
                  <div
                    className="flex items-center justify-center px-2 border-r border-gray-100 bg-gray-50/50"
                    style={{ width: columnWidths[0], minWidth: columnWidths[0] }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleRowSelection(rowPosition)}
                      className="h-4 w-4 cursor-pointer"
                    />
                  </div>
                )}
                {hasIndex && (
                  <div
                    className="flex items-center px-3 border-r border-gray-100 bg-gray-50/50 text-gray-500 text-xs font-mono"
                    style={{
                      width: columnWidths[selectionColumnVisible ? 1 : 0],
                      minWidth: columnWidths[selectionColumnVisible ? 1 : 0],
                    }}
                  >
                    {formatCell(rowIndex, "string")}
                  </div>
                )}
                {columns.map((col, colIdx) => (
                  <div
                    key={colIdx}
                    className="flex items-center px-3 border-r border-gray-100 last:border-r-0 text-sm truncate"
                    style={{
                      width: columnWidths[colIdx + colOffset],
                      minWidth: columnWidths[colIdx + colOffset],
                    }}
                    title={String(rowData?.[colIdx] ?? "")}
                  >
                    <CellValue value={rowData?.[colIdx]} type={col.type} />
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer with row count */}
      <div className="px-3 py-1.5 bg-gray-50 border-t border-gray-200 text-xs text-gray-500">
        {(typeof totalRows === "number" ? totalRows : rows.length).toLocaleString()} rows x {columns.length} columns
        {isServerPaged && loadingWindow && <span className="ml-2 text-blue-600">(loading window...)</span>}
        {truncated && (
          <span className="ml-2 text-amber-700">
            (showing first {rows.length.toLocaleString()} rows)
          </span>
        )}
      </div>
    </div>
  );
};

// Cell value renderer with type-specific formatting
const CellValue: React.FC<{ value: any; type: string }> = ({ value, type }) => {
  if (value === null || value === undefined) {
    return <span className="text-gray-400 italic">null</span>;
  }

  const formatted = formatCell(value, type);

  // Type-specific styling
  if (type === "integer" || type === "number") {
    return <span className="font-mono text-right w-full">{formatted}</span>;
  }

  if (type === "boolean") {
    return (
      <span className={value ? "text-green-600" : "text-red-600"}>
        {formatted}
      </span>
    );
  }

  if (type === "datetime" || type === "date") {
    return <span className="font-mono text-gray-600">{formatted}</span>;
  }

  return <span>{formatted}</span>;
};

// Format cell value based on type
function formatCell(value: any, type: string): string {
  if (value === null || value === undefined) {
    return "";
  }

  if (type === "number" || type === "integer") {
    if (typeof value === "number") {
      // Format numbers with reasonable precision
      if (Number.isInteger(value)) {
        return value.toLocaleString();
      }
      return value.toLocaleString(undefined, {
        minimumFractionDigits: 0,
        maximumFractionDigits: 4,
      });
    }
  }

  if (type === "boolean") {
    return value ? "true" : "false";
  }

  if (type === "datetime" || type === "date") {
    // Handle ISO strings
    if (typeof value === "string" && value.includes("T")) {
      try {
        const date = new Date(value);
        if (!isNaN(date.getTime())) {
          return date.toLocaleString();
        }
      } catch {
        // Fall through to string
      }
    }
  }

  return String(value);
}

// Static table (non-virtualized, for small data)
export const Table: React.FC<NodeComponentProps> = ({ props }) => {
  const { columns = [], rows = [] } = props as DataFrameProps;

  if (columns.length === 0 || rows.length === 0) {
    return (
      <div className="text-gray-400 text-sm italic p-4 border border-gray-200 rounded">
        Empty table
      </div>
    );
  }

  return (
    <div className="overflow-x-auto border border-gray-200 rounded-lg">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col) => (
              <th
                key={col.name}
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {col.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {rows.map((row, rowIdx) => (
            <tr key={rowIdx} className="hover:bg-gray-50">
              {columns.map((col, colIdx) => (
                <td
                  key={colIdx}
                  className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap"
                >
                  <CellValue value={row[colIdx]} type={col.type} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
