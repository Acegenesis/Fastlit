/// <reference lib="webworker" />

import type { PatchOp, UINode } from "./types";

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
    case "insertChild":
      return insertChild(tree, op.parentId!, op.index!, op.node!);
    case "remove":
      return removeNode(tree, op.id);
    default:
      return tree;
  }
}

function replaceNode(tree: UINode, id: string, newNode: UINode): UINode {
  if (tree.id === id) return newNode;
  if (!tree.children?.length) return tree;
  const newChildren = tree.children.map((child) => replaceNode(child, id, newNode));
  if (newChildren.every((c, i) => c === tree.children![i])) return tree;
  return { ...tree, children: newChildren };
}

function updateProps(tree: UINode, id: string, props: Record<string, any>): UINode {
  if (tree.id === id) return { ...tree, props: { ...tree.props, ...props } };
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
    children.splice(index, 0, node);
    return { ...tree, children };
  }
  if (!tree.children?.length) return tree;
  const newChildren = tree.children.map((child) => insertChild(child, parentId, index, node));
  if (newChildren.every((c, i) => c === tree.children![i])) return tree;
  return { ...tree, children: newChildren };
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

self.onmessage = (event: MessageEvent<PatchJob>) => {
  const { id, tree, ops } = event.data;
  const patched = applyPatch(tree, ops);
  (self as unknown as Worker).postMessage({ id, patched });
};

export {};
