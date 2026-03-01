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
  icon?: string | null;
  pageIndex?: number;
  urlPath?: string;
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

    if (item.pageIndex === currentIndex) {
      result.add(item.path);
      containsActive = true;
    }

    const childHasActive = collectActiveGroups(item.children, currentIndex, result);
    if (childHasActive) {
      result.add(item.path);
      containsActive = true;
    }
  }
  return containsActive;
}

function readStoredGroups(storageKey: string): Record<string, boolean> {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
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
  const storageKey = `fastlit:navigation:${nodeId}:groups`;
  const [value, setValue] = useWidgetValue(nodeId, opts[props.index ?? 0] ?? "");
  const currentIndex = opts.indexOf(value);
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>(() =>
    readStoredGroups(storageKey),
  );
  const [hasStoredGroups, setHasStoredGroups] = useState<boolean>(() => {
    if (typeof window === "undefined") return false;
    return window.localStorage.getItem(storageKey) !== null;
  });

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
      if (!hasStoredGroups) {
        for (const item of navItems) {
          if (item.type === "group" && next[item.path] === undefined) {
            next[item.path] = true;
          }
        }
      }
      return next;
    });
  }, [navItems, activeGroups, hasStoredGroups]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(expandedGroups));
      setHasStoredGroups(true);
    } catch {
      // Ignore storage failures in restricted environments.
    }
  }, [expandedGroups, storageKey]);

  const handleClick = (index: number) => {
    if (disabled) return;
    setValue(opts[index] ?? "");
    sendEvent(nodeId, index);
  };

  const toggleGroup = (path: string) => {
    setExpandedGroups((prev) => ({ ...prev, [path]: !prev[path] }));
  };

  const renderItems = (items: NavigationItem[], depth = 0): React.ReactNode =>
    items.map((item) => {
      if (item.type === "group") {
        const isExpanded = expandedGroups[item.path] ?? depth === 0;
        const isClickable = typeof item.pageIndex === "number";
        const isActive = item.pageIndex === currentIndex;
        return (
          <div key={`group:${item.path}`} className="flex flex-col gap-1">
            <div className="flex items-center gap-1">
              {isClickable ? (
                <button
                  type="button"
                  onClick={() => handleClick(item.pageIndex!)}
                  disabled={!!disabled}
                  data-url-path={item.urlPath ?? ""}
                  className={`flex-1 text-left py-2 px-3 text-sm rounded-md transition-colors ${
                    isActive
                      ? "bg-blue-50 text-blue-700 font-medium border-l-2 border-blue-600"
                      : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                  }${disabled ? " opacity-50 cursor-not-allowed" : " cursor-pointer"}`}
                  style={{ marginLeft: `${depth * 10}px` }}
                >
                  <span className="inline-flex items-center gap-2">
                    {item.icon ? <span>{item.icon}</span> : null}
                    <span>{item.label}</span>
                  </span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => toggleGroup(item.path)}
                  className="flex-1 text-left py-2 px-3 text-xs font-semibold uppercase tracking-[0.08em] text-gray-500 hover:text-gray-800"
                  style={{ paddingLeft: `${12 + depth * 14}px` }}
                >
                  <span className="inline-flex items-center gap-2">
                    {item.icon ? <span>{item.icon}</span> : null}
                    <span>{item.label}</span>
                  </span>
                </button>
              )}
              <button
                type="button"
                onClick={() => toggleGroup(item.path)}
                className="px-2 py-2 text-gray-500 hover:text-gray-800"
                aria-expanded={isExpanded}
                aria-label={isExpanded ? "Collapse group" : "Expand group"}
              >
                <span className="inline-flex w-3 justify-center">
                  {isExpanded ? "▾" : "▸"}
                </span>
              </button>
            </div>
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
        : opts.map((page, index) => {
            const isActive = index === currentIndex;
            return (
              <button
                key={index}
                type="button"
                onClick={() => handleClick(index)}
                disabled={!!disabled}
                data-url-path={pathList[index] ?? ""}
                className={`text-left py-2 px-3 text-sm rounded-md transition-colors ${
                  isActive
                    ? "bg-blue-50 text-blue-700 font-medium border-l-2 border-blue-600"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }${disabled ? " opacity-50 cursor-not-allowed" : " cursor-pointer"}`}
              >
                <span className="inline-flex items-center gap-2">
                  {iconList[index] ? <span>{iconList[index]}</span> : null}
                  <span>{page}</span>
                </span>
              </button>
            );
          })}
    </nav>
  );
};
