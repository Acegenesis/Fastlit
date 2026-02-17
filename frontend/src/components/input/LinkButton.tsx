import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { cn } from "../../lib/utils";

export const LinkButton: React.FC<NodeComponentProps> = ({ props }) => {
  const {
    label,
    url,
    help,
    type = "secondary",
    icon,
    disabled,
    useContainerWidth,
  } = props;

  const handleClick = () => {
    if (!disabled && url) {
      window.open(url, "_blank", "noopener,noreferrer");
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={!!disabled}
      title={help || undefined}
      className={cn(
        "inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors",
        "focus:outline-none focus:ring-2 focus:ring-offset-2",
        type === "primary"
          ? "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500"
          : "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-blue-500",
        disabled && "opacity-50 cursor-not-allowed",
        useContainerWidth && "w-full"
      )}
    >
      {icon && <span>{icon}</span>}
      {label}
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
      </svg>
    </button>
  );
};
