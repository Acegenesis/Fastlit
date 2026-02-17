import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useWidgetValue } from "../../context/WidgetStore";
import { cn } from "../../lib/utils";

export const SelectSlider: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const {
    label,
    options = [],
    isRange,
    help,
    disabled,
    labelVisibility,
  } = props;

  const defaultValue = isRange ? [0, options.length - 1] : 0;
  const [value, setValue] = useWidgetValue(nodeId, props.value ?? defaultValue);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newIndex = parseInt(e.target.value, 10);
    setValue(newIndex);
    sendEvent(nodeId, newIndex, { noRerun: props.noRerun ?? true });
  };

  const handleRangeChange = (index: 0 | 1) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const newIndex = parseInt(e.target.value, 10);
    const newValue = [...(Array.isArray(value) ? value : [0, options.length - 1])];
    newValue[index] = newIndex;
    // Ensure start <= end
    if (index === 0 && newIndex > newValue[1]) {
      newValue[1] = newIndex;
    } else if (index === 1 && newIndex < newValue[0]) {
      newValue[0] = newIndex;
    }
    setValue(newValue);
    sendEvent(nodeId, newValue, { noRerun: props.noRerun ?? true });
  };

  const showLabel = labelVisibility !== "hidden" && labelVisibility !== "collapsed";

  const currentIndex = Array.isArray(value) ? value[0] : (typeof value === "number" ? value : 0);
  const endIndex = Array.isArray(value) ? value[1] : options.length - 1;

  const displayValue = isRange
    ? `${options[Math.min(currentIndex, options.length - 1)]} - ${options[Math.min(endIndex, options.length - 1)]}`
    : options[Math.min(currentIndex, options.length - 1)] || "";

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

      <div className="space-y-2">
        {isRange ? (
          <>
            <div className="flex gap-4">
              <input
                type="range"
                min={0}
                max={options.length - 1}
                value={currentIndex}
                onChange={handleRangeChange(0)}
                disabled={!!disabled}
                className={cn(
                  "flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer",
                  disabled && "opacity-50 cursor-not-allowed"
                )}
              />
              <input
                type="range"
                min={0}
                max={options.length - 1}
                value={endIndex}
                onChange={handleRangeChange(1)}
                disabled={!!disabled}
                className={cn(
                  "flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer",
                  disabled && "opacity-50 cursor-not-allowed"
                )}
              />
            </div>
          </>
        ) : (
          <input
            type="range"
            min={0}
            max={options.length - 1}
            value={currentIndex}
            onChange={handleChange}
            disabled={!!disabled}
            className={cn(
              "w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer",
              disabled && "opacity-50 cursor-not-allowed"
            )}
          />
        )}

        <div className="flex justify-between text-xs text-gray-500">
          <span>{options[0]}</span>
          <span className="font-medium text-gray-700">{displayValue}</span>
          <span>{options[options.length - 1]}</span>
        </div>
      </div>
    </div>
  );
};
