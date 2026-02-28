import type { GridFilter, GridRowModel } from "./types";
import { normalizeListLikeValue, safeJsonStringify } from "./serialization";

export interface FilterOption {
  value: string;
  label: string;
}

export function searchText(value: any): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value.toLowerCase();
  if (typeof value === "number" || typeof value === "boolean") return String(value).toLowerCase();
  if (Array.isArray(value) || typeof value === "object") return safeJsonStringify(value).toLowerCase();
  return String(value).toLowerCase();
}

export function filterOptionsForType(type: string): FilterOption[] {
  switch (type) {
    case "number":
    case "integer":
    case "progress":
      return [
        { value: "equals", label: "Equals" },
        { value: "gt", label: ">" },
        { value: "gte", label: ">=" },
        { value: "lt", label: "<" },
        { value: "lte", label: "<=" },
        { value: "between", label: "Between" },
        { value: "is_empty", label: "Is empty" },
        { value: "not_empty", label: "Not empty" },
      ];
    case "boolean":
    case "checkbox":
      return [
        { value: "is_true", label: "Is true" },
        { value: "is_false", label: "Is false" },
        { value: "is_empty", label: "Is empty" },
      ];
    case "date":
    case "time":
    case "datetime":
      return [
        { value: "before", label: "Before" },
        { value: "on_or_before", label: "On or before" },
        { value: "after", label: "After" },
        { value: "on_or_after", label: "On or after" },
        { value: "between", label: "Between" },
        { value: "is_empty", label: "Is empty" },
        { value: "not_empty", label: "Not empty" },
      ];
    case "list":
    case "multiselect":
      return [
        { value: "contains_any", label: "Contains any" },
        { value: "contains_all", label: "Contains all" },
        { value: "is_empty", label: "Is empty" },
        { value: "not_empty", label: "Not empty" },
      ];
    default:
      return [
        { value: "contains", label: "Contains" },
        { value: "not_contains", label: "Does not contain" },
        { value: "equals", label: "Equals" },
        { value: "not_equals", label: "Not equals" },
        { value: "is_empty", label: "Is empty" },
        { value: "not_empty", label: "Not empty" },
      ];
  }
}

export function applyGridSearchAndFilters(
  rows: GridRowModel[],
  search: string,
  filters: GridFilter[],
  columnIndexMap: Record<string, number>,
): GridRowModel[] {
  const searchValue = search.trim().toLowerCase();
  let next = rows;
  if (searchValue) {
    next = next.filter((row) => row.cells.some((cell) => searchText(cell).includes(searchValue)));
  }
  if (!filters.length) return next;
  return next.filter((row) =>
    filters.every((filter) => {
      const columnIndex = columnIndexMap[filter.column];
      if (typeof columnIndex !== "number") return true;
      return matchesFilter(row.cells[columnIndex], filter.op, filter.value);
    })
  );
}

export function matchesFilter(value: any, op: string, filterValue: any): boolean {
  if (!op) return true;
  if (op === "is_empty") return isEmptyValue(value);
  if (op === "not_empty") return !isEmptyValue(value);
  if (op === "is_true") return value === true;
  if (op === "is_false") return value === false;

  if (op === "contains") return searchText(value).includes(searchText(filterValue));
  if (op === "not_contains") return !searchText(value).includes(searchText(filterValue));
  if (op === "equals") return searchText(value) === searchText(filterValue);
  if (op === "not_equals") return searchText(value) !== searchText(filterValue);

  if (["gt", "gte", "lt", "lte"].includes(op)) {
    const left = coerceNumber(value);
    const right = coerceNumber(filterValue);
    if (left === null || right === null) return false;
    if (op === "gt") return left > right;
    if (op === "gte") return left >= right;
    if (op === "lt") return left < right;
    return left <= right;
  }

  if (op === "between") {
    if (Array.isArray(filterValue) && filterValue.length === 2) {
      const leftNumber = coerceNumber(value);
      const lowNumber = coerceNumber(filterValue[0]);
      const highNumber = coerceNumber(filterValue[1]);
      if (leftNumber !== null && lowNumber !== null && highNumber !== null) {
        return leftNumber >= lowNumber && leftNumber <= highNumber;
      }
      const leftDate = coerceDate(value);
      const lowDate = coerceDate(filterValue[0]);
      const highDate = coerceDate(filterValue[1]);
      if (leftDate && lowDate && highDate) {
        return leftDate >= lowDate && leftDate <= highDate;
      }
    }
    return true;
  }

  if (["before", "on_or_before", "after", "on_or_after"].includes(op)) {
    const left = coerceDate(value);
    const right = coerceDate(filterValue);
    if (!left || !right) return false;
    if (op === "before") return left < right;
    if (op === "on_or_before") return left <= right;
    if (op === "after") return left > right;
    return left >= right;
  }

  if (op === "contains_any") {
    const items = normalizeListLikeValue(value);
    const filterItems = normalizeListLikeValue(filterValue);
    return filterItems.some((item) => items.some((candidate) => searchText(candidate) === searchText(item)));
  }

  if (op === "contains_all") {
    const items = normalizeListLikeValue(value);
    const filterItems = normalizeListLikeValue(filterValue);
    return filterItems.every((item) => items.some((candidate) => searchText(candidate) === searchText(item)));
  }

  return true;
}

function coerceNumber(value: any): number | null {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  if (typeof value === "boolean") return value ? 1 : 0;
  if (typeof value === "string") {
    const parsed = Number(value.trim());
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function coerceDate(value: any): string | null {
  if (value === null || value === undefined) return null;
  if (typeof value === "string") return value.trim() || null;
  if (value instanceof Date && !Number.isNaN(value.getTime())) return value.toISOString();
  return typeof value.isoformat === "function" ? String(value.isoformat()) : String(value);
}

function isEmptyValue(value: any): boolean {
  if (value === null || value === undefined) return true;
  if (typeof value === "string") return value.trim() === "";
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === "object") return Object.keys(value).length === 0;
  return false;
}
