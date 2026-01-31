import React from "react";
import type { NodeComponentProps } from "../registry/registry";

export const TextBlock: React.FC<NodeComponentProps> = ({ props }) => {
  return (
    <pre className="font-mono text-sm text-gray-600 bg-gray-50 p-2 rounded mb-2">
      {props.text}
    </pre>
  );
};
