import React, { useRef } from "react";
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
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const nextWidgetValue = (values: number[]) =>
    isRange ? values : values[0];

  const handleChange = (values: number[]) => {
    if (disabled) return;
    const nextValue = nextWidgetValue(values);
    // Update WidgetStore immediately for instant local feedback (e.g. direct refs like st.metric value=threshold)
    setValue(nextValue);
    // Debounce server rerun so Python-computed values update during drag
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      sendEvent(nodeId, nextValue);
      debounceRef.current = null;
    }, 150);
  };

  const handleCommit = (values: number[]) => {
    if (disabled) return;
    const nextValue = nextWidgetValue(values);
    setValue(nextValue);
    // Cancel any pending debounced event and send immediately on release
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
