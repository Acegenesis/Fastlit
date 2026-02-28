import { useCallback, useEffect, useMemo, useState } from "react";
import type { GridViewState } from "./types";

const VIEW_STATE_VERSION = 2;

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
      return {
        ...base,
        ...(parsed?.viewState ?? {}),
        columnOrder: Array.isArray(parsed?.viewState?.columnOrder) && parsed.viewState.columnOrder.length
          ? parsed.viewState.columnOrder
          : [...initialColumnOrder],
      };
    } catch {
      return base;
    }
  });

  useEffect(() => {
    setViewState((current) => {
      const nextOrder = current.columnOrder.length ? current.columnOrder : [...initialColumnOrder];
      return { ...current, columnOrder: nextOrder };
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
