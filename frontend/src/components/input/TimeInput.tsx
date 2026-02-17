import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useWidgetValue } from "../../context/WidgetStore";
import { cn } from "../../lib/utils";

export const TimeInput: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const {
    label,
    step = 900, // 15 minutes in seconds
    disabled,
    help,
    labelVisibility,
  } = props;

  const [value, setValue] = useWidgetValue(nodeId, props.value || "00:00");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setValue(newValue);
    sendEvent(nodeId, newValue, { noRerun: props.noRerun });
  };

  const showLabel = labelVisibility !== "hidden" && labelVisibility !== "collapsed";

  // Convert step from seconds to the step attribute format (in seconds for time input)
  const stepInSeconds = Math.max(1, step);

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

      <div className="relative">
        <input
          type="time"
          value={value || "00:00"}
          onChange={handleChange}
          disabled={!!disabled}
          step={stepInSeconds}
          className={cn(
            "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm font-mono",
            "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
            "appearance-none [&::-webkit-calendar-picker-indicator]:hidden",
            disabled ? "opacity-50 cursor-not-allowed bg-gray-100" : "bg-white"
          )}
        />
        {/* Clock icon */}
        <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
      </div>
    </div>
  );
};
