import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useWidgetValue } from "../../context/WidgetStore";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

export const Toggle: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, disabled, help, labelVisibility } = props;

  const [checked, setChecked] = useWidgetValue(nodeId, !!props.value);

  const handleChange = (newValue: boolean) => {
    setChecked(newValue);
    sendEvent(nodeId, newValue, { noRerun: props.noRerun });
  };

  const showLabel = labelVisibility !== "hidden" && labelVisibility !== "collapsed";

  return (
    <div className="mb-3 flex items-center gap-3" title={help || undefined}>
      <Switch
        id={nodeId}
        checked={checked}
        onCheckedChange={handleChange}
        disabled={!!disabled}
      />

      {showLabel && label && (
        <Label
          htmlFor={nodeId}
          className={cn(disabled ? "opacity-50" : "cursor-pointer")}
        >
          {label}
        </Label>
      )}

      <span
        className={cn(
          "text-xs font-medium px-2 py-0.5 rounded-full transition-colors",
          checked ? "bg-green-100 text-green-700" : "bg-muted text-muted-foreground"
        )}
      >
        {checked ? "ON" : "OFF"}
      </span>
    </div>
  );
};
