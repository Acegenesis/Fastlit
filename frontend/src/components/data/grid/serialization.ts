import type { GridFilter, GridSort, GridRowModel, GridResolvedColumn } from "./types";

export function encodeGridSorts(sorts: GridSort[]): string {
  return JSON.stringify(sorts);
}

export function encodeGridFilters(filters: GridFilter[]): string {
  return JSON.stringify(filters.map(({ column, op, value }) => ({ column, op, value })));
}

export function normalizeListLikeValue(value: any): any[] {
  if (Array.isArray(value)) return value;
  if (value === null || value === undefined) return [];
  if (typeof value !== "string") return [value];

  const trimmed = value.trim();
  if (!trimmed) return [];

  try {
    const parsed = JSON.parse(trimmed);
    if (Array.isArray(parsed)) return parsed;
  } catch {
    // Fall back to looser parsing below.
  }

  if (trimmed.startsWith("[") && trimmed.endsWith("]")) {
    return trimmed
      .slice(1, -1)
      .split(",")
      .map((item) => item.trim().replace(/^['\"]|['\"]$/g, ""))
      .filter(Boolean);
  }

  return [trimmed];
}

export function safeJsonStringify(value: any): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export function csvEscape(value: any): string {
  if (value === null || value === undefined) return "";
  const raw = Array.isArray(value) || (value && typeof value === "object")
    ? JSON.stringify(value)
    : String(value);
  const escaped = raw.replace(/"/g, '""');
  return /[",\n]/.test(escaped) ? `"${escaped}"` : escaped;
}

export function buildCsv(
  columns: GridResolvedColumn[],
  rows: GridRowModel[],
): string {
  const header = columns.map((column) => csvEscape(column.label || column.name)).join(",");
  const lines = rows.map((row) =>
    columns.map((column) => csvEscape(row.cells[column.originalIndex])).join(",")
  );
  return [header, ...lines].join("\n");
}

export function triggerCsvDownload(filename: string, csv: string) {
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const href = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(href);
}

export function defaultCsvFileName(prefix: string): string {
  const now = new Date();
  const stamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, "0")}${String(now.getDate()).padStart(2, "0")}-${String(now.getHours()).padStart(2, "0")}${String(now.getMinutes()).padStart(2, "0")}${String(now.getSeconds()).padStart(2, "0")}`;
  return `${prefix}-${stamp}.csv`;
}
