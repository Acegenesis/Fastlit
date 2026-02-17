import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useWidgetValue } from "../../context/WidgetStore";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export const TextInput: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, placeholder, maxChars, inputType, disabled, help, autocomplete } = props;
  const [value, setValue] = useWidgetValue(nodeId, props.value ?? "");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = e.target.value;
    if (maxChars && val.length > maxChars) {
      val = val.slice(0, maxChars);
    }
    setValue(val);
    sendEvent(nodeId, val, { noRerun: props.noRerun });
  };

  const charCount = typeof value === "string" ? value.length : 0;

  return (
    <div className="mb-3 space-y-1.5" title={help || undefined}>
      <Label htmlFor={nodeId}>{label}</Label>
      <Input
        id={nodeId}
        type={inputType === "password" ? "password" : "text"}
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        maxLength={maxChars ?? undefined}
        disabled={!!disabled}
        autoComplete={autocomplete || undefined}
      />
      {(maxChars || charCount > 0) && (
        <p className="text-xs text-muted-foreground text-right">
          {charCount}{maxChars ? ` / ${maxChars}` : ""} chars
        </p>
      )}
    </div>
  );
};
