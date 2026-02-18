import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useSidebar } from "../../context/SidebarContext";
import type { NodeComponentProps } from "../../registry/registry";

export const Sidebar: React.FC<NodeComponentProps> = ({ children }) => {
  const { collapsed, setCollapsed } = useSidebar();

  return (
    <>
      {/* Sidebar panel — inline styles for reliable CSS transitions */}
      <aside
        className="fixed top-0 left-0 h-full bg-gray-50 border-r border-gray-200 z-10"
        style={{
          width: collapsed ? 0 : 256,
          overflow: "hidden",
          overflowY: collapsed ? "hidden" : "auto",
          padding: collapsed ? 0 : "1rem",
          transition: "width 200ms ease, padding 200ms ease",
        }}
      >
        {!collapsed && children}
      </aside>

      {/* Toggle button — always visible, floats at the sidebar edge */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="fixed top-4 z-20 bg-white border border-gray-200 rounded-full shadow-sm p-1 hover:bg-gray-50"
        style={{
          left: collapsed ? 8 : 248,
          transition: "left 200ms ease",
        }}
        title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {collapsed ? (
          <ChevronRight className="w-4 h-4 text-gray-500" />
        ) : (
          <ChevronLeft className="w-4 h-4 text-gray-500" />
        )}
      </button>
    </>
  );
};
