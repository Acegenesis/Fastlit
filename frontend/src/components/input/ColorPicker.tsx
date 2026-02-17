import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useWidgetValue } from "../../context/WidgetStore";

export const ColorPicker: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const {
    label,
    disabled,
    help,
    labelVisibility,
  } = props;

  const [color, setColor] = useWidgetValue(nodeId, props.value || "#000000");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newColor = e.target.value;
    setColor(newColor);
    sendEvent(nodeId, newColor, { noRerun: props.noRerun });
  };

  const showLabel = labelVisibility !== "hidden" && labelVisibility !== "collapsed";

  return (
    <div className="mb-3">
      {showLabel && label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {help && (
            <span className="ml-1 text-gray-400 cursor-help" title={help}>
              ?
            </span>
          )}
        </label>
      )}

      <div className="flex items-center gap-3">
        <input
          type="color"
          value={color}
          onChange={handleChange}
          disabled={!!disabled}
          className={`w-12 h-10 p-1 border border-gray-300 rounded cursor-pointer
            ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
        />
        <input
          type="text"
          value={color}
          onChange={(e) => {
            const val = e.target.value;
            // Validate hex color format
            if (/^#[0-9A-Fa-f]{0,6}$/.test(val) || val === "") {
              setColor(val);
              if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                sendEvent(nodeId, val, { noRerun: props.noRerun });
              }
            }
          }}
          disabled={!!disabled}
          placeholder="#000000"
          className={`w-24 px-2 py-1 text-sm border border-gray-300 rounded
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
            font-mono uppercase
            ${disabled ? "opacity-50 cursor-not-allowed bg-gray-100" : "bg-white"}`}
        />
        <div
          className="w-8 h-8 rounded border border-gray-300 shadow-inner"
          style={{ backgroundColor: color }}
        />
      </div>
    </div>
  );
};
