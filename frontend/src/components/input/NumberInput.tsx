import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useWidgetValue } from "../../context/WidgetStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Minus, Plus } from "lucide-react";

export const NumberInput: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, min, max, step, disabled, help, placeholder } = props;
  const [value, setValue] = useWidgetValue(nodeId, props.value ?? 0);

  const clamp = (val: number) => {
    if (min != null && val < min) val = min;
    if (max != null && val > max) val = max;
    return val;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    if (raw === "" || raw === "-") {
      setValue(0);
      return;
    }
    let val = parseFloat(raw);
    if (isNaN(val)) return;
    val = clamp(val);
    setValue(val);
    sendEvent(nodeId, val, { noRerun: props.noRerun });
  };

  const increment = (dir: 1 | -1) => {
    if (disabled) return;
    let val = clamp(value + dir * (step ?? 1));
    setValue(val);
    sendEvent(nodeId, val, { noRerun: props.noRerun });
  };

  return (
    <div className="mb-3 space-y-1.5" title={help || undefined}>
      <Label>{label}</Label>
      <div className="flex items-center">
        <Button
          variant="outline"
          size="icon"
          onClick={() => increment(-1)}
          disabled={!!disabled}
          className="rounded-r-none"
        >
          <Minus className="h-4 w-4" />
        </Button>
        <Input
          type="number"
          value={value}
          onChange={handleChange}
          min={min ?? undefined}
          max={max ?? undefined}
          step={step ?? undefined}
          disabled={!!disabled}
          placeholder={placeholder || undefined}
          className="w-24 rounded-none text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
        />
        <Button
          variant="outline"
          size="icon"
          onClick={() => increment(1)}
          disabled={!!disabled}
          className="rounded-l-none"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};
