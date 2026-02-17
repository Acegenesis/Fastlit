import React, { useState } from "react";
import type { NodeComponentProps } from "../../registry/registry";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

export const Expander: React.FC<NodeComponentProps> = ({
  props,
  children,
}) => {
  const { label, expanded: defaultExpanded, icon } = props;
  const [open, setOpen] = useState<boolean>(!!defaultExpanded);

  return (
    <Collapsible open={open} onOpenChange={setOpen} className="mb-3 border rounded-md">
      <CollapsibleTrigger className="w-full flex items-center justify-between px-4 py-2 text-sm font-medium hover:bg-accent transition-colors">
        <span className="flex items-center gap-2">
          {icon && <span>{icon}</span>}
          {label}
        </span>
        <ChevronDown
          className={cn("h-4 w-4 transition-transform", open && "rotate-180")}
        />
      </CollapsibleTrigger>
      <CollapsibleContent className="px-4 pb-3 pt-1 border-t">
        {children}
      </CollapsibleContent>
    </Collapsible>
  );
};
