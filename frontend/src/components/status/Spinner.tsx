import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

export const Spinner: React.FC<NodeComponentProps> = ({ props }) => {
  const { text = "Loading...", active = true } = props;

  if (!active) return null;

  return (
    <div className="flex items-center gap-3 p-3 mb-3">
      <div className="relative">
        <div className="w-5 h-5 border-2 border-gray-200 rounded-full"></div>
        <div className="absolute inset-0 w-5 h-5 border-2 border-blue-500 rounded-full border-t-transparent animate-spin"></div>
      </div>
      <span className="text-gray-600 text-sm">{text}</span>
    </div>
  );
};
