import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

function FragmentSpinner(): React.ReactNode {
  return (
    <div className="flex min-h-[120px] items-center justify-center gap-3 rounded-lg border border-dashed border-border/70 bg-background/70 px-4 py-6">
      <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted-foreground/30 border-t-primary" />
      <span className="text-sm text-muted-foreground">Loading section...</span>
    </div>
  );
}

function FragmentSkeleton(minHeight: number): React.ReactNode {
  return (
    <div
      className="space-y-3 rounded-xl border border-dashed border-border/70 bg-muted/20 p-4 animate-pulse"
      style={{ minHeight }}
      aria-hidden="true"
    >
      <div className="h-5 w-40 rounded bg-muted" />
      <div className="space-y-2">
        <div className="h-4 w-full rounded bg-muted" />
        <div className="h-4 w-5/6 rounded bg-muted" />
        <div className="h-4 w-2/3 rounded bg-muted" />
      </div>
      <div className="h-28 w-full rounded bg-muted" />
    </div>
  );
}

/**
 * Fragment container. Deferred fragments keep their last rendered content
 * visible but non-interactive while a new version hydrates in the background.
 */
export const Fragment: React.FC<NodeComponentProps> = ({ props, children }) => {
  const loading = props?.loading === true;
  const placeholder = String(props?.placeholder ?? "skeleton");
  const minHeight =
    typeof props?.minHeight === "number" && Number.isFinite(props.minHeight)
      ? Math.max(64, props.minHeight)
      : 180;
  const hasChildren = React.Children.count(children) > 0;

  if (!loading) {
    return <>{children}</>;
  }

  let loader: React.ReactNode = null;
  if (placeholder === "spinner") {
    loader = FragmentSpinner();
  } else if (placeholder === "skeleton") {
    loader = FragmentSkeleton(minHeight);
  } else {
    loader = <div style={{ minHeight }} aria-hidden="true" />;
  }

  if (!hasChildren) {
    return <>{loader}</>;
  }

  return (
    <div className="relative">
      <div className="pointer-events-none opacity-60 select-none">{children}</div>
      <div className="absolute inset-0 flex items-start justify-center bg-background/35 p-3 backdrop-blur-[1px]">
        <div className="w-full max-w-full">{loader}</div>
      </div>
    </div>
  );
};
