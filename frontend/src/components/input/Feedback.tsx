import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useWidgetValue } from "../../context/WidgetStore";

const presets: Record<string, string[]> = {
  thumbs: ["👎", "👍"],
  faces: ["😞", "🙁", "😐", "🙂", "😀"],
  stars: ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"],
};

export const Feedback: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { preset, optionsMap, disabled } = props;
  const [selected, setSelected] = useWidgetValue(nodeId, null);

  const options =
    preset === "custom" && optionsMap
      ? Object.entries(optionsMap).map(([k, v]) => ({
          index: Number(k),
          label: String(v),
        }))
      : (presets[preset] || presets.thumbs).map((label, i) => ({
          index: i,
          label,
        }));

  const handleClick = (index: number) => {
    if (disabled) return;
    const newVal = selected === index ? null : index;
    setSelected(newVal);
    if (newVal !== null) {
      sendEvent(nodeId, newVal);
    }
  };

  return (
    <div className="flex gap-1 mb-3">
      {options.map((opt) => (
        <button
          key={opt.index}
          onClick={() => handleClick(opt.index)}
          disabled={!!disabled}
          className={`px-3 py-1.5 rounded-md text-sm transition-colors border ${
            selected === opt.index
              ? "bg-primary text-primary-foreground border-primary"
              : "bg-background hover:bg-muted border-border"
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
};
