/**
 * WidgetStore: shared React context for live widget values.
 *
 * Widgets publish their local state here on every change.
 * Text components (Markdown, Title, etc.) read from here to
 * resolve templates instantly — no server round-trip needed.
 */

import React, { createContext, useContext, useRef, useCallback, useSyncExternalStore } from "react";

type Listener = () => void;

class WidgetStoreImpl {
  private values = new Map<string, any>();
  private listeners = new Set<Listener>();
  private version = 0;

  get(id: string): any {
    return this.values.get(id);
  }

  set(id: string, value: any): void {
    this.values.set(id, value);
    this.version++;
    this.listeners.forEach((l) => l());
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  getVersion(): number {
    return this.version;
  }
}

const StoreContext = createContext<WidgetStoreImpl | null>(null);

export const WidgetStoreProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const storeRef = useRef(new WidgetStoreImpl());
  return (
    <StoreContext.Provider value={storeRef.current}>
      {children}
    </StoreContext.Provider>
  );
};

/**
 * Hook for widgets: publish their current value to the store.
 * Returns a setter function.
 */
export function useWidgetPublish(): (id: string, value: any) => void {
  const store = useContext(StoreContext);
  return useCallback(
    (id: string, value: any) => {
      store?.set(id, value);
    },
    [store]
  );
}

/**
 * Hook for text components: resolve a template string using live widget values.
 * Returns the resolved text, re-rendering when any referenced widget changes.
 */
export function useResolvedText(
  text: string,
  tpl?: string,
  refs?: Record<string, string>
): string {
  const store = useContext(StoreContext);

  // Subscribe to store changes for re-renders
  const subscribe = useCallback(
    (cb: () => void) => store?.subscribe(cb) ?? (() => {}),
    [store]
  );
  const getSnapshot = useCallback(
    () => store?.getVersion() ?? 0,
    [store]
  );
  useSyncExternalStore(subscribe, getSnapshot);

  // No template → return plain text (from server)
  if (!tpl || !refs || !store) return text;

  // Resolve template by replacing placeholders with live widget values
  let resolved = tpl;
  for (const [placeholder, widgetId] of Object.entries(refs)) {
    const liveValue = store.get(widgetId);
    if (liveValue !== undefined) {
      resolved = resolved.replace(placeholder, String(liveValue));
    } else {
      // Fallback: use server value (remove placeholder with original text)
      // The server text is the fallback
      return text;
    }
  }
  return resolved;
}
