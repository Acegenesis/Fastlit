import React, {
  useEffect,
  useRef,
  useState,
  useCallback,
  useMemo,
  useTransition,
} from "react";
import { FastlitWS } from "./runtime/ws";
import { applyPatch } from "./runtime/patcher";
import { applyPatchAsync } from "./runtime/patchWorkerClient";
import { NodeRenderer } from "./registry/NodeRenderer";
import { prefetchDefaultChunks, prefetchLikelyChunks } from "./registry/registry";
import { WidgetStoreProvider, WidgetStoreImpl } from "./context/WidgetStore";
import { SidebarContext } from "./context/SidebarContext";
import { Toaster } from "@/components/ui/sonner";
import { PageSkeleton } from "./components/layout/PageSkeleton";
import { cn } from "@/lib/utils";
import type { UINode, ErrorMessage, RuntimeEventPayload } from "./runtime/types";

type ConnectionStatus = "connecting" | "connected" | "disconnected";

/** Convert page name to URL slug */
function toSlug(page: string): string {
  return page
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

/** Get current page from URL pathname */
function getPageFromUrl(): string {
  return decodeURIComponent(window.location.pathname.slice(1));
}

// Page cache for instant navigation (LRU, max 20 entries)
type PageCache = Map<string, UINode[]>;
const PAGE_CACHE_MAX = 20;

/** Set a page in the cache, evicting oldest if over limit */
function setCacheEntry(cache: PageCache, slug: string, content: UINode[]) {
  cache.delete(slug); // remove first so re-insert puts it at end (most recent)
  cache.set(slug, content);
  while (cache.size > PAGE_CACHE_MAX) {
    const oldest = cache.keys().next().value;
    if (oldest !== undefined) cache.delete(oldest);
    else break;
  }
}

/** Collect all widget IDs from a UI tree (for orphan cleanup) */
function collectIds(node: UINode): Set<string> {
  const ids = new Set<string>();
  const stack = [node];
  while (stack.length) {
    const n = stack.pop()!;
    ids.add(n.id);
    if (n.children) stack.push(...n.children);
  }
  return ids;
}

export const App: React.FC = () => {
  const [tree, setTree] = useState<UINode | null>(null);
  const [error, setError] = useState<ErrorMessage | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [isNavigating, setIsNavigating] = useState(false);
  const [layout, setLayout] = useState<string>("centered");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [runtimeSpinners, setRuntimeSpinners] = useState<Map<string, string>>(new Map());
  const wsRef = useRef<FastlitWS | null>(null);
  const storeRef = useRef(new WidgetStoreImpl());

  // Page cache for instant switching (caches visited pages)
  const pageCacheRef = useRef<PageCache>(new Map());
  const currentPageRef = useRef<string>("");

  // Navigation state
  const sidebarNavRef = useRef<{
    id: string;
    options: string[];
    slugs: string[];
  } | null>(null);

  const [isPending, startTransition] = useTransition();

  // Cached navigation can require skipping exactly one backend patch.
  // We bind the skip to revision progression instead of a global boolean.
  const pendingSkipPatchAfterRevRef = useRef<number | null>(null);
  const lastServerRevRef = useRef(0);

  // Debounce for value widgets
  const debounceTimersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
  const pendingValuesRef = useRef<Map<string, any>>(new Map());
  const DEBOUNCE_MS = 150;

  const idleHandleRef = useRef<number | null>(null);
  const prefetchedNodeTypesRef = useRef<Set<string>>(new Set());
  const prefetchedDefaultsRef = useRef(false);
  const patchJobSeqRef = useRef(0);

  // Listen for page-config events from PageConfig component (A1, A4)
  useEffect(() => {
    const handler = (e: Event) => {
      const { layout: l, initialSidebarState } = (e as CustomEvent).detail;
      if (l) setLayout(l);
      if (initialSidebarState === "collapsed") setSidebarCollapsed(true);
      else if (initialSidebarState === "expanded") setSidebarCollapsed(false);
    };
    window.addEventListener("fastlit:page-config", handler);
    return () => window.removeEventListener("fastlit:page-config", handler);
  }, []);

  // Listen for sidebar_state nodes from backend (C2)
  // Backend emits a sidebar_state node via set_sidebar_state()
  const handleSidebarStateNode = useCallback((nodes: UINode[]) => {
    for (const node of nodes) {
      if (node.type === "sidebar_state") {
        if (node.props?.state === "collapsed") setSidebarCollapsed(true);
        else if (node.props?.state === "expanded") setSidebarCollapsed(false);
      }
    }
  }, []);

  // Flush pending widget values
  const flushPendingEvents = useCallback(() => {
    for (const [widgetId, timer] of debounceTimersRef.current.entries()) {
      clearTimeout(timer);
      const pendingValue = pendingValuesRef.current.get(widgetId);
      if (pendingValue !== undefined) {
        wsRef.current?.send({
          type: "widget_event",
          id: widgetId,
          value: pendingValue,
          noRerun: true,
        });
      }
    }
    debounceTimersRef.current.clear();
    pendingValuesRef.current.clear();
  }, []);

  // PURE REACT NAVIGATION - no server waiting
  const navigateToPage = useCallback(
    (pageIndex: number) => {
      const nav = sidebarNavRef.current;
      if (!nav) return;

      const page = nav.options[pageIndex];
      const slug = nav.slugs[pageIndex];
      if (!page || !slug) return;

      // Skip if already on this page
      if (currentPageRef.current === slug) return;

      flushPendingEvents();

      // 1. Update sidebar selection (React state)
      storeRef.current.set(nav.id, page);

      // 2. Update URL (browser)
      window.history.pushState(null, "", `/${slug}`);

      // 3. Update content from cache if available
      const cachedContent = pageCacheRef.current.get(slug);
      const hasCache = cachedContent && cachedContent.length > 0;

      currentPageRef.current = slug;

      if (hasCache) {
        // Show cached content instantly
        setTree((prev) => {
          if (!prev?.children) return prev;
          const sidebar = prev.children.filter((c) => c.type === "sidebar");
          return { ...prev, children: [...sidebar, ...cachedContent] };
        });
        // Send normal event so backend reruns and syncs _previous_tree.
        // Skip exactly the next newer patch revision for this cached navigation.
        pendingSkipPatchAfterRevRef.current = lastServerRevRef.current;
        wsRef.current?.send({
          type: "widget_event",
          id: nav.id,
          value: pageIndex,
        });
      } else {
        // No cache - show skeleton and request content from server
        setIsNavigating(true);
        wsRef.current?.send({
          type: "widget_event",
          id: nav.id,
          value: pageIndex,
        });
      }
    },
    [flushPendingEvents]
  );

  // Ref to always access latest navigateToPage without changing sendEvent identity
  const navigateToPageRef = useRef(navigateToPage);
  navigateToPageRef.current = navigateToPage;

  // Main event handler — stable reference (empty deps) so React.memo works on NodeRenderer
  const sendEvent = useCallback(
    (id: string, value: any, options?: { noRerun?: boolean }) => {
      const nav = sidebarNavRef.current;

      // Navigation events - pure React
      if (nav && id === nav.id) {
        navigateToPageRef.current(value as number);
        return;
      }

      // NoRerun events - debounce
      if (options?.noRerun) {
        pendingValuesRef.current.set(id, value);
        const existing = debounceTimersRef.current.get(id);
        if (existing) clearTimeout(existing);

        const timer = setTimeout(() => {
          debounceTimersRef.current.delete(id);
          pendingValuesRef.current.delete(id);
          wsRef.current?.send({ type: "widget_event", id, value, noRerun: true });
        }, DEBOUNCE_MS);

        debounceTimersRef.current.set(id, timer);
        return;
      }

      // Action events - flush and send
      for (const [widgetId, t] of debounceTimersRef.current.entries()) {
        clearTimeout(t);
        const pv = pendingValuesRef.current.get(widgetId);
        if (pv !== undefined) {
          wsRef.current?.send({ type: "widget_event", id: widgetId, value: pv, noRerun: true });
        }
      }
      debounceTimersRef.current.clear();
      pendingValuesRef.current.clear();
      wsRef.current?.send({ type: "widget_event", id, value });
    },
    [] // stable forever — all deps accessed via refs
  );

  // WebSocket setup
  useEffect(() => {
    const ws = new FastlitWS();
    wsRef.current = ws;

    ws.onStatusChange((nextStatus) => {
      setStatus(nextStatus);
      if (nextStatus !== "connected") {
        setRuntimeSpinners(new Map());
      }
    });

    ws.onRenderFull((msg) => {
      lastServerRevRef.current = Math.max(lastServerRevRef.current, msg.rev);
      if (
        pendingSkipPatchAfterRevRef.current !== null &&
        msg.rev > pendingSkipPatchAfterRevRef.current
      ) {
        // Backend state moved forward via full render; no patch skip needed anymore.
        pendingSkipPatchAfterRevRef.current = null;
      }
      // Check for sidebar_state nodes
      if (msg.tree?.children) {
        handleSidebarStateNode(msg.tree.children);
      }

      // Extract nav info from response
      const sidebar = msg.tree?.children?.find((c) => c.type === "sidebar");
      const navNode = sidebar?.children?.find(
        (c) => c.type === "navigation" || c.type === "radio"
      );
      const responseNavIndex = navNode?.props?.index as number | undefined;

      // Track if this is first load (nav just initialized)
      let isFirstLoad = false;

      // CRITICAL: Initialize nav IMMEDIATELY on first message (before useEffect)
      // This prevents prefetch responses from displaying before nav is set up
      if (navNode && !sidebarNavRef.current) {
        isFirstLoad = true;
        const isNav = navNode.type === "navigation";
        const opts = (isNav ? navNode.props.pages : navNode.props.options) as string[];
        const slugs = opts.map(toSlug);
        sidebarNavRef.current = { id: navNode.id, options: opts, slugs };

        // Respect the current URL on page reload; only fall back to server index
        const currentUrlSlug = getPageFromUrl();
        const urlIdx = currentUrlSlug ? slugs.indexOf(currentUrlSlug) : -1;

        if (urlIdx >= 0) {
          // URL matches a known page — use it (page reload case)
          currentPageRef.current = currentUrlSlug;
          // Update widget store so Navigation component shows correct selection
          storeRef.current.set(navNode.id, opts[urlIdx]);
          // Tell server to switch to this page so the next response is correct
          if (urlIdx !== (responseNavIndex ?? 0)) {
            setIsNavigating(true);
            wsRef.current?.send({
              type: "widget_event",
              id: navNode.id,
              value: urlIdx,
            });
          }
        } else {
          // No URL or unknown slug — use server default
          const serverIdx = responseNavIndex ?? 0;
          const initialSlug = slugs[serverIdx];
          if (initialSlug) {
            currentPageRef.current = initialSlug;
            window.history.replaceState(null, "", `/${initialSlug}`);
          }
        }
      }

      const nav = sidebarNavRef.current;

      // Determine which page this response is for
      const responseSlug = (responseNavIndex !== undefined && nav)
        ? nav.slugs[responseNavIndex]
        : null;

      // Cache the content for this page (always cache, even if not displaying)
      if (responseSlug && msg.tree?.children) {
        const mainContent = msg.tree.children.filter((c) => c.type !== "sidebar");
        setCacheEntry(pageCacheRef.current, responseSlug, mainContent);
      }

      // Only display if this response is for the current page
      const currentSlug = currentPageRef.current;
      const isCorrectPage = responseSlug === currentSlug;
      const shouldDisplay = isCorrectPage || (!nav && !currentSlug);

      if (isFirstLoad) {
        // ALWAYS set the tree on first load so sidebar is initialized and
        // subsequent patches have a base tree to work with.
        startTransition(() => {
          setTree(msg.tree);
          setError(null);
          // If the URL matched the server response, show content;
          // otherwise keep skeleton visible (we already sent an event for the right page)
          if (isCorrectPage) {
            setIsNavigating(false);
          }
        });
      } else if (shouldDisplay) {
        startTransition(() => {
          setTree(msg.tree);
          setError(null);
          setIsNavigating(false);
        });
      }
    });

    ws.onRenderPatch((msg) => {
      lastServerRevRef.current = Math.max(lastServerRevRef.current, msg.rev);
      // After cached navigation, the backend reruns to sync _previous_tree.
      // The patch it sends is based on (old page → new page) diff, but the
      // frontend already shows the new page from cache. Applying this patch
      // would corrupt the tree (duplication). Skip only the expected next rev.
      const skipAfterRev = pendingSkipPatchAfterRevRef.current;
      if (skipAfterRev !== null && msg.rev > skipAfterRev) {
        pendingSkipPatchAfterRevRef.current = null;
        setIsNavigating(false);
        return;
      }

      setTree((prev) => {
        if (!prev) return prev;
        const seq = ++patchJobSeqRef.current;
        applyPatchAsync(prev, msg.ops)
          .then((patched) => {
            if (seq !== patchJobSeqRef.current) return;
            startTransition(() => {
              setTree(patched);
              if (patched?.children) {
                handleSidebarStateNode(patched.children);
              }
              const currentSlug = currentPageRef.current;
              if (currentSlug && patched?.children) {
                const mainContent = patched.children.filter((c) => c.type !== "sidebar");
                setCacheEntry(pageCacheRef.current, currentSlug, mainContent);
              }
              setError(null);
              setIsNavigating(false);
            });
          })
          .catch(() => {
            const fallback = applyPatch(prev, msg.ops);
            startTransition(() => {
              setTree(fallback);
              setError(null);
              setIsNavigating(false);
            });
          });
        return prev;
      });
    });

    ws.onError((msg) => setError(msg));
    ws.onRuntimeEvent((msg) => {
      const event: RuntimeEventPayload = msg.event;
      if (event.kind !== "spinner") return;
      setRuntimeSpinners((prev) => {
        const next = new Map(prev);
        if (event.active) next.set(event.id, event.text || "Loading...");
        else next.delete(event.id);
        return next;
      });
    });
    ws.connect();

    return () => ws.disconnect();
  }, [handleSidebarStateNode]);

  // Cache current page content + clean orphan debounce timers when tree changes
  useEffect(() => {
    if (!tree?.children) return;

    const nav = sidebarNavRef.current;
    if (!nav) return;

    // Cache current page content
    const currentSlug = currentPageRef.current;
    if (currentSlug) {
      const mainContent = tree.children.filter((c) => c.type !== "sidebar");
      if (mainContent.length > 0) {
        setCacheEntry(pageCacheRef.current, currentSlug, mainContent);
      }
    }

    // Clean debounce timers for widgets no longer in the tree
    if (debounceTimersRef.current.size > 0) {
      const activeIds = collectIds(tree);
      for (const [widgetId, timer] of debounceTimersRef.current.entries()) {
        if (!activeIds.has(widgetId)) {
          clearTimeout(timer);
          debounceTimersRef.current.delete(widgetId);
          pendingValuesRef.current.delete(widgetId);
        }
      }
    }
  }, [tree]);

  // Browser back/forward - pure React
  useEffect(() => {
    const handlePopState = () => {
      const slug = getPageFromUrl();
      const nav = sidebarNavRef.current;
      if (!nav) return;

      const idx = nav.slugs.indexOf(slug);
      if (idx < 0) return;

      // Update sidebar selection
      storeRef.current.set(nav.id, nav.options[idx]);
      currentPageRef.current = slug;

      // Show cached content if available
      const cachedContent = pageCacheRef.current.get(slug);
      const hasCache = cachedContent && cachedContent.length > 0;

      if (hasCache) {
        setTree((prev) => {
          if (!prev?.children) return prev;
          const sidebar = prev.children.filter((c) => c.type === "sidebar");
          return { ...prev, children: [...sidebar, ...cachedContent] };
        });
        // Send normal event so backend syncs _previous_tree; skip the patch response
        pendingSkipPatchAfterRevRef.current = lastServerRevRef.current;
        wsRef.current?.send({
          type: "widget_event",
          id: nav.id,
          value: idx,
        });
      } else {
        // No cache - show skeleton and request content from server
        setIsNavigating(true);
        wsRef.current?.send({
          type: "widget_event",
          id: nav.id,
          value: idx,
        });
      }
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  // Memoized tree splitting
  const hasSidebar = useMemo(() => {
    return tree?.children?.some((c) => c.type === "sidebar") ?? false;
  }, [tree]);

  const { sidebarNodes, mainNodes } = useMemo(() => {
    if (!tree?.children) {
      return { sidebarNodes: [] as UINode[], mainNodes: [] as UINode[] };
    }
    const sidebar: UINode[] = [];
    const main: UINode[] = [];
    for (const child of tree.children) {
      if (child.type === "sidebar") sidebar.push(child);
      else main.push(child);
    }
    return { sidebarNodes: sidebar, mainNodes: main };
  }, [tree]);

  // offsetStyle: shifts the entire main area to the right of the sidebar.
  // Applied to an OUTER wrapper div so that the INNER .layout-main div can
  // still use margin-left:auto / margin-right:auto to center the content
  // within the remaining space. Setting marginLeft on .layout-main itself
  // would override the CSS `margin-left:auto` and break centering.
  const offsetStyle: React.CSSProperties = hasSidebar
    ? { marginLeft: sidebarCollapsed ? 0 : 256, transition: "margin-left 200ms ease" }
    : {};

  // Prefetch likely chunks when browser is idle.
  useEffect(() => {
    const scheduleIdle = (fn: () => void) => {
      const w = window as Window & {
        requestIdleCallback?: (cb: IdleRequestCallback, opts?: IdleRequestOptions) => number;
      };
      if (w.requestIdleCallback) {
        idleHandleRef.current = w.requestIdleCallback(() => fn(), { timeout: 1200 });
      } else {
        idleHandleRef.current = window.setTimeout(fn, 500);
      }
    };
    scheduleIdle(() => {
      if (!prefetchedDefaultsRef.current) {
        prefetchedDefaultsRef.current = true;
        prefetchDefaultChunks().catch(() => undefined);
      }
      if (tree) {
        const nodeTypes: string[] = [];
        const stack = [tree];
        while (stack.length > 0) {
          const n = stack.pop()!;
          if (!prefetchedNodeTypesRef.current.has(n.type)) {
            nodeTypes.push(n.type);
            prefetchedNodeTypesRef.current.add(n.type);
          }
          if (n.children) stack.push(...n.children);
        }
        if (nodeTypes.length > 0) {
          prefetchLikelyChunks(nodeTypes).catch(() => undefined);
        }
      }
    });
    return () => {
      if (idleHandleRef.current !== null) {
        const w = window as Window & { cancelIdleCallback?: (id: number) => void };
        if (w.cancelIdleCallback) w.cancelIdleCallback(idleHandleRef.current);
        else clearTimeout(idleHandleRef.current);
      }
      idleHandleRef.current = null;
    };
  }, [tree]);

  return (
    <WidgetStoreProvider store={storeRef.current}>
      <SidebarContext.Provider value={{ collapsed: sidebarCollapsed, setCollapsed: setSidebarCollapsed }}>
        <Toaster position="bottom-right" />
        {runtimeSpinners.size > 0 && (
          <div className="fixed top-3 right-3 z-50 flex flex-col gap-2">
            {Array.from(runtimeSpinners.entries()).map(([id, text]) => (
              <div
                key={id}
                className="flex items-center gap-3 rounded-md border bg-white px-3 py-2 shadow-sm"
              >
                <div className="relative">
                  <div className="w-5 h-5 border-2 border-gray-200 rounded-full" />
                  <div className="absolute inset-0 w-5 h-5 border-2 border-blue-500 rounded-full border-t-transparent animate-spin" />
                </div>
                <span className="text-gray-700 text-sm">{text}</span>
              </div>
            ))}
          </div>
        )}

        {sidebarNodes.map((node) => (
          <NodeRenderer key={node.id} node={node} sendEvent={sendEvent} />
        ))}

        {/* Outer div: pushes content past the sidebar (numeric px transition) */}
        <div style={offsetStyle}>
        {/* Inner div: .layout-main centers via margin:auto within the remaining space */}
        <div className="layout-main">
          {status === "connecting" && (
            <div className="mb-4 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-700">
              Connecting to Fastlit server...
            </div>
          )}
          {status === "disconnected" && (
            <div className="mb-4 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
              Disconnected. Reconnecting...
            </div>
          )}

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-300 rounded-lg">
              <h3 className="text-red-800 font-semibold mb-1">Error</h3>
              <p className="text-red-700 text-sm">{error.message}</p>
              {error.traceback && (
                <pre className="mt-2 text-xs text-red-600 bg-red-100 p-2 rounded overflow-auto">
                  {error.traceback}
                </pre>
              )}
            </div>
          )}

          {/* Show skeleton while navigating to uncached page */}
          {isNavigating && <PageSkeleton />}

          {/* Main content with fade transition */}
          {tree && mainNodes.length > 0 && !isNavigating && (
            <div
              key={currentPageRef.current}
              className={cn(
                "transition-opacity duration-200 ease-in-out",
                isPending ? "opacity-70" : "opacity-100"
              )}
            >
              {mainNodes.map((node) => (
                <NodeRenderer key={node.id} node={node} sendEvent={sendEvent} />
              ))}
            </div>
          )}

          {!tree && !isNavigating && status === "connected" && (
            <p className="text-muted-foreground text-sm">
              Waiting for app to render...
            </p>
          )}
        </div>{/* .layout-main */}
        </div>{/* sidebar offset wrapper */}
      </SidebarContext.Provider>
    </WidgetStoreProvider>
  );
};
