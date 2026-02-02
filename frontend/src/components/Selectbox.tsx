import React from "react";
import type { NodeComponentProps } from "../registry/registry";
import { useWidgetValue } from "../context/WidgetStore";

export const Selectbox: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, options, disabled, help, placeholder } = props;
  const opts = options as string[];
  const [value, setValue] = useWidgetValue(nodeId, opts[props.index ?? 0] ?? "");
  const currentIndex = Math.max(0, opts.indexOf(value));

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const idx = parseInt(e.target.value, 10);
    setValue(opts[idx] ?? "");
    sendEvent(nodeId, idx);
  };

  return (
    <div className="mb-3" title={help || undefined}>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <select
        value={currentIndex}
        onChange={handleChange}
        disabled={!!disabled}
        className={`w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                   text-sm bg-white${disabled ? " opacity-50 cursor-not-allowed" : ""}`}
      >
        {placeholder && currentIndex === -1 && (
          <option value={-1} disabled>
            {placeholder}
          </option>
        )}
        {opts.map((opt, i) => (
          <option key={i} value={i}>
            {opt}
          </option>
        ))}
      </select>
    </div>
  );
};
