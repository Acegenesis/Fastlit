import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

export const Divider: React.FC<NodeComponentProps> = () => {
  return <hr className="my-4 border-t border-gray-200" />;
};
