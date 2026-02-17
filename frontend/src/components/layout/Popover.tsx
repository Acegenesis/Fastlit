import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import {
  Popover as ShadcnPopover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

export const Popover: React.FC<NodeComponentProps> = ({
  props,
  children,
}) => {
  const { label, disabled, help, type: btnType, useContainerWidth } = props;

  const variant =
    btnType === "primary"
      ? "destructive"
      : btnType === "tertiary"
        ? "ghost"
        : "outline";

  return (
    <ShadcnPopover>
      <PopoverTrigger asChild>
        <Button
          variant={variant}
          disabled={!!disabled}
          title={help || undefined}
          className={cn("mb-3", useContainerWidth && "w-full")}
        >
          {label}
          <ChevronDown className="ml-1 h-4 w-4" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="min-w-[240px]">
        {children}
      </PopoverContent>
    </ShadcnPopover>
  );
};
