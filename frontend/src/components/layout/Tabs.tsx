import React, { useState } from "react";
import type { NodeComponentProps } from "../../registry/registry";

export const Tabs: React.FC<NodeComponentProps> = ({
  props,
  children,
}) => {
  const labels = (props.labels as string[]) ?? [];
  const defaultIndex = (props.defaultIndex as number) ?? 0;
  const [activeIndex, setActiveIndex] = useState(defaultIndex);

  const childArray = React.Children.toArray(children);

  return (
    <div className="mb-3">
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
