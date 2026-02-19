import { applyPatch } from "./patcher";
import type { PatchOp, UINode } from "./types";

type Pending = {
  resolve: (node: UINode) => void;
  reject: (err: unknown) => void;
};

let worker: Worker | null = null;
let seq = 1;
const pending = new Map<number, Pending>();

function getWorker(): Worker | null {
  if (typeof Worker === "undefined") return null;
  if (worker) return worker;

  worker = new Worker(new URL("./patchWorker.ts", import.meta.url), {
    type: "module",
  });
  worker.onmessage = (event: MessageEvent<{ id: number; patched: UINode }>) => {
    const job = pending.get(event.data.id);
    if (!job) return;
    pending.delete(event.data.id);
    job.resolve(event.data.patched);
  };
  worker.onerror = (err) => {
    for (const [id, job] of pending.entries()) {
      pending.delete(id);
      job.reject(err);
    }
  };
  return worker;
}

export function applyPatchAsync(tree: UINode, ops: PatchOp[]): Promise<UINode> {
  const w = getWorker();
  if (!w) {
    return Promise.resolve(applyPatch(tree, ops));
  }

  return new Promise<UINode>((resolve, reject) => {
    const id = seq++;
    pending.set(id, { resolve, reject });
    w.postMessage({ id, tree, ops });
  });
}
