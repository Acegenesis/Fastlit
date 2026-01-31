import React, { useEffect, useRef, useState, useCallback } from "react";
import { FastlitWS } from "./runtime/ws";
import { applyPatch } from "./runtime/patcher";
import { NodeRenderer } from "./registry/NodeRenderer";
import type { UINode, ErrorMessage } from "./runtime/types";

type ConnectionStatus = "connecting" | "connected" | "disconnected";

export const App: React.FC = () => {
  const [tree, setTree] = useState<UINode | null>(null);
  const [error, setError] = useState<ErrorMessage | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const wsRef = useRef<FastlitWS | null>(null);

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

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* Connection status indicator */}
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

      {/* UI tree */}
      {tree ? (
        <NodeRenderer node={tree} sendEvent={sendEvent} />
      ) : (
        status === "connected" && (
          <p className="text-gray-400 text-sm">Waiting for app to render...</p>
        )
      )}
    </div>
  );
};
