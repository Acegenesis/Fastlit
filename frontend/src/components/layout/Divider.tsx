import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

const COLOR_MAP: Record<string, string> = {
  blue: "bg-blue-500",
  green: "bg-green-500",
  orange: "bg-orange-500",
  red: "bg-red-500",
  violet: "bg-violet-500",
  gray: "bg-gray-500",
  rainbow: "bg-gradient-to-r from-red-500 via-yellow-500 to-blue-500",
};

export const Divider: React.FC<NodeComponentProps> = ({ props }) => {
  const color = props?.color as string | undefined;
  const colorClass = color ? COLOR_MAP[color] : undefined;

  if (colorClass) {
    return <hr className={cn("my-4 h-0.5 border-0 rounded", colorClass)} />;
  }

  return <Separator className="my-4" decorative />;
};
