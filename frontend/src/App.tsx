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
import { NodeRenderer } from "./registry/NodeRenderer";
import { WidgetStoreProvider, WidgetStoreImpl } from "./context/WidgetStore";
import { Toaster } from "@/components/ui/sonner";
import { PageSkeleton } from "./components/layout/PageSkeleton";
import { cn } from "@/lib/utils";
import type { UINode, ErrorMessage } from "./runtime/types";

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

// Page cache for instant navigation
type PageCache = Map<string, UINode[]>;

export const App: React.FC = () => {
  const [tree, setTree] = useState<UINode | null>(null);
  const [error, setError] = useState<ErrorMessage | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [isNavigating, setIsNavigating] = useState(false);
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

  // After cached navigation, skip the next patch response (backend syncs _previous_tree
  // but the patch is based on old→new diff which is wrong for the frontend's cached tree)
  const skipNextPatchRef = useRef(false);

  // Debounce for value widgets
  const debounceTimersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
  const pendingValuesRef = useRef<Map<string, any>>(new Map());
  const DEBOUNCE_MS = 150;

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
        // Skip the resulting patch (it's based on old→new diff, wrong for our cached tree).
        skipNextPatchRef.current = true;
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

    ws.onStatusChange(setStatus);

    ws.onRenderFull((msg) => {
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
        pageCacheRef.current.set(responseSlug, mainContent);
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
      // After cached navigation, the backend reruns to sync _previous_tree.
      // The patch it sends is based on (old page → new page) diff, but the
      // frontend already shows the new page from cache. Applying this patch
      // would corrupt the tree (duplication). Skip it — both sides are now synced.
      if (skipNextPatchRef.current) {
        skipNextPatchRef.current = false;
        setIsNavigating(false);
        return;
      }

      startTransition(() => {
        setTree((prev) => {
          if (!prev) return prev;
          const patched = applyPatch(prev, msg.ops);

          // Update cache
          const currentSlug = currentPageRef.current;
          if (currentSlug && patched?.children) {
            const mainContent = patched.children.filter((c) => c.type !== "sidebar");
            pageCacheRef.current.set(currentSlug, mainContent);
          }

          return patched;
        });
        setError(null);
        setIsNavigating(false);
      });
    });

    ws.onError((msg) => setError(msg));
    ws.connect();

    return () => ws.disconnect();
  }, []);

  // Cache current page content when tree changes
  useEffect(() => {
    if (!tree?.children) return;

    const nav = sidebarNavRef.current;
    if (!nav) return;

    // Cache current page content
    const currentSlug = currentPageRef.current;
    if (currentSlug) {
      const mainContent = tree.children.filter((c) => c.type !== "sidebar");
      if (mainContent.length > 0) {
        pageCacheRef.current.set(currentSlug, mainContent);
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
        skipNextPatchRef.current = true;
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

  return (
    <WidgetStoreProvider store={storeRef.current}>
      <Toaster position="bottom-right" />

      {sidebarNodes.map((node) => (
        <NodeRenderer key={node.id} node={node} sendEvent={sendEvent} />
      ))}

      <div className={`${hasSidebar ? "ml-64" : ""} max-w-4xl mx-auto px-6 py-8`}>
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
      </div>
    </WidgetStoreProvider>
  );
};
