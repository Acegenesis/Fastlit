import React, { useEffect, useMemo, useState } from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useWidgetValue } from "../../context/WidgetStore";

type NavigationPageItem = {
  type: "page";
  label: string;
  icon?: string | null;
  index: number;
  urlPath?: string;
};

type NavigationGroupItem = {
  type: "group";
  label: string;
  path: string;
  children: NavigationItem[];
};

type NavigationItem = NavigationPageItem | NavigationGroupItem;

function collectActiveGroups(
  items: NavigationItem[],
  currentIndex: number,
  result: Set<string>,
): boolean {
  let containsActive = false;
  for (const item of items) {
    if (item.type === "page") {
      if (item.index === currentIndex) containsActive = true;
      continue;
    }
    const childHasActive = collectActiveGroups(item.children, currentIndex, result);
    if (childHasActive) {
      result.add(item.path);
      containsActive = true;
    }
  }
  return containsActive;
}

export const Navigation: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { pages, icons, urlPaths, disabled } = props;
  const opts = pages as string[];
  const iconList = (icons ?? []) as Array<string | null | undefined>;
  const pathList = (urlPaths ?? []) as Array<string | undefined>;
  const navItems = (props.items ?? []) as NavigationItem[];
  const [value, setValue] = useWidgetValue(
    nodeId,
    opts[props.index ?? 0] ?? "",
  );
  const currentIndex = opts.indexOf(value);
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});

  const activeGroups = useMemo(() => {
    const groups = new Set<string>();
    collectActiveGroups(navItems, currentIndex, groups);
    return groups;
  }, [navItems, currentIndex]);

  useEffect(() => {
    if (navItems.length === 0) return;
    setExpandedGroups((prev) => {
      const next = { ...prev };
      for (const path of activeGroups) {
        next[path] = true;
      }
      for (const item of navItems) {
        if (item.type === "group" && next[item.path] === undefined) {
          next[item.path] = true;
        }
      }
      return next;
    });
  }, [navItems, activeGroups]);

  const handleClick = (i: number) => {
    if (disabled) return;
    setValue(opts[i] ?? "");
    sendEvent(nodeId, i);
  };

  const toggleGroup = (path: string) => {
    setExpandedGroups((prev) => ({ ...prev, [path]: !prev[path] }));
  };

  const renderItems = (items: NavigationItem[], depth = 0): React.ReactNode =>
    items.map((item) => {
      if (item.type === "group") {
        const isExpanded = expandedGroups[item.path] ?? depth === 0;
        return (
          <div key={`group:${item.path}`} className="flex flex-col gap-1">
            <button
              type="button"
              onClick={() => toggleGroup(item.path)}
              className="text-left py-2 px-3 text-xs font-semibold uppercase tracking-[0.08em] text-gray-500 hover:text-gray-800"
              style={{ paddingLeft: `${12 + depth * 14}px` }}
            >
              <span className="inline-flex items-center gap-2">
                <span className="w-3 text-center">{isExpanded ? "▾" : "▸"}</span>
                <span>{item.label}</span>
              </span>
            </button>
            {isExpanded ? renderItems(item.children, depth + 1) : null}
          </div>
        );
      }

      const isActive = item.index === currentIndex;
      return (
        <button
          key={`page:${item.index}`}
          type="button"
          onClick={() => handleClick(item.index)}
          disabled={!!disabled}
          data-url-path={item.urlPath ?? ""}
          className={`text-left py-2 px-3 text-sm rounded-md transition-colors ${
            isActive
              ? "bg-blue-50 text-blue-700 font-medium border-l-2 border-blue-600"
              : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
          }${disabled ? " opacity-50 cursor-not-allowed" : " cursor-pointer"}`}
          style={{ marginLeft: `${depth * 10}px` }}
        >
          <span className="inline-flex items-center gap-2">
            {item.icon ? <span>{item.icon}</span> : null}
            <span>{item.label}</span>
          </span>
        </button>
      );
    });

  return (
    <nav className="flex flex-col gap-1">
      {navItems.length > 0
        ? renderItems(navItems)
        : opts.map((page, i) => {
            const isActive = i === currentIndex;
            return (
              <button
                key={i}
                type="button"
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
