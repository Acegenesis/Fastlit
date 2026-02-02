import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

export const Button: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, disabled, type: btnType, useContainerWidth, help } = props;

  const handleClick = () => {
    if (disabled) return;
    sendEvent(nodeId, true);
  };

  const baseClasses =
    "px-4 py-2 rounded-md font-medium text-sm mb-2 transition-colors";
  const typeClasses =
    btnType === "primary"
      ? "bg-red-600 text-white hover:bg-red-700 active:bg-red-800"
      : btnType === "tertiary"
        ? "bg-transparent text-blue-600 hover:bg-blue-50 active:bg-blue-100"
        : "bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800";
  const disabledClasses = disabled
    ? "opacity-50 cursor-not-allowed"
    : "cursor-pointer";
  const widthClass = useContainerWidth ? "w-full" : "";

  return (
    <button
      onClick={handleClick}
      disabled={!!disabled}
      title={help || undefined}
      className={`${baseClasses} ${typeClasses} ${disabledClasses} ${widthClass}`}
    >
      {label}
    </button>
  );
};
