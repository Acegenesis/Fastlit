import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useWidgetValue } from "../../context/WidgetStore";

export const Navigation: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { pages, icons, urlPaths, disabled } = props;
  const opts = pages as string[];
  const iconList = (icons ?? []) as Array<string | null | undefined>;
  const pathList = (urlPaths ?? []) as Array<string | undefined>;
  const [value, setValue] = useWidgetValue(
    nodeId,
    opts[props.index ?? 0] ?? "",
  );
  const currentIndex = Math.max(0, opts.indexOf(value));

  const handleClick = (i: number) => {
    if (disabled) return;
    setValue(opts[i] ?? "");
    sendEvent(nodeId, i);
  };

  return (
    <nav className="flex flex-col gap-1">
      {opts.map((page, i) => {
        const isActive = i === currentIndex;
        return (
          <button
            key={i}
            onClick={() => handleClick(i)}
            disabled={!!disabled}
            data-url-path={pathList[i] ?? ""}
            className={`text-left py-2 px-3 text-sm rounded-md transition-colors ${
              isActive
                ? "bg-blue-50 text-blue-700 font-medium border-l-2 border-blue-600"
                : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
            }${disabled ? " opacity-50 cursor-not-allowed" : " cursor-pointer"}`}
          >
            <span className="inline-flex items-center gap-2">
              {iconList[i] ? <span>{iconList[i]}</span> : null}
              <span>{page}</span>
            </span>
          </button>
        );
      })}
    </nav>
  );
};
