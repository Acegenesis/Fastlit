import React from "react";
import type { NodeComponentProps } from "../registry/registry";
import { useWidgetValue } from "../context/WidgetStore";

export const Checkbox: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, disabled, help } = props;
  const [checked, setChecked] = useWidgetValue(nodeId, !!props.value);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setChecked(e.target.checked);
    sendEvent(nodeId, e.target.checked);
  };

  return (
    <div className="mb-3 flex items-center gap-2" title={help || undefined}>
      <input
        type="checkbox"
        checked={checked}
        onChange={handleChange}
        disabled={!!disabled}
        className={`h-4 w-4 rounded border-gray-300 text-blue-600
                   focus:ring-2 focus:ring-blue-500${disabled ? " opacity-50 cursor-not-allowed" : ""}`}
      />
      <label className="text-sm text-gray-700">{label}</label>
    </div>
  );
};
