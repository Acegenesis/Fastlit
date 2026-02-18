import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useWidgetValue } from "../../context/WidgetStore";
import { Label } from "@/components/ui/label";

export const SegmentedControl: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const {
    label,
    options,
    selectionMode,
    help,
    disabled,
    labelVisibility,
  } = props;
  const isMulti = selectionMode === "multi";
  const [selected, setSelected] = useWidgetValue(nodeId, props.defaultIndex);

  const handleClick = (index: number) => {
    if (disabled) return;

    if (isMulti) {
      const current = Array.isArray(selected) ? [...selected] : [];
      const pos = current.indexOf(index);
      if (pos >= 0) {
        current.splice(pos, 1);
      } else {
        current.push(index);
      }
      setSelected(current);
      sendEvent(nodeId, current);
    } else {
      setSelected(index);
      sendEvent(nodeId, index);
    }
  };

  const isSelected = (index: number): boolean => {
    if (isMulti) {
      return Array.isArray(selected) && selected.includes(index);
    }
    return selected === index;
  };

  return (
    <div className="mb-3" title={help || undefined}>
      {labelVisibility !== "collapsed" && (
        <Label
          className={`mb-2 block ${
            labelVisibility === "hidden" ? "sr-only" : ""
          }`}
        >
          {label}
        </Label>
      )}
      <div className="inline-flex rounded-lg border border-border overflow-hidden">
        {(options as string[]).map((opt: string, i: number) => (
          <button
            key={i}
            onClick={() => handleClick(i)}
            disabled={!!disabled}
            className={`px-4 py-2 text-sm font-medium transition-colors border-r last:border-r-0 border-border ${
              isSelected(i)
                ? "bg-primary text-primary-foreground"
                : "bg-background hover:bg-muted text-foreground"
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
};
