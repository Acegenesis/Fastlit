/**
 * WebSocket client for Fastlit.
 * Connects to the backend, sends widget events, receives render messages.
 */

import type {
  ServerMessage,
  WidgetEvent,
  RenderFullMessage,
  RenderPatchMessage,
  RuntimeEventMessage,
  PatchOp,
  ErrorMessage,
} from "./types";

type OnRenderFull = (msg: RenderFullMessage) => void;
type OnRenderPatch = (msg: RenderPatchMessage) => void;
type OnError = (msg: ErrorMessage) => void;
type OnRuntimeEvent = (msg: RuntimeEventMessage) => void;
type OnStatusChange = (status: "connected" | "disconnected" | "connecting") => void;

const BASE_DELAY = 2000;
const MAX_DELAY = 30000;
const MAX_INTERNED_NODES = 500;
const internedNodes = new Map<string, any>();

function setInternedNode(token: string, node: any): void {
  if (internedNodes.has(token)) internedNodes.delete(token);
  internedNodes.set(token, node);
  if (internedNodes.size <= MAX_INTERNED_NODES) return;
  const oldest = internedNodes.keys().next().value;
  if (oldest !== undefined) internedNodes.delete(oldest);
}

function getInternedNode(token: string): any {
  const node = internedNodes.get(token);
  if (node === undefined) return undefined;
  // Refresh recency (LRU behavior).
  internedNodes.delete(token);
  internedNodes.set(token, node);
  return node;
}

function decodeCompactOps(
  compact: [PatchOp["op"], string, string | undefined, number | undefined, Record<string, any> | undefined, any | undefined][]
): PatchOp[] {
  return compact.map(([op, id, parentId, index, props, node]) => ({
    // compact node interning:
    // - {"$def": [token, fullNode]} defines token + payload
    // - {"$ref": token} references previously defined node
    // - otherwise node is a plain full payload
    op,
    id,
    parentId,
    index,
    props,
    node:
      node && typeof node === "object" && "$def" in node
        ? (() => {
            const [token, fullNode] = (node as { $def: [string, any] }).$def;
            setInternedNode(token, fullNode);
            return fullNode;
          })()
        : node && typeof node === "object" && "$ref" in node
          ? getInternedNode((node as { $ref: string }).$ref)
          : node,
  }));
}

async function inflateZlibBase64(base64Data: string): Promise<string> {
  const binary = atob(base64Data);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);

  if (typeof DecompressionStream === "undefined") {
    throw new Error("DecompressionStream is not available in this browser");
  }

  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate"));
  const decompressed = await new Response(stream).arrayBuffer();
  return new TextDecoder().decode(decompressed);
}

export class FastlitWS {
  private ws: WebSocket | null = null;
  private url: string;
  private onRenderFullCb: OnRenderFull | null = null;
  private onRenderPatchCb: OnRenderPatch | null = null;
  private onErrorCb: OnError | null = null;
  private onRuntimeEventCb: OnRuntimeEvent | null = null;
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
      internedNodes.clear();
      this.onStatusChangeCb?.("connected");
    };

    this.ws.onmessage = async (event) => {
      try {
        const msg: ServerMessage = JSON.parse(event.data);
        switch (msg.type) {
          case "render_full":
            this.onRenderFullCb?.(msg);
            break;
          case "render_patch":
            this.onRenderPatchCb?.(msg);
            break;
          case "render_patch_compact":
            this.onRenderPatchCb?.({
              type: "render_patch",
              rev: msg.rev,
              ops: decodeCompactOps(msg.ops),
            });
            break;
          case "render_patch_z": {
            const text = await inflateZlibBase64(msg.ops);
            const decoded = JSON.parse(text) as ServerMessage;
            if (decoded.type === "render_patch_compact") {
              this.onRenderPatchCb?.({
                type: "render_patch",
                rev: decoded.rev,
                ops: decodeCompactOps(decoded.ops),
              });
            } else if (decoded.type === "render_patch") {
              this.onRenderPatchCb?.(decoded);
            } else {
              console.warn("Unexpected compressed patch payload type:", decoded.type);
            }
            break;
          }
          case "error":
            this.onErrorCb?.(msg);
            break;
          case "runtime_event":
            this.onRuntimeEventCb?.(msg);
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

  onRuntimeEvent(cb: OnRuntimeEvent): void {
    this.onRuntimeEventCb = cb;
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
