import React, { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { FastlitWS } from "./runtime/ws";
import { applyPatch } from "./runtime/patcher";
import { NodeRenderer } from "./registry/NodeRenderer";
import { WidgetStoreProvider, WidgetStoreImpl } from "./context/WidgetStore";
import type { UINode, ErrorMessage } from "./runtime/types";

type ConnectionStatus = "connecting" | "connected" | "disconnected";

/** Convert page name to URL slug: "Dialog & Popover" → "dialog-popover" */
function toSlug(page: string): string {
  return page
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

/** Get current page from URL pathname */
function getPageFromUrl(): string {
  const path = window.location.pathname;
  // Remove leading slash, decode
  return decodeURIComponent(path.slice(1));
}

export const App: React.FC = () => {
  const [tree, setTree] = useState<UINode | null>(null);
  const [error, setError] = useState<ErrorMessage | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const wsRef = useRef<FastlitWS | null>(null);
  const storeRef = useRef(new WidgetStoreImpl());

  // --- Page routing: clean URLs like /layouts, /widgets ---
  const sidebarNavRef = useRef<{
    id: string;
    options: string[];
    slugs: string[]; // URL slugs for each option
    type: "radio" | "navigation";
  } | null>(null);
  const initialPathRef = useRef(getPageFromUrl());

  // Debounce timers and pending values for noRerun events (slider, text_input, etc.)
  const debounceTimersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
  const pendingValuesRef = useRef<Map<string, any>>(new Map());
  const DEBOUNCE_MS = 100; // 100ms debounce for value widgets

  // Flush all pending debounced events immediately (called before action events)
  const flushPendingEvents = useCallback(() => {
    // Clear all timers and send pending values immediately
    for (const [widgetId, timer] of debounceTimersRef.current.entries()) {
      clearTimeout(timer);
      const pendingValue = pendingValuesRef.current.get(widgetId);
      if (pendingValue !== undefined) {
        wsRef.current?.send({ type: "widget_event", id: widgetId, value: pendingValue, noRerun: true });
      }
    }
    debounceTimersRef.current.clear();
    pendingValuesRef.current.clear();
  }, []);

  // Send events — navigation updates store instantly, then server sends new content
  const sendEvent = useCallback((id: string, value: any, options?: { noRerun?: boolean }) => {
    const nav = sidebarNavRef.current;
    if (nav && id === nav.id) {
      const page = nav.options[value as number];
      const slug = nav.slugs[value as number];
      if (page && slug) {
        // Flush pending widget values before navigation
        flushPendingEvents();
        // 1. Update store → instant re-render of nav component (no flicker)
        storeRef.current.set(nav.id, page);
        // 2. Update URL with clean path
        window.history.pushState(null, "", `/${slug}`);
        // 3. Tell server to navigate — it will rerun and send new page content
        wsRef.current?.send({ type: "widget_event", id, value });
        return;
      }
    }

    // For noRerun events: debounce to avoid flooding the server
    if (options?.noRerun) {
      // Store the pending value
      pendingValuesRef.current.set(id, value);
      // Clear any pending debounce for this widget
      const existing = debounceTimersRef.current.get(id);
      if (existing) {
        clearTimeout(existing);
      }
      // Schedule the send after debounce delay
      const timer = setTimeout(() => {
        debounceTimersRef.current.delete(id);
        pendingValuesRef.current.delete(id);
        const msg = { type: "widget_event" as const, id, value, noRerun: true };
        console.log("[DEBUG] Sending noRerun event:", msg);
        wsRef.current?.send(msg);
      }, DEBOUNCE_MS);
      debounceTimersRef.current.set(id, timer);
      return;
    }

    // For action events (button, etc.): flush pending values first, then send
    flushPendingEvents();
    const msg = { type: "widget_event" as const, id, value, noRerun: options?.noRerun };
    console.log("[DEBUG] Sending action event:", msg);
    wsRef.current?.send(msg);
  }, [flushPendingEvents]);

  // WebSocket setup
  useEffect(() => {
    const ws = new FastlitWS();
    wsRef.current = ws;

    ws.onStatusChange(setStatus);

    ws.onRenderFull((msg) => {
      setTree(msg.tree);
      setError(null);
    });

    ws.onRenderPatch((msg) => {
      setTree((prev) => {
        if (!prev) return prev;
        return applyPatch(prev, msg.ops);
      });
      setError(null);
    });

    ws.onError((msg) => {
      setError(msg);
    });

    ws.connect();

    return () => {
      ws.disconnect();
    };
  }, []);

  // Extract sidebar nav info — URL is source of truth, never overwrite it
  useEffect(() => {
    if (!tree?.children) return;

    const sidebar = tree.children.find((c) => c.type === "sidebar");
    // Support both navigation (links) and radio (legacy) for page routing
    const navNode = sidebar?.children?.find(
      (c) => c.type === "navigation" || c.type === "radio",
    );

    if (navNode) {
      const isNav = navNode.type === "navigation";
      const opts = (isNav ? navNode.props.pages : navNode.props.options) as string[];
      const slugs = opts.map(toSlug);
      const serverIdx = navNode.props.index as number;

      sidebarNavRef.current = {
        id: navNode.id,
        options: opts,
        slugs,
        type: isNav ? "navigation" : "radio",
      };

      // URL is the source of truth — check what page the URL says we're on
      const currentSlug = getPageFromUrl();
      const urlIdx = slugs.indexOf(currentSlug);

      // On first load with empty URL, set URL to server's default page
      if (!currentSlug && serverIdx >= 0) {
        const defaultSlug = slugs[serverIdx] || slugs[0];
        if (defaultSlug) {
          window.history.replaceState(null, "", `/${defaultSlug}`);
        }
      }
      // If URL points to a valid page different from server, tell server to navigate
      else if (urlIdx >= 0 && urlIdx !== serverIdx) {
        // Update store for instant UI
        storeRef.current.set(navNode.id, opts[urlIdx]);
        // Tell server to navigate — it will rerun and send new page content
        wsRef.current?.send({ type: "widget_event", id: navNode.id, value: urlIdx });
      }
    }
  }, [tree]);

  // Browser back/forward navigation
  useEffect(() => {
    const handlePopState = () => {
      const slug = getPageFromUrl();
      const nav = sidebarNavRef.current;
      if (!nav) return;

      const idx = nav.slugs.indexOf(slug);
      if (idx < 0) return;

      // Update store directly for instant nav component re-render
      storeRef.current.set(nav.id, nav.options[idx]);

      // Tell server to navigate — it will rerun and send new page content
      wsRef.current?.send({ type: "widget_event", id: nav.id, value: idx });
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  // Split tree into sidebar and main content
  const hasSidebar = useMemo(() => {
    if (!tree?.children) return false;
    return tree.children.some((c) => c.type === "sidebar");
  }, [tree]);

  const { sidebarNodes, mainNodes } = useMemo(() => {
    if (!tree?.children)
      return { sidebarNodes: [] as UINode[], mainNodes: [] as UINode[] };
    const sidebar: UINode[] = [];
    const main: UINode[] = [];
    for (const child of tree.children) {
      if (child.type === "sidebar") {
        sidebar.push(child);
      } else {
        main.push(child);
      }
    }
    return { sidebarNodes: sidebar, mainNodes: main };
  }, [tree]);

  // Display the real main nodes from the server
  const displayMainNodes = mainNodes;

  return (
    <WidgetStoreProvider store={storeRef.current}>
      {sidebarNodes.map((node) => (
        <NodeRenderer key={node.id} node={node} sendEvent={sendEvent} />
      ))}

      <div
        className={`${hasSidebar ? "ml-64" : ""} max-w-4xl mx-auto px-6 py-8`}
      >
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

        {tree ? (
          displayMainNodes.map((node) => (
            <NodeRenderer key={node.id} node={node} sendEvent={sendEvent} />
          ))
        ) : (
          status === "connected" && (
            <p className="text-gray-400 text-sm">
              Waiting for app to render...
            </p>
          )
        )}
      </div>
    </WidgetStoreProvider>
  );
};
