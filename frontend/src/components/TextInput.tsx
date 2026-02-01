import React, { useState, useEffect } from "react";
import type { NodeComponentProps } from "../registry/registry";
import { useWidgetPublish } from "../context/WidgetStore";

export const TextInput: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, placeholder, maxChars } = props;
  const [localValue, setLocalValue] = useState<string>(props.value ?? "");
  const publish = useWidgetPublish();

  useEffect(() => { publish(nodeId, props.value ?? ""); }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = e.target.value;
    if (maxChars && val.length > maxChars) {
      val = val.slice(0, maxChars);
    }
    setLocalValue(val);
    publish(nodeId, val);
    sendEvent(nodeId, val);
  };

  return (
    <div className="mb-3">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <input
        type="text"
        value={localValue}
        onChange={handleChange}
        placeholder={placeholder}
        maxLength={maxChars ?? undefined}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                   text-sm"
      />
    </div>
  );
};
