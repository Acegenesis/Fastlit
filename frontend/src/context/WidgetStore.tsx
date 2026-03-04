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
        case "floordiv": return left / right >= 0 ? Math.floor(left / right) : Math.ceil(left / right);
        case "mod": return left % right;
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
    if (!tpl || !store) return text;
    let resolved = tpl;
    if (refs) {
      for (const [placeholder, widgetId] of Object.entries(refs)) {
        const liveValue = store.get(widgetId);
        if (liveValue !== undefined) {
          resolved = resolved.replace(placeholder, String(liveValue));
        } else {
          return text;
        }
      }
    }
    if (exprs) {
      for (const [placeholder, expr] of Object.entries(exprs)) {
        const liveValue = evaluateExpression(expr, store);
        if (liveValue !== undefined) {
          resolved = resolved.replace(placeholder, String(liveValue));
        } else {
          return text;
        }
      }
    }
    return resolved;
  }, [exprs, refs, store, text, tpl]);

  return useSyncExternalStore(subscribe, getSnapshot);
}
