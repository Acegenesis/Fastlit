import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useResolvedPropText, useResolvedTextList, useWidgetValue } from "../../context/WidgetStore";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

export const Radio: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { options, disabled, horizontal, captions } = props;
  const label = useResolvedPropText(props, "label");
  const help = useResolvedPropText(props, "help");
  const opts = useResolvedTextList((options as string[]) ?? [], props.optionsTpls, props.optionsRefsList, props.optionsExprsList);
  const resolvedCaptions = useResolvedTextList((captions as string[] | undefined) ?? [], props.captionsTpls, props.captionsRefsList, props.captionsExprsList);
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
              {resolvedCaptions[i] && (
                <p className="text-xs text-muted-foreground">{resolvedCaptions[i]}</p>
              )}
            </div>
          </div>
        ))}
      </RadioGroup>
    </div>
  );
};
