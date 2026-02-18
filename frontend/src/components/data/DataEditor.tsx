import React, { useRef, useMemo, useState, useCallback } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import type { NodeComponentProps } from "../../registry/registry";

interface Column {
  name: string;
  type: string;
}

interface DataEditorProps {
  columns: Column[];
  rows: any[][];
  index?: any[];
  height?: number;
  width?: number;
  useContainerWidth?: boolean;
  editable?: boolean;
  numRows?: "fixed" | "dynamic";
  disabledColumns?: string[];
  columnConfig?: Record<string, any>;
  rerunOnChange?: boolean;
}

const ROW_HEIGHT = 36;
const HEADER_HEIGHT = 40;
const DEFAULT_HEIGHT = 400;
const MIN_COL_WIDTH = 100;

export const DataEditor: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const {
    columns = [],
    rows: initialRows = [],
    index,
    height,
    useContainerWidth = true,
    numRows = "fixed",
    disabledColumns = [],
    rerunOnChange = false,
  } = props as DataEditorProps;

  const parentRef = useRef<HTMLDivElement>(null);

  // Local state for edited data
  const [rows, setRows] = useState<any[][]>(initialRows);
  const [editingCell, setEditingCell] = useState<{
    row: number;
    col: number;
  } | null>(null);
  // Buffered value during editing — only committed to rows on blur/Enter/Tab
  const [editValue, setEditValue] = useState<string>("");

  // Calculate column widths
  const columnWidths = useMemo(() => {
    const widths: number[] = [];
    const hasIndex = index && index.length > 0;

    if (hasIndex) {
      const maxIndexLen = Math.max(
        5,
        ...index.map((v) => String(v ?? "").length)
      );
      widths.push(Math.max(MIN_COL_WIDTH * 0.6, maxIndexLen * 10));
    }

    for (let colIdx = 0; colIdx < columns.length; colIdx++) {
      const col = columns[colIdx];
      let maxLen = col.name.length;
      const sampleRows = rows.slice(0, 100);
      for (const row of sampleRows) {
        const cellValue = row[colIdx];
        maxLen = Math.max(maxLen, String(cellValue ?? "").length);
      }
      const estimatedWidth = Math.min(
        300,
        Math.max(MIN_COL_WIDTH, maxLen * 9 + 24)
      );
      widths.push(estimatedWidth);
    }

    return widths;
  }, [columns, rows, index]);

  const totalWidth = columnWidths.reduce((sum, w) => sum + w, 0);
  const containerHeight =
    height ?? Math.min(DEFAULT_HEIGHT, HEADER_HEIGHT + rows.length * ROW_HEIGHT + 2);

  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 5,
  });

  const hasIndex = index && index.length > 0;

  // Handle cell edit
  const handleCellChange = useCallback(
    (rowIdx: number, colIdx: number, value: any) => {
      const newRows = [...rows];
      newRows[rowIdx] = [...newRows[rowIdx]];
      newRows[rowIdx][colIdx] = value;
      setRows(newRows);

      // Send update to server; rerun if on_change is set
      sendEvent(nodeId, { rows: newRows }, { noRerun: !rerunOnChange });
    },
    [rows, nodeId, sendEvent, rerunOnChange]
  );

  // Handle cell click to start editing — initializes the edit buffer
  const handleCellClick = useCallback(
    (rowIdx: number, colIdx: number, colName: string) => {
      if (disabledColumns.includes(colName)) return;
      setEditingCell({ row: rowIdx, col: colIdx });
      setEditValue(String(rows[rowIdx]?.[colIdx] ?? ""));
    },
    [disabledColumns, rows]
  );

  // Handle blur to finish editing
  const handleBlur = useCallback(() => {
    setEditingCell(null);
    setEditValue("");
  }, []);

  // Add row (for dynamic mode)
  const handleAddRow = useCallback(() => {
    const newRow = columns.map(() => "");
    const newRows = [...rows, newRow];
    setRows(newRows);
    sendEvent(nodeId, { rows: newRows }, { noRerun: !rerunOnChange });
  }, [columns, rows, nodeId, sendEvent, rerunOnChange]);

  // Delete row
  const handleDeleteRow = useCallback(
    (rowIdx: number) => {
      const newRows = rows.filter((_, i) => i !== rowIdx);
      setRows(newRows);
      sendEvent(nodeId, { rows: newRows }, { noRerun: !rerunOnChange });
    },
    [rows, nodeId, sendEvent, rerunOnChange]
  );

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
        {hasIndex && (
          <div
            className="flex items-center px-3 border-r border-gray-200 bg-gray-100 text-gray-500 text-xs"
            style={{ width: columnWidths[0], minWidth: columnWidths[0] }}
          >
            #
          </div>
        )}
        {columns.map((col, colIdx) => (
          <div
            key={col.name}
            className={`flex items-center px-3 border-r border-gray-200 last:border-r-0 truncate ${
              disabledColumns.includes(col.name) ? "text-gray-400" : ""
            }`}
            style={{
              width: columnWidths[hasIndex ? colIdx + 1 : colIdx],
              minWidth: columnWidths[hasIndex ? colIdx + 1 : colIdx],
            }}
            title={col.name}
          >
            {col.name}
            {!disabledColumns.includes(col.name) && (
              <span className="ml-1 text-blue-500 text-xs">✎</span>
            )}
          </div>
        ))}
        {numRows === "dynamic" && (
          <div className="flex items-center px-2 bg-gray-100" style={{ width: 40 }}>
            {/* Actions column header */}
          </div>
        )}
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
            width: totalWidth + (numRows === "dynamic" ? 40 : 0),
            position: "relative",
          }}
        >
          {rowVirtualizer.getVirtualItems().map((virtualRow) => {
            const rowData = rows[virtualRow.index];
            const rowIndex = index?.[virtualRow.index];

            return (
              <div
                key={virtualRow.index}
                className={`flex absolute top-0 left-0 w-full border-b border-gray-100 ${
                  virtualRow.index % 2 === 0 ? "bg-white" : "bg-gray-50/50"
                }`}
                style={{
                  height: `${virtualRow.size}px`,
                  transform: `translateY(${virtualRow.start}px)`,
                }}
              >
                {hasIndex && (
                  <div
                    className="flex items-center px-3 border-r border-gray-100 bg-gray-50/50 text-gray-500 text-xs font-mono"
                    style={{
                      width: columnWidths[0],
                      minWidth: columnWidths[0],
                    }}
                  >
                    {String(rowIndex ?? virtualRow.index)}
                  </div>
                )}
                {columns.map((col, colIdx) => {
                  const isEditing =
                    editingCell?.row === virtualRow.index &&
                    editingCell?.col === colIdx;
                  const isDisabled = disabledColumns.includes(col.name);

                  return (
                    <div
                      key={colIdx}
                      className={`flex items-center border-r border-gray-100 last:border-r-0 text-sm ${
                        isDisabled
                          ? "bg-gray-50 text-gray-400"
                          : "cursor-pointer hover:bg-blue-50"
                      }`}
                      style={{
                        width: columnWidths[hasIndex ? colIdx + 1 : colIdx],
                        minWidth: columnWidths[hasIndex ? colIdx + 1 : colIdx],
                      }}
                      onClick={() =>
                        handleCellClick(virtualRow.index, colIdx, col.name)
                      }
                    >
                      {/* E1: boolean → native checkbox; E2: date/datetime → date picker */}
                      {col.type === "boolean" ? (
                        <div className="px-3 flex items-center">
                          <input
                            type="checkbox"
                            checked={!!rowData[colIdx]}
                            disabled={isDisabled}
                            onChange={(e) =>
                              handleCellChange(virtualRow.index, colIdx, e.target.checked)
                            }
                            className="w-4 h-4 accent-blue-500 cursor-pointer"
                          />
                        </div>
                      ) : col.type === "date" || col.type === "datetime" ? (
                        isEditing ? (
                          <input
                            type={col.type === "datetime" ? "datetime-local" : "date"}
                            className="w-full h-full px-3 py-1 border-2 border-blue-500 outline-none bg-white text-sm"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            onBlur={(e) => {
                              const committed = e.target.validity.valid ? editValue : "";
                              handleCellChange(virtualRow.index, colIdx, committed);
                              handleBlur();
                            }}
                            autoFocus
                          />
                        ) : (
                          <span className="px-3 truncate">
                            {formatCell(rowData[colIdx], col.type)}
                          </span>
                        )
                      ) : isEditing ? (
                        <input
                          type={
                            col.type === "number" || col.type === "integer"
                              ? "number"
                              : "text"
                          }
                          className="w-full h-full px-3 py-1 border-2 border-blue-500 outline-none bg-white"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          onBlur={() => {
                            const committed =
                              col.type === "number" || col.type === "integer"
                                ? parseFloat(editValue) || 0
                                : editValue;
                            handleCellChange(virtualRow.index, colIdx, committed);
                            handleBlur();
                          }}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === "Tab") {
                              e.preventDefault();
                              const committed =
                                col.type === "number" || col.type === "integer"
                                  ? parseFloat(editValue) || 0
                                  : editValue;
                              handleCellChange(virtualRow.index, colIdx, committed);
                              handleBlur();
                            } else if (e.key === "Escape") {
                              handleBlur();
                            }
                          }}
                          autoFocus
                        />
                      ) : (
                        <span className="px-3 truncate">
                          {formatCell(rowData[colIdx], col.type)}
                        </span>
                      )}
                    </div>
                  );
                })}
                {numRows === "dynamic" && (
                  <div
                    className="flex items-center justify-center"
                    style={{ width: 40 }}
                  >
                    <button
                      onClick={() => handleDeleteRow(virtualRow.index)}
                      className="text-red-400 hover:text-red-600 p-1"
                      title="Delete row"
                    >
                      ✕
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-gray-50 border-t border-gray-200 text-xs text-gray-500">
        <span>
          {rows.length.toLocaleString()} rows × {columns.length} columns
        </span>
        {numRows === "dynamic" && (
          <button
            onClick={handleAddRow}
            className="px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-xs"
          >
            + Add row
          </button>
        )}
      </div>
    </div>
  );
};

function formatCell(value: any, type: string): string {
  if (value === null || value === undefined) {
    return "";
  }

  if (type === "number" || type === "integer") {
    if (typeof value === "number") {
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

  return String(value);
}
