import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { Progress as ShadcnProgress } from "@/components/ui/progress";

export const Progress: React.FC<NodeComponentProps> = ({ props }) => {
  const { value = 0, text } = props;
  const percentage = Math.max(0, Math.min(100, value));

  return (
    <div className="mb-3 space-y-1">
      {text && (
        <p className="text-sm text-muted-foreground">{text}</p>
      )}
      <ShadcnProgress value={percentage} />
    </div>
  );
};
