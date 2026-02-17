import React, { useRef } from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useWidgetValue } from "../../context/WidgetStore";

export const Navigation: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { pages, disabled } = props;
  const opts = pages as string[];
  const [value, setValue] = useWidgetValue(
    nodeId,
    opts[props.index ?? 0] ?? "",
  );
  const currentIndex = Math.max(0, opts.indexOf(value));
  const hoverTimerRef = useRef<ReturnType<typeof setTimeout>>();

  const handleClick = (i: number) => {
    if (disabled) return;
    clearTimeout(hoverTimerRef.current); // Cancel any pending prefetch
    setValue(opts[i] ?? "");
    sendEvent(nodeId, i);
  };

  const handleMouseEnter = (i: number) => {
    if (disabled || i === currentIndex) return;
    hoverTimerRef.current = setTimeout(() => {
      sendEvent(nodeId, i, { prefetch: true });
    }, 100);
  };

  const handleMouseLeave = () => {
    clearTimeout(hoverTimerRef.current);
  };

  return (
    <nav className="flex flex-col gap-1">
      {opts.map((page, i) => {
        const isActive = i === currentIndex;
        return (
          <button
            key={i}
            onClick={() => handleClick(i)}
            onMouseEnter={() => handleMouseEnter(i)}
            onMouseLeave={handleMouseLeave}
            disabled={!!disabled}
            className={`text-left py-2 px-3 text-sm rounded-md transition-colors ${
              isActive
                ? "bg-blue-50 text-blue-700 font-medium border-l-2 border-blue-600"
                : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
            }${disabled ? " opacity-50 cursor-not-allowed" : " cursor-pointer"}`}
          >
            {page}
          </button>
        );
      })}
    </nav>
  );
};
