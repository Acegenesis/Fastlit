/**
 * WebSocket client for Fastlit.
 * Connects to the backend, sends widget events, receives render messages.
 */

import type {
  ServerMessage,
  WidgetEvent,
  RenderFullMessage,
  RenderPatchMessage,
  ErrorMessage,
} from "./types";

type OnRenderFull = (msg: RenderFullMessage) => void;
type OnRenderPatch = (msg: RenderPatchMessage) => void;
type OnError = (msg: ErrorMessage) => void;
type OnStatusChange = (status: "connected" | "disconnected" | "connecting") => void;

const BASE_DELAY = 2000;
const MAX_DELAY = 30000;

export class FastlitWS {
  private ws: WebSocket | null = null;
  private url: string;
  private onRenderFullCb: OnRenderFull | null = null;
  private onRenderPatchCb: OnRenderPatch | null = null;
  private onErrorCb: OnError | null = null;
  private onStatusChangeCb: OnStatusChange | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectAttempts = 0;

  constructor(url?: string) {
    // Default: connect to same host on /ws
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    this.url = url ?? `${protocol}//${window.location.host}/ws`;
  }

  connect(): void {
    this.onStatusChangeCb?.("connecting");
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0; // reset backoff on successful connection
      this.onStatusChangeCb?.("connected");
    };

    this.ws.onmessage = (event) => {
      try {
        const msg: ServerMessage = JSON.parse(event.data);
        switch (msg.type) {
          case "render_full":
            this.onRenderFullCb?.(msg);
            break;
          case "render_patch":
            this.onRenderPatchCb?.(msg);
            break;
          case "error":
            this.onErrorCb?.(msg);
            break;
        }
      } catch (e) {
        console.error("Failed to parse server message:", e);
      }
    };

    this.ws.onclose = () => {
      this.onStatusChangeCb?.("disconnected");
      this.scheduleReconnect();
    };

    this.ws.onerror = () => {
      // onclose will fire after onerror
    };
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;
    // Exponential backoff: 2s → 4s → 8s → 16s → 30s (capped)
    const delay = Math.min(BASE_DELAY * Math.pow(2, this.reconnectAttempts), MAX_DELAY);
    this.reconnectAttempts++;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }

  send(msg: WidgetEvent): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    }
  }

  onRenderFull(cb: OnRenderFull): void {
    this.onRenderFullCb = cb;
  }

  onRenderPatch(cb: OnRenderPatch): void {
    this.onRenderPatchCb = cb;
  }

  onError(cb: OnError): void {
    this.onErrorCb = cb;
  }

  onStatusChange(cb: OnStatusChange): void {
    this.onStatusChangeCb = cb;
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
  }
}
