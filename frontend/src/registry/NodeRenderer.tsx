/**
 * Recursive node renderer: looks up the component in the registry
 * and renders it with its props and children.
 */

import React from "react";
import type { UINode } from "../runtime/types";
import { getComponent } from "./registry";

interface NodeRendererProps {
  node: UINode;
  sendEvent: (id: string, value: any) => void;
}

function FallbackComponent({ nodeId, props }: { nodeId: string; props: Record<string, any> }) {
  return (
    <div className="p-2 my-1 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
      Unknown component: <code>{nodeId}</code>
      <pre className="text-xs mt-1">{JSON.stringify(props, null, 2)}</pre>
    </div>
  );
}

export const NodeRenderer: React.FC<NodeRendererProps> = ({ node, sendEvent }) => {
  const children = node.children?.map((child) => (
    <NodeRenderer key={child.id} node={child} sendEvent={sendEvent} />
  ));

  // The root node is a transparent container — just render its children
  if (node.type === "root") {
    return <>{children}</>;
  }

  const Component = getComponent(node.type);

  if (!Component) {
    return <FallbackComponent nodeId={node.id} props={node.props} />;
  }

  return (
    <Component nodeId={node.id} props={node.props} sendEvent={sendEvent}>
      {children}
    </Component>
  );
};
