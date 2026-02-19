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

/**
 * Hook for text components: resolve a template using live widget values.
 * Subscribes only to referenced widget IDs.
 */
export function useResolvedText(
  text: string,
  tpl?: string,
  refs?: Record<string, string>,
): string {
  const store = useContext(StoreContext);
  const refWidgetIds = useMemo(
    () => (refs ? Array.from(new Set(Object.values(refs))) : []),
    [refs]
  );

  const subscribe = useCallback(
    (cb: () => void) => {
      if (!store || refWidgetIds.length === 0) return () => {};
      return store.subscribeMany(refWidgetIds, cb);
    },
    [store, refWidgetIds]
  );

  const getSnapshot = useCallback(() => {
    if (!tpl || !refs || !store) return text;
    let resolved = tpl;
    for (const [placeholder, widgetId] of Object.entries(refs)) {
      const liveValue = store.get(widgetId);
      if (liveValue !== undefined) {
        resolved = resolved.replace(placeholder, String(liveValue));
      } else {
        return text;
      }
    }
    return resolved;
  }, [store, text, tpl, refs]);

  return useSyncExternalStore(subscribe, getSnapshot);
}
