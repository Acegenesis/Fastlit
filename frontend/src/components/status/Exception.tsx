import React, { useState } from "react";
import type { NodeComponentProps } from "../../registry/registry";

export const Exception: React.FC<NodeComponentProps> = ({ props }) => {
  const { type, message, traceback } = props;
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-red-50 border border-red-200 rounded-lg mb-3 overflow-hidden">
      <div className="p-4">
        <div className="flex items-start gap-3">
          <span className="flex-shrink-0 text-red-500 text-lg">!</span>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-red-800">{type}</p>
            <p className="text-red-700 text-sm mt-1">{message}</p>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex-shrink-0 text-red-600 hover:text-red-800 text-sm font-medium"
          >
            {expanded ? "Hide" : "Show"} traceback
          </button>
        </div>
      </div>
      {expanded && traceback && (
        <div className="border-t border-red-200 bg-red-100/50 p-4">
          <pre className="text-xs text-red-800 overflow-x-auto whitespace-pre-wrap font-mono">
            {traceback}
          </pre>
        </div>
      )}
    </div>
  );
};
