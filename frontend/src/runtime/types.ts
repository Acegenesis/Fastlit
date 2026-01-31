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

export interface ErrorMessage {
  type: "error";
  message: string;
  traceback?: string;
}

export type ServerMessage = RenderFullMessage | RenderPatchMessage | ErrorMessage;

// --- Client to Server ---

export interface WidgetEvent {
  type: "widget_event";
  id: string;
  value: any;
}

export type ClientMessage = WidgetEvent;
