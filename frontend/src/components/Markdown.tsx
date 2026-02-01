import React from "react";
import type { NodeComponentProps } from "../registry/registry";
import { useResolvedText } from "../context/WidgetStore";

export const Markdown: React.FC<NodeComponentProps> = ({ props }) => {
  const resolved = useResolvedText(props.text, props._tpl, props._refs);

  return (
    <p className="text-gray-700 mb-2 whitespace-pre-wrap leading-relaxed">
      {resolved}
    </p>
  );
};
