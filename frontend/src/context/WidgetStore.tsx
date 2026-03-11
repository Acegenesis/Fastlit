/**
 * WidgetStore — single source of truth for all widget values.
 *
 * Architecture (React-first):
 *   Widget interaction → store.set() → instant re-render
 *   sendEvent() to server → async, never blocks UI
 *   Server patches → update tree structure only, never override store
 *
 * Per-widget subscriptions: only widgets/texts bound to changed IDs re-render.
 */

import React, {
  createContext,
  useContext,
  useCallback,
  useMemo,
  useRef,
  useSyncExternalStore,
} from "react";

type Listener = () => void;

export interface LiveExpression {
  kind: "literal" | "widget" | "binary" | "unary" | "if";
  value?: any;
  widgetId?: string;
  op?: string;
  left?: LiveExpression;
  right?: LiveExpression;
  condition?: LiveExpression;
  then?: LiveExpression;
  else?: LiveExpression;
}

function pythonFloorDiv(left: any, right: any): number | undefined {
  if (typeof left !== "number" || typeof right !== "number" || right === 0) return undefined;
  return Math.floor(left / right);
}

function pythonModulo(left: any, right: any): number | undefined {
  if (typeof left !== "number" || typeof right !== "number" || right === 0) return undefined;
  return left - pythonFloorDiv(left, right)! * right;
}

export class WidgetStoreImpl {
  private values = new Map<string, any>();
  private widgetSubs = new Map<string, Set<Listener>>();

  get(id: string): any {
    return this.values.get(id);
  }

  has(id: string): boolean {
    return this.values.has(id);
  }

  /** Update a value — only notifies if the value actually changed. */
  set(id: string, value: any): void {
    if (Object.is(this.values.get(id), value)) return;
    this.values.set(id, value);
    this.widgetSubs.get(id)?.forEach((l) => l());
  }

  /** Set a default value silently (no listeners). Used during first render. */
  init(id: string, value: any): void {
    if (!this.values.has(id)) {
      this.values.set(id, value);
    }
  }

  subscribeWidget(id: string, listener: Listener): () => void {
    let set = this.widgetSubs.get(id);
    if (!set) {
      set = new Set();
      this.widgetSubs.set(id, set);
    }
    set.add(listener);
    return () => set!.delete(listener);
  }

  subscribeMany(ids: Iterable<string>, listener: Listener): () => void {
    const unsubs: Array<() => void> = [];
    for (const id of ids) {
      unsubs.push(this.subscribeWidget(id, listener));
    }
    return () => {
      for (const unsub of unsubs) unsub();
    };
  }
}

const StoreContext = createContext<WidgetStoreImpl | null>(null);

interface ProviderProps {
  store: WidgetStoreImpl;
  children: React.ReactNode;
}

export const WidgetStoreProvider: React.FC<ProviderProps> = ({
  store,
  children,
}) => {
  return (
    <StoreContext.Provider value={store}>{children}</StoreContext.Provider>
  );
};

/** Return the raw store instance (for App-level operations like deep links). */
export function useWidgetStore(): WidgetStoreImpl {
  return useContext(StoreContext)!;
}

/**
 * Hook for widgets: read + write a single widget value.
 * Per-widget subscription — only THIS widget re-renders on change.
 * No useState, no useEffect needed in the widget component.
 */
export function useWidgetValue(
  id: string,
  defaultValue: any,
): [any, (v: any) => void] {
  const store = useContext(StoreContext)!;

  // Silently initialize on first render so useResolvedText can find it.
  store.init(id, defaultValue);

  const subscribe = useCallback(
    (cb: () => void) => store.subscribeWidget(id, cb),
    [store, id],
  );

  const getSnapshot = useCallback(() => {
    const v = store.get(id);
    return v !== undefined ? v : defaultValue;
  }, [store, id, defaultValue]);

  const value = useSyncExternalStore(subscribe, getSnapshot);

  const setValue = useCallback((v: any) => store.set(id, v), [store, id]);

  return [value, setValue];
}

function collectExpressionWidgetIds(expr?: LiveExpression): string[] {
  if (!expr) return [];
  switch (expr.kind) {
    case "widget":
      return expr.widgetId ? [expr.widgetId] : [];
    case "binary":
      return [...collectExpressionWidgetIds(expr.left), ...collectExpressionWidgetIds(expr.right)];
    case "unary":
      return collectExpressionWidgetIds(expr.value);
    case "if":
      return [
        ...collectExpressionWidgetIds(expr.condition),
        ...collectExpressionWidgetIds(expr.then),
        ...collectExpressionWidgetIds(expr.else),
      ];
    default:
      return [];
  }
}

function areStringArraysEqual(left: readonly string[], right: readonly string[]): boolean {
  if (left === right) return true;
  if (left.length !== right.length) return false;
  for (let i = 0; i < left.length; i += 1) {
    if (left[i] !== right[i]) return false;
  }
  return true;
}

function evaluateExpression(expr: LiveExpression | undefined, store: WidgetStoreImpl): any {
  if (!expr) return undefined;
  switch (expr.kind) {
    case "literal":
      return expr.value;
    case "widget":
      return expr.widgetId ? store.get(expr.widgetId) : undefined;
    case "binary": {
      const left = evaluateExpression(expr.left, store);
      const right = evaluateExpression(expr.right, store);
      switch (expr.op) {
        case "add": return left + right;
        case "sub": return left - right;
        case "mul": return left * right;
        case "div": return left / right;
        case "floordiv": return pythonFloorDiv(left, right);
        case "mod": return pythonModulo(left, right);
        case "pow": return left ** right;
        case "eq": return left === right;
        case "ne": return left !== right;
        case "lt": return left < right;
        case "le": return left <= right;
        case "gt": return left > right;
        case "ge": return left >= right;
        default: return undefined;
      }
    }
    case "unary": {
      const next = evaluateExpression(expr.value, store);
      switch (expr.op) {
        case "neg": return -next;
        case "abs": return Math.abs(next);
        default: return undefined;
      }
    }
    case "if":
      return evaluateExpression(expr.condition, store)
        ? evaluateExpression(expr.then, store)
        : evaluateExpression(expr.else, store);
    default:
      return undefined;
  }
}

function useExpressionSnapshot<T>(fallback: T, expr?: LiveExpression): T {
  const store = useContext(StoreContext);
  const exprWidgetIds = useMemo(
    () => Array.from(new Set(collectExpressionWidgetIds(expr))),
    [expr]
  );

  const subscribe = useCallback(
    (cb: () => void) => {
      if (!store || exprWidgetIds.length === 0) return () => {};
      return store.subscribeMany(exprWidgetIds, cb);
    },
    [store, exprWidgetIds]
  );

  const getSnapshot = useCallback(() => {
    if (!store || !expr) return fallback;
    const resolved = evaluateExpression(expr, store);
    return (resolved !== undefined ? resolved : fallback) as T;
  }, [store, expr, fallback]);

  return useSyncExternalStore(subscribe, getSnapshot);
}

export function useResolvedValue<T>(fallback: T, expr?: LiveExpression): T {
  return useExpressionSnapshot(fallback, expr);
}

function resolveTemplateText(
  fallback: string,
  tpl: string | undefined,
  refs: Record<string, string> | undefined,
  exprs: Record<string, LiveExpression> | undefined,
  store: WidgetStoreImpl | null,
): string {
  if (!tpl || !store) return fallback;
  let resolved = tpl;
  if (refs) {
    for (const [placeholder, widgetId] of Object.entries(refs)) {
      const liveValue = store.get(widgetId);
      if (liveValue !== undefined) {
        resolved = resolved.replace(placeholder, String(liveValue));
      } else {
        return fallback;
      }
    }
  }
  if (exprs) {
    for (const [placeholder, expr] of Object.entries(exprs)) {
      const liveValue = evaluateExpression(expr, store);
      if (liveValue !== undefined) {
        resolved = resolved.replace(placeholder, String(liveValue));
      } else {
        return fallback;
      }
    }
  }
  return resolved;
}

/**
 * Hook for text components: resolve a template using live widget values.
 * Subscribes only to referenced widget IDs.
 */
export function useResolvedText(
  text: string,
  tpl?: string,
  refs?: Record<string, string>,
  exprs?: Record<string, LiveExpression>,
): string {
  const store = useContext(StoreContext);
  const refWidgetIds = useMemo(() => {
    const direct = refs ? Object.values(refs) : [];
    const computed = exprs ? Object.values(exprs).flatMap((expr) => collectExpressionWidgetIds(expr)) : [];
    return Array.from(new Set([...direct, ...computed]));
  }, [exprs, refs]
  );

  const subscribe = useCallback(
    (cb: () => void) => {
      if (!store || refWidgetIds.length === 0) return () => {};
      return store.subscribeMany(refWidgetIds, cb);
    },
    [store, refWidgetIds]
  );

  const getSnapshot = useCallback(() => {
    return resolveTemplateText(text, tpl, refs, exprs, store);
  }, [exprs, refs, store, text, tpl]);

  return useSyncExternalStore(subscribe, getSnapshot);
}

export function useResolvedPropText(
  props: Record<string, any>,
  prefix: string,
  fallback = "",
): string {
  return useResolvedText(
    String(props[prefix] ?? fallback),
    props[`${prefix}Tpl`],
    props[`${prefix}Refs`],
    props[`${prefix}Exprs`],
  );
}

export function useResolvedPropValue<T>(
  props: Record<string, any>,
  prefix: string,
  fallback: T,
): T {
  return useResolvedValue((props[prefix] ?? fallback) as T, props[`${prefix}Live`]);
}

export function useResolvedTextList(
  texts: Array<string | null | undefined>,
  tpls?: Array<string | null | undefined>,
  refsList?: Array<Record<string, string> | null | undefined>,
  exprsList?: Array<Record<string, LiveExpression> | null | undefined>,
): string[] {
  const store = useContext(StoreContext);
  const cachedSnapshotRef = useRef<string[]>([]);
  const widgetIds = useMemo(() => {
    const direct = (refsList ?? []).flatMap((refs) => refs ? Object.values(refs) : []);
    const computed = (exprsList ?? []).flatMap((exprs) =>
      exprs ? Object.values(exprs).flatMap((expr) => collectExpressionWidgetIds(expr)) : []
    );
    return Array.from(new Set([...direct, ...computed]));
  }, [exprsList, refsList]);

  const subscribe = useCallback(
    (cb: () => void) => {
      if (!store || widgetIds.length === 0) return () => {};
      return store.subscribeMany(widgetIds, cb);
    },
    [store, widgetIds]
  );

  const getSnapshot = useCallback(() => {
    const nextSnapshot = texts.map((text, index) =>
      resolveTemplateText(
        String(text ?? ""),
        tpls?.[index] ?? undefined,
        refsList?.[index] ?? undefined,
        exprsList?.[index] ?? undefined,
        store,
      )
    );
    const cachedSnapshot = cachedSnapshotRef.current;
    if (areStringArraysEqual(cachedSnapshot, nextSnapshot)) {
      return cachedSnapshot;
    }
    cachedSnapshotRef.current = nextSnapshot;
    return nextSnapshot;
  }, [exprsList, refsList, store, texts, tpls]);

  return useSyncExternalStore(subscribe, getSnapshot);
}
