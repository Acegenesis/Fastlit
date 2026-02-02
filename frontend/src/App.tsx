import React, { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { FastlitWS } from "./runtime/ws";
import { applyPatch } from "./runtime/patcher";
import { NodeRenderer } from "./registry/NodeRenderer";
import { WidgetStoreProvider, WidgetStoreImpl } from "./context/WidgetStore";
import type { UINode, ErrorMessage } from "./runtime/types";

type ConnectionStatus = "connecting" | "connected" | "disconnected";

export const App: React.FC = () => {
  const [tree, setTree] = useState<UINode | null>(null);
  const [error, setError] = useState<ErrorMessage | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const wsRef = useRef<FastlitWS | null>(null);
  const storeRef = useRef(new WidgetStoreImpl());

  // --- Page routing: URL hash + page cache for instant navigation ---
  const sidebarRadioRef = useRef<{ id: string; options: string[] } | null>(
    null,
  );
  const pageCacheRef = useRef(new Map<string, UINode[]>());
  const [optimisticMainNodes, setOptimisticMainNodes] = useState<
    UINode[] | null
  >(null);
  const initialHashRef = useRef(
    decodeURIComponent(window.location.hash.slice(1)),
  );

  // Send events — intercept sidebar radio for URL routing + optimistic nav
  const sendEvent = useCallback((id: string, value: any) => {
    const radio = sidebarRadioRef.current;
    if (radio && id === radio.id) {
      const page = radio.options[value as number];
      if (page) {
        // Update store directly → instant radio re-render
        storeRef.current.set(radio.id, page);
        // Update URL
        window.history.pushState(null, "", `#${encodeURIComponent(page)}`);
        // Show cached page content instantly (if we visited before)
        const cached = pageCacheRef.current.get(page);
        if (cached) {
          setOptimisticMainNodes(cached);
        }
      }
    }
    // Send to server async — never blocks UI
    wsRef.current?.send({ type: "widget_event", id, value });
  }, []);

  // WebSocket setup
  useEffect(() => {
    const ws = new FastlitWS();
    wsRef.current = ws;

    ws.onStatusChange(setStatus);

    ws.onRenderFull((msg) => {
      setTree(msg.tree);
      setError(null);
      // Full render always replaces everything — clear optimistic
      setOptimisticMainNodes(null);
    });

    ws.onRenderPatch((msg) => {
      setTree((prev) => {
        if (!prev) return prev;
        return applyPatch(prev, msg.ops);
      });
      setError(null);
      // DON'T clear optimistic here — the tree-update effect below
      // will clear it only when the tree's page matches the URL hash.
      // This prevents premature clearing when intermediate patches
      // (e.g. text input updates) arrive before the page-switch patch.
    });

    ws.onError((msg) => {
      setError(msg);
    });

    ws.connect();

    return () => {
      ws.disconnect();
    };
  }, []);

  // Extract sidebar radio info, cache pages, sync URL hash,
  // and clear optimistic nodes only when the tree's page matches the URL.
  useEffect(() => {
    if (!tree?.children) return;

    const sidebar = tree.children.find((c) => c.type === "sidebar");
    const radio = sidebar?.children?.find((c) => c.type === "radio");

    if (radio) {
      const opts = radio.props.options as string[];
      const idx = radio.props.index as number;
      const page = opts[idx] || "";

      sidebarRadioRef.current = { id: radio.id, options: opts };

      // Cache main content for this page
      const main = tree.children.filter((c) => c.type !== "sidebar");
      pageCacheRef.current.set(page, main);

      // Check if the tree's page matches the URL hash — if so, the server
      // has caught up and we can show real content instead of cached.
      const hash = decodeURIComponent(window.location.hash.slice(1));
      if (!hash || page === hash) {
        setOptimisticMainNodes(null);
      }

      // Sync URL hash (replaceState — don't push a history entry)
      const expectedHash = `#${encodeURIComponent(page)}`;
      if (window.location.hash !== expectedHash) {
        window.history.replaceState(null, "", expectedHash);
      }

      // On first render, if URL hash points to a different page, navigate
      const initPage = initialHashRef.current;
      if (initPage) {
        initialHashRef.current = "";
        if (initPage !== page) {
          const targetIdx = opts.indexOf(initPage);
          if (targetIdx >= 0) {
            // Update store directly for instant UI update
            storeRef.current.set(radio.id, initPage);
            sendEvent(radio.id, targetIdx);
          }
        }
      }
    } else {
      // No sidebar radio — always show real content
      setOptimisticMainNodes(null);
    }
  }, [tree, sendEvent]);

  // Browser back/forward navigation
  useEffect(() => {
    const handlePopState = () => {
      const page = decodeURIComponent(window.location.hash.slice(1));
      const radio = sidebarRadioRef.current;
      if (!page || !radio) return;

      const idx = radio.options.indexOf(page);
      if (idx < 0) return;

      // Update store directly for instant radio re-render
      storeRef.current.set(radio.id, page);

      // Show cached page instantly
      const cached = pageCacheRef.current.get(page);
      if (cached) {
        setOptimisticMainNodes(cached);
      }

      // Tell server about the navigation (async, non-blocking)
      wsRef.current?.send({ type: "widget_event", id: radio.id, value: idx });
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

  // Show optimistic (cached) nodes during navigation, real nodes otherwise
  const displayMainNodes = optimisticMainNodes || mainNodes;

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
