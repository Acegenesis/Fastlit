import React, { useState, useRef, useEffect } from "react";
import type { NodeComponentProps } from "../../registry/registry";

export const Popover: React.FC<NodeComponentProps> = ({
  props,
  children,
}) => {
  const { label, disabled, help, type: btnType, useContainerWidth } = props;
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const baseClasses =
    "px-4 py-2 rounded-md font-medium text-sm transition-colors";
  const typeClasses =
    btnType === "primary"
      ? "bg-red-600 text-white hover:bg-red-700"
      : btnType === "tertiary"
        ? "bg-transparent text-blue-600 hover:bg-blue-50"
        : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50";
  const disabledClasses = disabled
    ? "opacity-50 cursor-not-allowed"
    : "cursor-pointer";
  const widthClass = useContainerWidth ? "w-full" : "";

  return (
    <div ref={ref} className="relative inline-block mb-3">
      <button
        onClick={() => !disabled && setOpen(!open)}
        disabled={!!disabled}
        title={help || undefined}
        className={`${baseClasses} ${typeClasses} ${disabledClasses} ${widthClass}`}
      >
        {label} <span className="ml-1 text-xs">&#9662;</span>
      </button>
      {open && (
        <div className="absolute z-40 mt-1 left-0 min-w-[240px] bg-white border border-gray-200 rounded-lg shadow-lg p-4">
          {children}
        </div>
      )}
    </div>
  );
};
