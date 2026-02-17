import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useResolvedText } from "../../context/WidgetStore";
import { cn } from "@/lib/utils";

const DIVIDER_COLORS: Record<string, string> = {
  blue: "bg-blue-500",
  green: "bg-green-500",
  orange: "bg-orange-500",
  red: "bg-red-500",
  violet: "bg-violet-500",
  gray: "bg-gray-300",
  rainbow: "bg-gradient-to-r from-red-500 via-yellow-500 via-green-500 via-blue-500 to-violet-500",
};

export const Header: React.FC<NodeComponentProps> = ({ props, nodeId }) => {
  const resolved = useResolvedText(props.text, props._tpl, props._refs);
  const divider = props.divider;
  const help = props.help as string | undefined;

  const isSubheader = nodeId.includes("subheader") || props._level === 3;
  const className = isSubheader
    ? "text-xl font-semibold text-foreground"
    : "text-2xl font-bold text-foreground";

  const Tag = isSubheader ? "h3" : "h2";

  const dividerColor = typeof divider === "string" ? DIVIDER_COLORS[divider] : undefined;
  const showDivider = divider === true || typeof divider === "string";

  return (
    <div className="mb-3" title={help}>
      <Tag className={className}>{resolved}</Tag>
      {showDivider && (
        <hr
          className={cn(
            "mt-2 border-0 rounded",
            dividerColor ? "h-1" : "h-px bg-border",
            dividerColor
          )}
        />
      )}
    </div>
  );
};
