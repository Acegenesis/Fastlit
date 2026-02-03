import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

export const Column: React.FC<NodeComponentProps> = ({ props, children }) => {
  const border = props.border as boolean;

  return (
    <div
      className={`${border ? "border border-gray-200 rounded-lg p-4" : ""}`}
    >
      {children}
    </div>
  );
};
