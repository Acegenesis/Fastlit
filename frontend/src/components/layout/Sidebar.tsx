import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

export const Sidebar: React.FC<NodeComponentProps> = ({ children }) => {
  return (
    <aside className="fixed top-0 left-0 h-full w-64 bg-gray-50 border-r border-gray-200 p-4 overflow-y-auto z-10">
      {children}
    </aside>
  );
};
