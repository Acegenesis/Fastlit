import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { Button as ShadcnButton } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export const Button: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, disabled, type: btnType, useContainerWidth, help } = props;

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
      {label}
    </ShadcnButton>
  );
};
