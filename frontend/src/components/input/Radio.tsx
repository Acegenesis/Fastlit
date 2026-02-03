import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useWidgetValue } from "../../context/WidgetStore";

export const Radio: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, options, disabled, help, horizontal, captions } = props;
  const opts = options as string[];
  const [value, setValue] = useWidgetValue(nodeId, opts[props.index ?? 0] ?? "");
  const currentIndex = Math.max(0, opts.indexOf(value));

  const handleChange = (i: number) => {
    if (disabled) return;
    setValue(opts[i] ?? "");
    sendEvent(nodeId, i, { noRerun: props.noRerun });
  };

  return (
    <div className="mb-3" title={help || undefined}>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <div className={horizontal ? "flex flex-wrap gap-4" : "space-y-1"}>
        {opts.map((opt, i) => (
          <label
            key={i}
            className={`flex items-center gap-2 cursor-pointer${
              disabled ? " opacity-50 cursor-not-allowed" : ""
            }`}
          >
            <input
              type="radio"
              name={nodeId}
              checked={i === currentIndex}
              onChange={() => handleChange(i)}
              disabled={!!disabled}
              className="h-4 w-4 border-gray-300 text-blue-600
                         focus:ring-2 focus:ring-blue-500"
            />
            <div>
              <span className="text-sm text-gray-700">{opt}</span>
              {captions && captions[i] && (
                <p className="text-xs text-gray-500">{captions[i]}</p>
              )}
            </div>
          </label>
        ))}
      </div>
    </div>
  );
};
