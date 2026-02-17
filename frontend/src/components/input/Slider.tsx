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
  const { label, min, max, step, disabled, help } = props;
  const [value, setValue] = useWidgetValue(nodeId, props.value);

  const handleChange = (values: number[]) => {
    if (disabled) return;
    const val = values[0];
    setValue(val);
    sendEvent(nodeId, val, { noRerun: props.noRerun });
  };

  return (
    <div className="mb-3 space-y-3" title={help || undefined}>
      <div className="flex items-center justify-between">
        <Label>{label}</Label>
        <span className="text-sm font-mono text-muted-foreground min-w-[3rem] text-right">
          {value}
        </span>
      </div>
      <ShadcnSlider
        value={[value]}
        onValueChange={handleChange}
        min={min}
        max={max}
        step={step}
        disabled={!!disabled}
      />
    </div>
  );
};
