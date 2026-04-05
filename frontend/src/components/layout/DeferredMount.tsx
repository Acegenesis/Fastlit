import React, { useEffect, useMemo, useRef, useState } from "react";
import type { NodeComponentProps } from "../../registry/registry";

function normalizePrefetchTypes(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  const seen = new Set<string>();
  const result: string[] = [];
  for (const item of value) {
    const text = typeof item === "string" ? item.trim() : "";
    if (!text || seen.has(text)) continue;
    seen.add(text);
    result.push(text);
  }
  return result;
}

export const DeferredMount: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
  children,
}) => {
  const active = props?.active === true;
  const trigger = typeof props?.trigger === "string" ? props.trigger : "visible";
  const placeholderHeight =
    typeof props?.placeholderHeight === "number" && Number.isFinite(props.placeholderHeight)
      ? Math.max(96, props.placeholderHeight)
      : 240;
  const prefetchTypes = useMemo(
    () => normalizePrefetchTypes(props?.prefetchTypes),
    [props?.prefetchTypes]
  );
  const hostRef = useRef<HTMLDivElement>(null);
  const requestedRef = useRef(active);
  const [requested, setRequested] = useState(active);

  useEffect(() => {
    if (!active) return;
    requestedRef.current = true;
    setRequested(true);
  }, [active]);

  useEffect(() => {
    if (active || trigger !== "visible" || requestedRef.current) return;

    const activate = () => {
      if (requestedRef.current) return;
      requestedRef.current = true;
      setRequested(true);
      if (prefetchTypes.length > 0) {
        void import("../../registry/registry")
          .then((mod) => mod.prefetchLikelyChunks(prefetchTypes))
          .catch(() => undefined);
      }
      sendEvent(nodeId, true);
    };

    const target = hostRef.current;
    if (!target) return;

    if (typeof IntersectionObserver === "undefined") {
      activate();
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          observer.disconnect();
          activate();
        }
      },
      { rootMargin: "300px" }
    );
    observer.observe(target);
    return () => observer.disconnect();
  }, [active, nodeId, prefetchTypes, sendEvent, trigger]);

  if (active) {
    return <div ref={hostRef}>{children}</div>;
  }

  return (
    <div
      ref={hostRef}
      className="mb-3 rounded-lg border border-dashed border-border/70 bg-muted/20"
      style={{ minHeight: placeholderHeight }}
    >
      <div
        className="flex items-center justify-center px-4 py-6 text-sm text-muted-foreground"
        style={{ minHeight: placeholderHeight }}
      >
        <div className="flex items-center gap-3">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted-foreground/30 border-t-muted-foreground" />
          <span>{requested ? "Loading section..." : "Preparing section..."}</span>
        </div>
      </div>
    </div>
  );
};
