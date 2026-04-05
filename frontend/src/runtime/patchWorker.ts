/// <reference lib="webworker" />

import type { PatchOp, UINode } from "./types";

const UNSAFE_PROP_KEYS = new Set(["__proto__", "constructor", "prototype"]);

interface PatchJob {
  id: number;
  tree: UINode;
  ops: PatchOp[];
}

function applyPatch(tree: UINode, ops: PatchOp[]): UINode {
  let result = tree;
  for (const op of ops) {
    result = applyOp(result, op);
  }
  return result;
}

function applyOp(tree: UINode, op: PatchOp): UINode {
  switch (op.op) {
    case "replace":
      return replaceNode(tree, op.id, op.node!);
    case "updateProps":
      return updateProps(tree, op.id, op.props!);
    case "streamText":
      return streamText(tree, op.id, op.props ?? {});
    case "insertChild":
      return insertChild(tree, op.parentId!, op.index!, op.node!);
    case "remove":
      return removeNode(tree, op.id);
    case "moveChild":
      return moveChild(tree, op.parentId!, op.id, op.index!);
    default:
      return tree;
  }
}

function streamText(tree: UINode, id: string, props: Record<string, any>): UINode {
  if (tree.id === id) {
    const currentText = typeof tree.props?.text === "string" ? tree.props.text : "";
    const chunk = typeof props.chunk === "string" ? props.chunk : "";
    return {
      ...tree,
      props: mergePropsSafely(tree.props, {
        text: currentText + chunk,
        isStreaming: props.done === true ? false : true,
      }),
    };
  }
  if (!tree.children?.length) return tree;
  const newChildren = tree.children.map((child) => streamText(child, id, props));
  if (newChildren.every((c, i) => c === tree.children![i])) return tree;
  return { ...tree, children: newChildren };
}

function replaceNode(tree: UINode, id: string, newNode: UINode): UINode {
  if (tree.id === id) return sanitizeNode(newNode);
  if (!tree.children?.length) return tree;
  const newChildren = tree.children.map((child) => replaceNode(child, id, newNode));
  if (newChildren.every((c, i) => c === tree.children![i])) return tree;
  return { ...tree, children: newChildren };
}

function updateProps(tree: UINode, id: string, props: Record<string, any>): UINode {
  if (tree.id === id) return { ...tree, props: mergePropsSafely(tree.props, props) };
  if (!tree.children?.length) return tree;
  const newChildren = tree.children.map((child) => updateProps(child, id, props));
  if (newChildren.every((c, i) => c === tree.children![i])) return tree;
  return { ...tree, children: newChildren };
}

function insertChild(
  tree: UINode,
  parentId: string,
  index: number,
  node: UINode
): UINode {
  if (tree.id === parentId) {
    const children = [...(tree.children ?? [])];
    children.splice(index, 0, sanitizeNode(node));
    return { ...tree, children };
  }
  if (!tree.children?.length) return tree;
  const newChildren = tree.children.map((child) => insertChild(child, parentId, index, node));
  if (newChildren.every((c, i) => c === tree.children![i])) return tree;
  return { ...tree, children: newChildren };
}

function mergePropsSafely(
  current: Record<string, any> | undefined,
  next: Record<string, any>
): Record<string, any> {
  const merged = Object.create(null) as Record<string, any>;
  for (const source of [current ?? {}, next]) {
    for (const [key, value] of Object.entries(source)) {
      if (UNSAFE_PROP_KEYS.has(key)) continue;
      merged[key] = value;
    }
  }
  return merged;
}

function sanitizeNode(node: UINode): UINode {
  return {
    ...node,
    props: mergePropsSafely(undefined, node.props ?? {}),
    children: node.children?.map((child) => sanitizeNode(child)),
  };
}

function removeNode(tree: UINode, id: string): UINode {
  if (tree.id === id || !tree.children?.length) return tree;
  const newChildren = tree.children.filter((child) => child.id !== id).map((child) => removeNode(child, id));
  if (
    newChildren.length === tree.children.length &&
    newChildren.every((c, i) => c === tree.children![i])
  ) {
    return tree;
  }
  return { ...tree, children: newChildren };
}

function moveChild(
  tree: UINode,
  parentId: string,
  id: string,
  index: number
): UINode {
  if (tree.id === parentId) {
    const children = [...(tree.children ?? [])];
    const currentIndex = children.findIndex((child) => child.id === id);
    if (currentIndex < 0 || currentIndex === index) return tree;
    const [node] = children.splice(currentIndex, 1);
    children.splice(index, 0, node);
    return { ...tree, children };
  }
  if (!tree.children?.length) return tree;
  const newChildren = tree.children.map((child) => moveChild(child, parentId, id, index));
  if (newChildren.every((c, i) => c === tree.children![i])) return tree;
  return { ...tree, children: newChildren };
}

self.onmessage = (event: MessageEvent<PatchJob>) => {
  const { id, tree, ops } = event.data;
  const patched = applyPatch(tree, ops);
  (self as unknown as Worker).postMessage({ id, patched });
};

export {};
