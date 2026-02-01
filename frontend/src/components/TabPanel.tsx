import React from "react";
import type { NodeComponentProps } from "../registry/registry";

export const TabPanel: React.FC<NodeComponentProps> = ({ children }) => {
  return <div>{children}</div>;
};
