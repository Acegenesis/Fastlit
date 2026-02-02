import React from "react";
import type { NodeComponentProps } from "../registry/registry";
import { useWidgetValue } from "../context/WidgetStore";

export const TextArea: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, height, placeholder, maxChars } = props;
  const [value, setValue] = useWidgetValue(nodeId, props.value ?? "");

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    let val = e.target.value;
    if (maxChars && val.length > maxChars) {
      val = val.slice(0, maxChars);
    }
    setValue(val);
    sendEvent(nodeId, val);
  };

  return (
    <div className="mb-3">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <textarea
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        maxLength={maxChars ?? undefined}
        style={{ height: height ? `${height}px` : undefined }}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                   text-sm resize-y"
      />
    </div>
  );
};
