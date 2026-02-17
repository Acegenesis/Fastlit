import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { cn } from "../../lib/utils";

export const PageLink: React.FC<NodeComponentProps> = ({ props }) => {
  const {
    page,
    label,
    icon,
    help,
    disabled,
    useContainerWidth,
  } = props;

  const handleClick = () => {
    if (!disabled) {
      // For internal navigation, we could emit an event
      // For now, treat as URL
      if (page.startsWith("http://") || page.startsWith("https://")) {
        window.open(page, "_blank", "noopener,noreferrer");
      } else {
        // Internal page navigation could be implemented here
        console.log("Navigate to:", page);
      }
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={!!disabled}
      title={help || undefined}
      className={cn(
        "inline-flex items-center gap-2 px-3 py-2 text-sm text-blue-600 hover:text-blue-800 hover:underline transition-colors",
        "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded",
        disabled && "opacity-50 cursor-not-allowed text-gray-400 hover:no-underline",
        useContainerWidth && "w-full justify-start"
      )}
    >
      {icon && <span>{icon}</span>}
      {label}
    </button>
  );
};
