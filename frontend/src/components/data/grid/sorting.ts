import type { GridRowModel, GridSort } from "./types";

function sortKey(value: any): [number, any] {
  if (value === null || value === undefined) return [1, ""];
  if (typeof value === "boolean") return [0, value ? 1 : 0];
  if (typeof value === "number") return [0, value];
  if (typeof value === "string") return [0, value.toLowerCase()];
  if (Array.isArray(value)) return [0, JSON.stringify(value)];
  if (typeof value === "object") return [0, JSON.stringify(value)];
  return [0, String(value).toLowerCase()];
}

export function toggleGridSort(current: GridSort[], column: string, multi: boolean): GridSort[] {
  const existing = current.find((item) => item.column === column);
  const nextDirection = !existing ? "asc" : existing.direction === "asc" ? "desc" : null;
  const base = multi ? current.filter((item) => item.column !== column) : [];
  if (!nextDirection) return base;
  return [...base, { column, direction: nextDirection }];
}

export function applyGridSorts(
  rows: GridRowModel[],
  sorts: GridSort[],
  columnIndexMap: Record<string, number>,
): GridRowModel[] {
  if (!sorts.length) return rows;
  const next = [...rows];
  next.sort((left, right) => {
    for (const sort of sorts) {
      const columnIndex = columnIndexMap[sort.column];
      if (typeof columnIndex !== "number") continue;
      const leftKey = sortKey(left.cells[columnIndex]);
      const rightKey = sortKey(right.cells[columnIndex]);
      const cmp = compareKeys(leftKey, rightKey);
      if (cmp !== 0) return sort.direction === "desc" ? -cmp : cmp;
    }
    return left.originalPosition - right.originalPosition;
  });
  return next;
}

function compareKeys(left: [number, any], right: [number, any]): number {
  if (left[0] !== right[0]) return left[0] - right[0];
  if (left[1] < right[1]) return -1;
  if (left[1] > right[1]) return 1;
  return 0;
}
