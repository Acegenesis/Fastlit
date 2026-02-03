import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useWidgetValue } from "../../context/WidgetStore";

export const TextInput: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, placeholder, maxChars, inputType, disabled, help, autocomplete } = props;
  const [value, setValue] = useWidgetValue(nodeId, props.value ?? "");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = e.target.value;
    if (maxChars && val.length > maxChars) {
      val = val.slice(0, maxChars);
    }
    setValue(val);
    sendEvent(nodeId, val, { noRerun: props.noRerun });
  };

  return (
    <div className="mb-3" title={help || undefined}>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <input
        type={inputType === "password" ? "password" : "text"}
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        maxLength={maxChars ?? undefined}
        disabled={!!disabled}
        autoComplete={autocomplete || undefined}
        className={`w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                   text-sm${disabled ? " opacity-50 bg-gray-100 cursor-not-allowed" : ""}`}
      />
    </div>
  );
};
