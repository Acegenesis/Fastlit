import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useWidgetValue } from "../../context/WidgetStore";
import { Checkbox as ShadcnCheckbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

export const Checkbox: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, disabled, help } = props;
  const [checked, setChecked] = useWidgetValue(nodeId, !!props.value);

  const handleChange = (value: boolean) => {
    setChecked(value);
    sendEvent(nodeId, value, { noRerun: props.noRerun });
  };

  return (
    <div className="mb-3 flex items-center gap-2" title={help || undefined}>
      <ShadcnCheckbox
        id={nodeId}
        checked={checked}
        onCheckedChange={handleChange}
        disabled={!!disabled}
      />
      <Label htmlFor={nodeId} className="cursor-pointer">
        {label}
      </Label>
    </div>
  );
};
