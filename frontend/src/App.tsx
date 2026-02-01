import React, { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { FastlitWS } from "./runtime/ws";
import { applyPatch } from "./runtime/patcher";
import { NodeRenderer } from "./registry/NodeRenderer";
import { WidgetStoreProvider } from "./context/WidgetStore";
import type { UINode, ErrorMessage } from "./runtime/types";

type ConnectionStatus = "connecting" | "connected" | "disconnected";

export const App: React.FC = () => {
  const [tree, setTree] = useState<UINode | null>(null);
  const [error, setError] = useState<ErrorMessage | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const wsRef = useRef<FastlitWS | null>(null);

  // Send events immediately — no debounce.
  // Widgets use local React state (instant), server patches only update non-widget nodes.
  // Server-side drain (timeout=0) coalesces events that pile up during script execution.
  const sendEvent = useCallback((id: string, value: any) => {
    wsRef.current?.send({ type: "widget_event", id, value });
  }, []);

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

  // Check if the tree has a sidebar child
  const hasSidebar = useMemo(() => {
    if (!tree?.children) return false;
    return tree.children.some((c) => c.type === "sidebar");
  }, [tree]);

  // Split tree children into sidebar and main content
  const { sidebarNodes, mainNodes } = useMemo(() => {
    if (!tree?.children) return { sidebarNodes: [] as UINode[], mainNodes: [] as UINode[] };
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

  return (
    <WidgetStoreProvider>
      {/* Render sidebar nodes at top level (they position themselves fixed) */}
      {sidebarNodes.map((node) => (
        <NodeRenderer key={node.id} node={node} sendEvent={sendEvent} />
      ))}

      {/* Main content area — shifted right if sidebar exists */}
      <div className={`${hasSidebar ? "ml-64" : ""} max-w-4xl mx-auto px-6 py-8`}>
        {/* Connection status */}
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

        {/* Error display */}
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

        {/* Main content nodes */}
        {tree ? (
          mainNodes.map((node) => (
            <NodeRenderer key={node.id} node={node} sendEvent={sendEvent} />
          ))
        ) : (
          status === "connected" && (
            <p className="text-gray-400 text-sm">Waiting for app to render...</p>
          )
        )}
      </div>
    </WidgetStoreProvider>
  );
};
