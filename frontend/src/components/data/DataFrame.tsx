import React, { useRef, useMemo } from "react";
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
}

const ROW_HEIGHT = 36;
const HEADER_HEIGHT = 40;
const DEFAULT_HEIGHT = 400;
const MIN_COL_WIDTH = 100;

export const DataFrame: React.FC<NodeComponentProps> = ({ props }) => {
  const {
    columns = [],
    rows = [],
    index,
    height,
    useContainerWidth = true,
  } = props as DataFrameProps;

  const parentRef = useRef<HTMLDivElement>(null);

  // Calculate column widths based on content
  const columnWidths = useMemo(() => {
    const widths: number[] = [];
    const hasIndex = index && index.length > 0;

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
      const sampleRows = rows.slice(0, 100);
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
  }, [columns, rows, index]);

  // Total width
  const totalWidth = columnWidths.reduce((sum, w) => sum + w, 0);

  // Container height
  const containerHeight = height ?? Math.min(DEFAULT_HEIGHT, HEADER_HEIGHT + rows.length * ROW_HEIGHT + 2);

  // Virtualizer for rows
  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 5,
  });

  const hasIndex = index && index.length > 0;

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
            className="flex items-center px-3 border-r border-gray-200 last:border-r-0 truncate"
            style={{
              width: columnWidths[hasIndex ? colIdx + 1 : colIdx],
              minWidth: columnWidths[hasIndex ? colIdx + 1 : colIdx],
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
            const rowData = rows[virtualRow.index];
            const rowIndex = index?.[virtualRow.index];

            return (
              <div
                key={virtualRow.index}
                className={`flex absolute top-0 left-0 w-full border-b border-gray-100 ${
                  virtualRow.index % 2 === 0 ? "bg-white" : "bg-gray-50/50"
                } hover:bg-blue-50/50 transition-colors`}
                style={{
                  height: `${virtualRow.size}px`,
                  transform: `translateY(${virtualRow.start}px)`,
                }}
              >
                {hasIndex && (
                  <div
                    className="flex items-center px-3 border-r border-gray-100 bg-gray-50/50 text-gray-500 text-xs font-mono"
                    style={{ width: columnWidths[0], minWidth: columnWidths[0] }}
                  >
                    {formatCell(rowIndex, "string")}
                  </div>
                )}
                {columns.map((col, colIdx) => (
                  <div
                    key={colIdx}
                    className="flex items-center px-3 border-r border-gray-100 last:border-r-0 text-sm truncate"
                    style={{
                      width: columnWidths[hasIndex ? colIdx + 1 : colIdx],
                      minWidth: columnWidths[hasIndex ? colIdx + 1 : colIdx],
                    }}
                    title={String(rowData[colIdx] ?? "")}
                  >
                    <CellValue value={rowData[colIdx]} type={col.type} />
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer with row count */}
      <div className="px-3 py-1.5 bg-gray-50 border-t border-gray-200 text-xs text-gray-500">
        {rows.length.toLocaleString()} rows × {columns.length} columns
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
