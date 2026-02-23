/** Wire protocol types shared between frontend and backend. */

export interface UINode {
  type: string;
  id: string;
  props: Record<string, any>;
  children?: UINode[];
}

// --- Server to Client ---

export interface RenderFullMessage {
  type: "render_full";
  rev: number;
  tree: UINode;
}

export interface PatchOp {
  op: "replace" | "updateProps" | "insertChild" | "remove";
  id: string;
  node?: UINode;
  props?: Record<string, any>;
  parentId?: string;
  index?: number;
}

export interface RenderPatchMessage {
  type: "render_patch";
  rev: number;
  ops: PatchOp[];
}

export interface RenderPatchCompactMessage {
  type: "render_patch_compact";
  rev: number;
  // [op, id, parentId, index, props, node]
  ops: [PatchOp["op"], string, string | undefined, number | undefined, Record<string, any> | undefined, any | undefined][];
}

export interface RenderPatchCompressedMessage {
  type: "render_patch_z";
  rev: number;
  encoding: "zlib+base64";
  ops: string;
}

export interface ErrorMessage {
  type: "error";
  message: string;
  traceback?: string;
}

export interface RuntimeEventPayload {
  kind: "spinner";
  id: string;
  text: string;
  active: boolean;
}

export interface RuntimeEventMessage {
  type: "runtime_event";
  event: RuntimeEventPayload;
}

export type ServerMessage =
  | RenderFullMessage
  | RenderPatchMessage
  | RenderPatchCompactMessage
  | RenderPatchCompressedMessage
  | RuntimeEventMessage
  | ErrorMessage;

// --- Client to Server ---

export interface WidgetEvent {
  type: "widget_event";
  id: string;
  value: any;
  noRerun?: boolean; // If true, server stores value but doesn't rerun script
}

export type ClientMessage = WidgetEvent;
