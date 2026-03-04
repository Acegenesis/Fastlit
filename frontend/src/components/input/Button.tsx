import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { Button as ShadcnButton } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useResolvedPropText } from "../../context/WidgetStore";

export const Button: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { disabled, type: btnType, useContainerWidth, iconPosition } = props;
  const label = useResolvedPropText(props, "label");
  const help = useResolvedPropText(props, "help");
  const icon = useResolvedPropText(props, "icon");

  const handleClick = () => {
    if (disabled) return;
    sendEvent(nodeId, true);
  };

  const variant =
    btnType === "primary"
      ? "destructive"
      : btnType === "tertiary"
        ? "ghost"
        : "default";

  return (
    <ShadcnButton
      variant={variant}
      onClick={handleClick}
      disabled={!!disabled}
      title={help || undefined}
      className={cn("mb-2", useContainerWidth && "w-full")}
    >
      {icon && iconPosition !== "right" ? <span>{icon}</span> : null}
      {label}
      {icon && iconPosition === "right" ? <span>{icon}</span> : null}
    </ShadcnButton>
  );
};
