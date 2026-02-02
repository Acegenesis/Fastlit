import React, { useState } from "react";
import type { NodeComponentProps } from "../../registry/registry";

const WIDTH_MAP: Record<string, string> = {
  small: "max-w-lg",
  medium: "max-w-3xl",
  large: "max-w-6xl",
};

export const Dialog: React.FC<NodeComponentProps> = ({
  props,
  children,
}) => {
  const { title, width, dismissible } = props;
  const [open, setOpen] = useState(true);

  if (!open) return null;

  const widthClass = WIDTH_MAP[width as string] ?? "max-w-lg";

  const handleBackdropClick = () => {
    if (dismissible !== false) {
      setOpen(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={handleBackdropClick}
    >
      <div
        className={`${widthClass} w-full mx-4 bg-white rounded-xl shadow-2xl`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
          {dismissible !== false && (
            <button
              onClick={() => setOpen(false)}
              className="text-gray-400 hover:text-gray-600 text-xl leading-none"
            >
              &times;
            </button>
          )}
        </div>
        <div className="px-6 py-4">{children}</div>
      </div>
    </div>
  );
};
