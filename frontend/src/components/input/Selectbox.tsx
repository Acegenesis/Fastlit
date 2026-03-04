import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useResolvedPropText, useResolvedTextList, useWidgetValue } from "../../context/WidgetStore";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";

export const Selectbox: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { options, disabled } = props;
  const label = useResolvedPropText(props, "label");
  const help = useResolvedPropText(props, "help");
  const placeholder = useResolvedPropText(props, "placeholder");
  const opts = useResolvedTextList((options as string[]) ?? [], props.optionsTpls, props.optionsRefsList, props.optionsExprsList);
  const [value, setValue] = useWidgetValue(nodeId, opts[props.index ?? 0] ?? "");
  const currentIndex = Math.max(0, opts.indexOf(value));

  const handleChange = (val: string) => {
    const idx = parseInt(val, 10);
    setValue(opts[idx] ?? "");
    sendEvent(nodeId, idx, { noRerun: props.noRerun });
  };

  return (
    <div className="mb-3 space-y-1.5" title={help || undefined}>
      <Label>{label}</Label>
      <Select
        value={String(currentIndex)}
        onValueChange={handleChange}
        disabled={!!disabled}
      >
        <SelectTrigger>
          <SelectValue placeholder={placeholder || "Select..."} />
        </SelectTrigger>
        <SelectContent>
          {opts.map((opt, i) => (
            <SelectItem key={i} value={String(i)}>
              {opt}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};
