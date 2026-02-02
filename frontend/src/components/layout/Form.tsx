import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

export const Form: React.FC<NodeComponentProps> = ({
  props,
  children,
  sendEvent,
  nodeId,
}) => {
  const border = props.border !== false;
  const enterToSubmit = props.enterToSubmit !== false;

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (enterToSubmit && e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendEvent(nodeId, true);
    }
  };

  return (
    <div
      onKeyDown={handleKeyDown}
      className={`mb-3${
        border ? " border border-gray-200 rounded-lg p-4" : ""
      }`}
    >
      {children}
    </div>
  );
};
