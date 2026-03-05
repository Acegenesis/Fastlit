import React, { useRef } from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useResolvedPropText, useWidgetValue } from "../../context/WidgetStore";
import { Slider as ShadcnSlider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";

export const Slider: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { min, max, step, disabled, isRange } = props;
  const label = useResolvedPropText(props, "label");
  const help = useResolvedPropText(props, "help");
  const [value, setValue] = useWidgetValue(nodeId, props.value);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isArrowDemoSlider =
    nodeId === "k:arrow_demo_rows" || label === "Number of rows to generate";

  const nextWidgetValue = (values: number[]) =>
    isRange ? values : values[0];

  const handleChange = (values: number[]) => {
    if (disabled) return;
    const nextValue = nextWidgetValue(values);
    if (isArrowDemoSlider) {
      console.log("[Fastlit][Slider:change]", {
        nodeId,
        label,
        nextValue,
      });
    }
    setValue(nextValue);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      if (isArrowDemoSlider) {
        console.log("[Fastlit][Slider:debounced-send]", {
          nodeId,
          label,
          nextValue,
        });
      }
      sendEvent(nodeId, nextValue);
      debounceRef.current = null;
    }, 150);
  };

  const handleCommit = (values: number[]) => {
    if (disabled) return;
    const nextValue = nextWidgetValue(values);
    if (isArrowDemoSlider) {
      console.log("[Fastlit][Slider:commit]", {
        nodeId,
        label,
        nextValue,
      });
    }
    setValue(nextValue);
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
      debounceRef.current = null;
    }
    sendEvent(nodeId, nextValue);
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
        onValueCommit={handleCommit}
        min={min}
        max={max}
        step={step}
        disabled={!!disabled}
      />
    </div>
  );
};
