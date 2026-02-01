import React, { useState, useEffect } from "react";
import type { NodeComponentProps } from "../registry/registry";
import { useWidgetPublish } from "../context/WidgetStore";

export const Selectbox: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, options } = props;
  const opts = options as string[];
  const [currentIndex, setCurrentIndex] = useState<number>(props.index ?? 0);
  const publish = useWidgetPublish();

  useEffect(() => { publish(nodeId, opts[props.index ?? 0] ?? ""); }, []);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const idx = parseInt(e.target.value, 10);
    setCurrentIndex(idx);
    publish(nodeId, opts[idx] ?? "");
    sendEvent(nodeId, idx);
  };

  return (
    <div className="mb-3">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <select
        value={currentIndex}
        onChange={handleChange}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                   text-sm bg-white"
      >
        {opts.map((opt, i) => (
          <option key={i} value={i}>
            {opt}
          </option>
        ))}
      </select>
    </div>
  );
};
