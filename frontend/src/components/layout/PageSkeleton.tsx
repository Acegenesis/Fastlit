import React from "react";

/**
 * Skeleton loading placeholder for page content.
 * Displayed while navigating to a new (uncached) page.
 */
export const PageSkeleton: React.FC = () => (
  <div className="animate-pulse space-y-6">
    {/* Title skeleton */}
    <div className="h-8 w-64 bg-muted rounded" />

    {/* Intro paragraph */}
    <div className="space-y-2">
      <div className="h-4 w-full bg-muted rounded" />
      <div className="h-4 w-5/6 bg-muted rounded" />
      <div className="h-4 w-4/6 bg-muted rounded" />
    </div>

    {/* Subheader */}
    <div className="h-6 w-48 bg-muted rounded mt-4" />

    {/* Widget placeholder (button/input) */}
    <div className="h-10 w-40 bg-muted rounded" />

    {/* More text content */}
    <div className="space-y-2">
      <div className="h-4 w-full bg-muted rounded" />
      <div className="h-4 w-3/4 bg-muted rounded" />
    </div>

    {/* Code block placeholder */}
    <div className="h-32 w-full bg-muted rounded" />

    {/* Additional widgets */}
    <div className="flex gap-4">
      <div className="h-10 w-32 bg-muted rounded" />
      <div className="h-10 w-32 bg-muted rounded" />
    </div>
  </div>
);
