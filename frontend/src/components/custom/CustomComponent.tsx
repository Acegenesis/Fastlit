import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type { NodeComponentProps } from "../../registry/registry";

/**
 * CustomComponent — renders a Streamlit-compatible custom component inside
 * a sandboxed iframe and bridges props/events via the streamlit: postMessage
 * protocol.
 *
 * Protocol (Streamlit-compatible):
 *   Parent → iframe  {type:"streamlit:render",  args:{...}, disabled:false, theme:{...}}
 *   iframe → parent  {type:"streamlit:componentReady", apiVersion:1}
 *   iframe → parent  {type:"streamlit:setComponentValue", value:any}
 *   iframe → parent  {type:"streamlit:setFrameHeight", height:number}
 */
export const CustomComponent: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { componentUrl, componentName, args } = props as {
    componentUrl: string;
    componentName: string;
    args: Record<string, unknown>;
    default: unknown;
  };

  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [frameHeight, setFrameHeight] = useState<number>(150);
  // Track whether the iframe has announced it is ready
  const readyRef = useRef(false);
  // Keep a stable reference to the latest args so the message handler can
  // send up-to-date props without stale closures.
  const argsRef = useRef(args);
  useEffect(() => {
    argsRef.current = args;
  }, [args]);

  const expectedOrigin = useMemo(() => {
    try {
      return new URL(componentUrl, window.location.origin).origin;
    } catch {
      return null;
    }
  }, [componentUrl]);

  /** Dispatch streamlit:render with the current args into the iframe. */
  const sendProps = useCallback(() => {
    if (!expectedOrigin) return;
    iframeRef.current?.contentWindow?.postMessage(
      {
        type: "streamlit:render",
        args: argsRef.current ?? {},
        disabled: false,
        theme: {},
      },
      expectedOrigin,
    );
  }, [expectedOrigin]);

  /** Listen for messages from the iframe. */
  useEffect(() => {
    const handleMessage = (ev: MessageEvent) => {
      // Only process messages from our own iframe
      if (ev.source !== iframeRef.current?.contentWindow) return;
      if (!expectedOrigin || ev.origin !== expectedOrigin) return;
      const data = ev.data ?? {};
      if (typeof data !== "object" || data === null) return;
      const msgType: string = data.type ?? "";

      if (msgType === "streamlit:componentReady") {
        readyRef.current = true;
        sendProps();
      } else if (msgType === "streamlit:setComponentValue") {
        // Forward the value to the Fastlit backend via the widget store
        sendEvent(nodeId, data.value ?? null);
      } else if (
        msgType === "streamlit:setFrameHeight" &&
        typeof data.height === "number" &&
        data.height > 0
      ) {
        setFrameHeight(data.height);
      }
    };

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [expectedOrigin, nodeId, sendEvent, sendProps]);

  /** Re-send props whenever args change (after the iframe is ready). */
  useEffect(() => {
    if (readyRef.current) {
      sendProps();
    }
  }, [args, sendProps]); // eslint-disable-line react-hooks/exhaustive-deps

  /** When the iframe reloads (hard refresh), resend props if already ready. */
  const handleLoad = useCallback(() => {
    if (readyRef.current) {
      sendProps();
    }
  }, [sendProps]);

  return (
    <iframe
      ref={iframeRef}
      src={componentUrl}
      onLoad={handleLoad}
      sandbox="allow-scripts allow-same-origin"
      referrerPolicy="no-referrer"
      style={{
        width: "100%",
        height: `${frameHeight}px`,
        border: "none",
        display: "block",
      }}
      allow="camera; microphone"
      title={`fastlit-component-${componentName}-${nodeId}`}
    />
  );
};
