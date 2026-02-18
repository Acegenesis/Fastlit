import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useWidgetValue } from "../../context/WidgetStore";
import { Slider as ShadcnSlider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";

export const Slider: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, min, max, step, disabled, help, isRange } = props;
  const [value, setValue] = useWidgetValue(nodeId, props.value);

  const handleChange = (values: number[]) => {
    if (disabled) return;
    if (isRange) {
      setValue(values);
      sendEvent(nodeId, values, { noRerun: props.noRerun });
    } else {
      const val = values[0];
      setValue(val);
      sendEvent(nodeId, val, { noRerun: props.noRerun });
    }
  };

  const displayValue = isRange
    ? `${Array.isArray(value) ? value[0] : min} – ${Array.isArray(value) ? value[1] : max}`
    : String(value);

  const sliderValue = isRange
    ? (Array.isArray(value) ? value : [min, max])
    : [typeof value === "number" ? value : min];

  return (
    <div className="mb-3 space-y-3" title={help || undefined}>
      <div className="flex items-center justify-between">
        <Label>{label}</Label>
        <span className="text-sm font-mono text-muted-foreground min-w-[3rem] text-right">
          {displayValue}
        </span>
      </div>
      <ShadcnSlider
        value={sliderValue}
        onValueChange={handleChange}
        min={min}
        max={max}
        step={step}
        disabled={!!disabled}
      />
    </div>
  );
};
