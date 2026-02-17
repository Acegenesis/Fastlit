import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useWidgetValue } from "../../context/WidgetStore";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

export const Radio: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, options, disabled, help, horizontal, captions } = props;
  const opts = options as string[];
  const [value, setValue] = useWidgetValue(nodeId, opts[props.index ?? 0] ?? "");
  const currentIndex = Math.max(0, opts.indexOf(value));

  const handleChange = (val: string) => {
    if (disabled) return;
    const idx = parseInt(val, 10);
    setValue(opts[idx] ?? "");
    sendEvent(nodeId, idx, { noRerun: props.noRerun });
  };

  return (
    <div className="mb-3 space-y-1.5" title={help || undefined}>
      <Label>{label}</Label>
      <RadioGroup
        value={String(currentIndex)}
        onValueChange={handleChange}
        disabled={!!disabled}
        className={cn(horizontal && "flex flex-wrap gap-4")}
      >
        {opts.map((opt, i) => (
          <div key={i} className="flex items-center gap-2">
            <RadioGroupItem value={String(i)} id={`${nodeId}-${i}`} />
            <div>
              <Label htmlFor={`${nodeId}-${i}`} className="cursor-pointer font-normal">
                {opt}
              </Label>
              {captions && captions[i] && (
                <p className="text-xs text-muted-foreground">{captions[i]}</p>
              )}
            </div>
          </div>
        ))}
      </RadioGroup>
    </div>
  );
};
