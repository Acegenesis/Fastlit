import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useResolvedText } from "../../context/WidgetStore";

export const Text: React.FC<NodeComponentProps> = ({ props }) => {
  const resolved = useResolvedText(props.text, props._tpl, props._refs);

  return (
    <pre className="font-mono text-sm text-gray-600 bg-gray-50 p-2 rounded mb-2">
      {resolved}
    </pre>
  );
};
