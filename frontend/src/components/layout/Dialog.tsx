import React, { useState, useEffect, useRef } from "react";
import type { NodeComponentProps } from "../../registry/registry";
import {
  Dialog as ShadcnDialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

const WIDTH_MAP: Record<string, string> = {
  small: "max-w-lg",
  medium: "max-w-3xl",
  large: "max-w-6xl",
};

export const Dialog: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  children,
  sendEvent,
}) => {
  const { title, width, dismissible } = props;
  const [open, setOpen] = useState(true);
  const prevNodeIdRef = useRef(nodeId);

  useEffect(() => {
    if (prevNodeIdRef.current !== nodeId) {
      prevNodeIdRef.current = nodeId;
      setOpen(true);
    }
  }, [nodeId]);

  const widthClass = WIDTH_MAP[width as string] ?? "max-w-lg";

  const handleOpenChange = (newOpen: boolean) => {
    if (dismissible !== false || newOpen) {
      setOpen(newOpen);
      if (!newOpen) {
        sendEvent(nodeId, false);
      }
    }
  };

  return (
    <ShadcnDialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className={cn(widthClass, "w-full")}>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <div>{children}</div>
      </DialogContent>
    </ShadcnDialog>
  );
};
