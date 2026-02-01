import React, { useState } from "react";
import type { NodeComponentProps } from "../registry/registry";
import type { UINode } from "../runtime/types";
import { NodeRenderer } from "../registry/NodeRenderer";

export const TabsComponent: React.FC<NodeComponentProps & { node?: UINode; sendEvent: (id: string, value: any) => void }> = ({
  props,
  children,
  nodeId,
  sendEvent,
}) => {
  const labels = (props.labels as string[]) ?? [];
  const [activeIndex, setActiveIndex] = useState(0);

  // children is an array of rendered Tab components
  // We need to show only the active one
  const childArray = React.Children.toArray(children);

  return (
    <div className="mb-3">
      {/* Tab headers */}
      <div className="flex border-b border-gray-200">
        {labels.map((label, i) => (
          <button
            key={i}
            onClick={() => setActiveIndex(i)}
            className={`px-4 py-2 text-sm font-medium transition-colors
              ${
                i === activeIndex
                  ? "text-blue-600 border-b-2 border-blue-600"
                  : "text-gray-500 hover:text-gray-700"
              }`}
          >
            {label}
          </button>
        ))}
      </div>
      {/* Tab content — only show active */}
      <div className="pt-3">
        {childArray.map((child, i) => (
          <div key={i} className={i === activeIndex ? "block" : "hidden"}>
            {child}
          </div>
        ))}
      </div>
    </div>
  );
};
