import React from "react";
import type { NodeComponentProps } from "../registry/registry";

export const Button: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const handleClick = () => {
    sendEvent(nodeId, true);
  };

  return (
    <button
      onClick={handleClick}
      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700
                 active:bg-blue-800 transition-colors font-medium text-sm mb-2"
    >
      {props.label}
    </button>
  );
};
