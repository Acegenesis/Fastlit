import React, { useState } from "react";
import type { NodeComponentProps } from "../registry/registry";

export const ExpanderComponent: React.FC<NodeComponentProps> = ({
  props,
  children,
}) => {
  const { label, expanded: defaultExpanded } = props;
  const [open, setOpen] = useState<boolean>(!!defaultExpanded);

  return (
    <div className="mb-3 border border-gray-200 rounded-md">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-2 text-sm font-medium
                   text-gray-700 hover:bg-gray-50 transition-colors"
      >
        <span>{label}</span>
        <svg
          className={`w-4 h-4 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="px-4 pb-3 pt-1 border-t border-gray-100">
          {children}
        </div>
      )}
    </div>
  );
};
