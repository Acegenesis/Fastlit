import React, { useState } from "react";
import type { NodeComponentProps } from "../../registry/registry";

const stateIcons = {
  running: (
    <div className="relative w-4 h-4">
      <div className="w-4 h-4 border-2 border-gray-300 rounded-full"></div>
      <div className="absolute inset-0 w-4 h-4 border-2 border-blue-500 rounded-full border-t-transparent animate-spin"></div>
    </div>
  ),
  complete: (
    <span className="w-4 h-4 flex items-center justify-center text-green-500 text-sm">
      ✓
    </span>
  ),
  error: (
    <span className="w-4 h-4 flex items-center justify-center text-red-500 text-sm">
      ✕
    </span>
  ),
};

const stateStyles = {
  running: "border-blue-200 bg-blue-50/50",
  complete: "border-green-200 bg-green-50/50",
  error: "border-red-200 bg-red-50/50",
};

export const Status: React.FC<NodeComponentProps> = ({ props, children }) => {
  const { label, expanded: initialExpanded = true, state = "running" } = props;
  const [expanded, setExpanded] = useState(initialExpanded);

  const icon = stateIcons[state as keyof typeof stateIcons] || stateIcons.running;
  const styles = stateStyles[state as keyof typeof stateStyles] || stateStyles.running;

  return (
    <div className={`border rounded-lg mb-3 overflow-hidden ${styles}`}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-3 text-left hover:bg-black/5 transition-colors"
      >
        {icon}
        <span className="flex-1 font-medium text-gray-800">{label}</span>
        <svg
          className={`w-4 h-4 text-gray-500 transition-transform ${expanded ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {expanded && children && (
        <div className="px-3 pb-3 pt-1 border-t border-inherit">
          {children}
        </div>
      )}
    </div>
  );
};
