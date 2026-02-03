import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

export const Tab: React.FC<NodeComponentProps> = ({ children }) => {
  // Tab is a simple container — visibility is controlled by parent Tabs
  return <>{children}</>;
};
