import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { cn } from "../../lib/utils";

export const DownloadButton: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const {
    label,
    data,
    fileName,
    mime,
    help,
    type = "secondary",
    icon,
    disabled,
    useContainerWidth,
  } = props;

  const handleClick = () => {
    if (disabled) return;

    // Decode base64 and trigger download
    try {
      const byteCharacters = atob(data);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: mime });

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = fileName || "download";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      // Notify backend of click
      sendEvent(nodeId, true);
    } catch (err) {
      console.error("Download failed:", err);
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
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
      </svg>
      {label}
    </button>
  );
};
