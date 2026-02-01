import React from "react";
import type { NodeComponentProps } from "../registry/registry";
import { useResolvedText } from "../context/WidgetStore";

export const Title: React.FC<NodeComponentProps> = ({ props }) => {
  const resolved = useResolvedText(props.text, props._tpl, props._refs);

  return (
    <h1 className="text-3xl font-bold text-gray-900 mb-4">
      {resolved}
    </h1>
  );
};
