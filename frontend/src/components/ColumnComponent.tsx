import React from "react";
import type { NodeComponentProps } from "../registry/registry";

export const ColumnComponent: React.FC<NodeComponentProps> = ({ children }) => {
  return <div className="min-w-0">{children}</div>;
};
