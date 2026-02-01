import React, { useState, useEffect } from "react";
import type { NodeComponentProps } from "../registry/registry";
import { useWidgetPublish } from "../context/WidgetStore";

export const Radio: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, options } = props;
  const opts = options as string[];
  const [currentIndex, setCurrentIndex] = useState<number>(props.index ?? 0);
  const publish = useWidgetPublish();

  useEffect(() => { publish(nodeId, opts[props.index ?? 0] ?? ""); }, []);

  const handleChange = (i: number) => {
    setCurrentIndex(i);
    publish(nodeId, opts[i] ?? "");
    sendEvent(nodeId, i);
  };

  return (
    <div className="mb-3">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <div className="space-y-1">
        {opts.map((opt, i) => (
          <label key={i} className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name={nodeId}
              checked={i === currentIndex}
              onChange={() => handleChange(i)}
              className="h-4 w-4 border-gray-300 text-blue-600
                         focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">{opt}</span>
          </label>
        ))}
      </div>
    </div>
  );
};
