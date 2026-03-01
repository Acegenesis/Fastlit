import { useMemo } from "react";
import type { GridColumn, GridResolvedColumn, GridViewState } from "./types";

const MIN_WIDTH = 110;

function resolveWidth(width: string | number | null | undefined, computed: number): number {
  if (typeof width === "number" && Number.isFinite(width)) return width;
  if (width === "small") return 96;
  if (width === "medium") return 160;
  if (width === "large") return 260;
  return computed;
}

export function useGridColumns({
  columns,
  rows,
  viewState,
}: {
  columns: GridColumn[];
  rows: any[][];
  viewState: GridViewState;
}) {
  return useMemo(() => {
    const byName = new Map(columns.map((column, index) => [column.name, { column, index }]));
    const orderedNames = viewState.columnOrder.length
      ? viewState.columnOrder.filter((name) => byName.has(name))
      : columns.map((column) => column.name);

    const hidden = new Set(viewState.hiddenColumns);
    const sampleRows = rows.slice(0, 50);
    const resolved: GridResolvedColumn[] = orderedNames
      .map((name) => {
        const match = byName.get(name);
        if (!match) return null;
        const { column, index } = match;
        if (hidden.has(column.name) || column.hidden) return null;
        let maxLen = (column.label || column.name).length;
        for (const row of sampleRows) {
          maxLen = Math.max(maxLen, String(row[index] ?? "").length);
        }
        const computedWidth = resolveWidth(column.width, Math.min(360, Math.max(MIN_WIDTH, maxLen * 8 + 40)));
        const manualWidth = viewState.manualWidths[column.name];
        const minWidth = Math.max(MIN_WIDTH, Number(column.minWidth ?? MIN_WIDTH));
        const maxWidth = Number.isFinite(Number(column.maxWidth)) && column.maxWidth !== null
          ? Number(column.maxWidth)
          : Number.POSITIVE_INFINITY;
        const widthPx = Math.min(maxWidth, Math.max(minWidth, manualWidth ?? computedWidth));
        const pinned = viewState.pinnedColumns[column.name] ?? column.pinned ?? null;
        return {
          ...column,
          originalIndex: index,
          widthPx,
          minWidth,
          maxWidth,
          pinned,
        } as GridResolvedColumn;
      })
      .filter(Boolean) as GridResolvedColumn[];

    const left = resolved.filter((column) => column.pinned === "left");
    const center = resolved.filter((column) => !column.pinned);
    const right = resolved.filter((column) => column.pinned === "right");
    const ordered = [...left, ...center, ...right];

    let leftOffset = 0;
    for (const column of ordered) {
      if (column.pinned === "left") {
        column.leftOffset = leftOffset;
        leftOffset += column.widthPx;
      }
    }

    let rightOffset = 0;
    for (let i = ordered.length - 1; i >= 0; i -= 1) {
      const column = ordered[i];
      if (column.pinned === "right") {
        column.rightOffset = rightOffset;
        rightOffset += column.widthPx;
      }
    }

    const columnIndexMap = Object.fromEntries(columns.map((column, index) => [column.name, index]));
    const totalWidth = ordered.reduce((sum, column) => sum + column.widthPx, 0);

    return {
      resolvedColumns: ordered,
      columnIndexMap,
      totalWidth,
    };
  }, [columns, rows, viewState]);
}
