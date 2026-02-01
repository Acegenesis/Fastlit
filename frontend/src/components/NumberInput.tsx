import React, { useState, useEffect } from "react";
import type { NodeComponentProps } from "../registry/registry";
import { useWidgetPublish } from "../context/WidgetStore";

export const NumberInput: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, min, max, step } = props;
  const [localValue, setLocalValue] = useState<number>(props.value ?? 0);
  const publish = useWidgetPublish();

  useEffect(() => { publish(nodeId, props.value ?? 0); }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    if (raw === "" || raw === "-") {
      setLocalValue(0);
      return;
    }
    let val = parseFloat(raw);
    if (isNaN(val)) return;
    if (min != null && val < min) val = min;
    if (max != null && val > max) val = max;
    setLocalValue(val);
    publish(nodeId, val);
    sendEvent(nodeId, val);
  };

  const increment = (dir: 1 | -1) => {
    let val = localValue + dir * (step ?? 1);
    if (min != null && val < min) val = min;
    if (max != null && val > max) val = max;
    setLocalValue(val);
    publish(nodeId, val);
    sendEvent(nodeId, val);
  };

  return (
    <div className="mb-3">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <div className="flex items-center gap-1">
        <button
          onClick={() => increment(-1)}
          className="px-2 py-2 border border-gray-300 rounded-l-md bg-gray-50
                     hover:bg-gray-100 text-gray-600 text-sm"
        >
          −
        </button>
        <input
          type="number"
          value={localValue}
          onChange={handleChange}
          min={min ?? undefined}
          max={max ?? undefined}
          step={step ?? undefined}
          className="w-24 px-3 py-2 border-t border-b border-gray-300 text-center
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                     text-sm [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none
                     [&::-webkit-inner-spin-button]:appearance-none"
        />
        <button
          onClick={() => increment(1)}
          className="px-2 py-2 border border-gray-300 rounded-r-md bg-gray-50
                     hover:bg-gray-100 text-gray-600 text-sm"
        >
          +
        </button>
      </div>
    </div>
  );
};
