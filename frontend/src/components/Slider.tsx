import React from "react";
import type { NodeComponentProps } from "../registry/registry";
import { useWidgetValue } from "../context/WidgetStore";

export const Slider: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, min, max, step } = props;
  const [value, setValue] = useWidgetValue(nodeId, props.value);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setValue(val);
    sendEvent(nodeId, val);
  };

  return (
    <div className="mb-3">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <div className="flex items-center gap-3">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={handleChange}
          className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
        />
        <span className="text-sm font-mono text-gray-600 min-w-[3rem] text-right">
          {value}
        </span>
      </div>
    </div>
  );
};
