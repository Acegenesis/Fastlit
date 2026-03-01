import { useCallback, useEffect, useMemo, useState } from "react";
import type { GridViewState } from "./types";

const VIEW_STATE_VERSION = 3;

const EMPTY_VIEW_STATE: GridViewState = {
  search: "",
  sorts: [],
  filters: [],
  hiddenColumns: [],
  manualWidths: {},
  pinnedColumns: {},
  columnOrder: [],
  scrollTop: 0,
  scrollLeft: 0,
};

function sanitizeViewState(
  value: unknown,
  initialColumnOrder: string[],
): GridViewState {
  const base: GridViewState = { ...EMPTY_VIEW_STATE, columnOrder: [...initialColumnOrder] };
  if (!value || typeof value !== "object") return base;

  const raw = value as Partial<GridViewState>;
  const allowedColumns = new Set(initialColumnOrder);

  const columnOrder = Array.isArray(raw.columnOrder)
    ? raw.columnOrder.filter((name): name is string => typeof name === "string" && allowedColumns.has(name))
    : [];
  for (const columnName of initialColumnOrder) {
    if (!columnOrder.includes(columnName)) columnOrder.push(columnName);
  }

  const hiddenColumns = Array.isArray(raw.hiddenColumns)
    ? raw.hiddenColumns.filter((name): name is string => typeof name === "string" && allowedColumns.has(name))
    : [];

  const sorts = Array.isArray(raw.sorts)
    ? raw.sorts.filter(
        (item): item is GridViewState["sorts"][number] =>
          !!item &&
          typeof item === "object" &&
          typeof item.column === "string" &&
          allowedColumns.has(item.column) &&
          (item.direction === "asc" || item.direction === "desc")
      )
    : [];

  const filters = Array.isArray(raw.filters)
    ? raw.filters.filter(
        (item): item is GridViewState["filters"][number] =>
          !!item &&
          typeof item === "object" &&
          typeof item.id === "string" &&
          typeof item.column === "string" &&
          allowedColumns.has(item.column) &&
          typeof item.op === "string"
      )
    : [];

  const manualWidths =
    raw.manualWidths && typeof raw.manualWidths === "object"
      ? Object.fromEntries(
          Object.entries(raw.manualWidths).filter(
            ([name, width]) =>
              allowedColumns.has(name) &&
              typeof width === "number" &&
              Number.isFinite(width) &&
              width > 0
          )
        )
      : {};

  const pinnedColumns =
    raw.pinnedColumns && typeof raw.pinnedColumns === "object"
      ? Object.fromEntries(
          Object.entries(raw.pinnedColumns).filter(
            ([name, pinned]) =>
              allowedColumns.has(name) &&
              (pinned === "left" || pinned === "right" || pinned === null)
          )
        )
      : {};

  return {
    search: typeof raw.search === "string" ? raw.search : "",
    sorts,
    filters,
    hiddenColumns,
    manualWidths,
    pinnedColumns,
    columnOrder,
    scrollTop:
      typeof raw.scrollTop === "number" && Number.isFinite(raw.scrollTop) && raw.scrollTop >= 0
        ? raw.scrollTop
        : 0,
    scrollLeft:
      typeof raw.scrollLeft === "number" && Number.isFinite(raw.scrollLeft) && raw.scrollLeft >= 0
        ? raw.scrollLeft
        : 0,
  };
}

export function useGridViewState({
  nodeId,
  widgetKind,
  schemaSignature,
  enabled,
  initialColumnOrder,
}: {
  nodeId: string;
  widgetKind: string;
  schemaSignature: string;
  enabled: boolean;
  initialColumnOrder: string[];
}) {
  const storageKey = useMemo(
    () => `${nodeId}:${widgetKind}:viewState:v${VIEW_STATE_VERSION}`,
    [nodeId, widgetKind]
  );

  const [viewState, setViewState] = useState<GridViewState>(() => {
    const base: GridViewState = { ...EMPTY_VIEW_STATE, columnOrder: [...initialColumnOrder] };
    if (!enabled || typeof window === "undefined") return base;
    try {
      const raw = window.sessionStorage.getItem(storageKey);
      if (!raw) return base;
      const parsed = JSON.parse(raw);
      if (parsed?.schemaSignature !== schemaSignature) return base;
      return sanitizeViewState(parsed?.viewState, initialColumnOrder);
    } catch {
      return base;
    }
  });

  useEffect(() => {
    setViewState((current) => {
      return sanitizeViewState(current, initialColumnOrder);
    });
  }, [initialColumnOrder]);

  useEffect(() => {
    if (!enabled || typeof window === "undefined") return;
    window.sessionStorage.setItem(
      storageKey,
      JSON.stringify({ schemaSignature, viewState })
    );
  }, [enabled, schemaSignature, storageKey, viewState]);

  const updateViewState = useCallback(
    (updater: (current: GridViewState) => GridViewState) => {
      setViewState((current) => updater(current));
    },
    []
  );

  const resetViewState = useCallback(() => {
    setViewState({ ...EMPTY_VIEW_STATE, columnOrder: [...initialColumnOrder] });
  }, [initialColumnOrder]);

  return {
    storageKey,
    viewState,
    updateViewState,
    resetViewState,
  };
}
