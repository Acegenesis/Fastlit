import React from "react";
import type { NodeComponentProps } from "../registry/registry";
import { useResolvedText } from "../context/WidgetStore";

export const Header: React.FC<NodeComponentProps> = ({ props, nodeId }) => {
  const resolved = useResolvedText(props.text, props._tpl, props._refs);

  const isSubheader = nodeId.includes("subheader") || props._level === 3;
  const className = isSubheader
    ? "text-xl font-semibold text-gray-800 mb-3"
    : "text-2xl font-bold text-gray-900 mb-3";

  const Tag = isSubheader ? "h3" : "h2";

  return <Tag className={className}>{resolved}</Tag>;
};
