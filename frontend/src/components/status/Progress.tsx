import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { Progress as ShadcnProgress } from "@/components/ui/progress";
import { LiveExpression, useResolvedText, useResolvedValue } from "../../context/WidgetStore";

interface ProgressProps {
  value?: number;
  valueLive?: LiveExpression;
  text?: string | null;
  textTpl?: string;
  textRefs?: Record<string, string>;
  textExprs?: Record<string, LiveExpression>;
}

export const Progress: React.FC<NodeComponentProps> = ({ props }) => {
  const { value = 0, valueLive, text, textTpl, textRefs, textExprs } = props as ProgressProps;
  const resolvedValue = useResolvedValue(value, valueLive);
  const resolvedText = useResolvedText(text ?? "", textTpl, textRefs, textExprs);
  const percentage = Math.max(0, Math.min(100, Number(resolvedValue) || 0));

  return (
    <div className="mb-3 space-y-1">
      {resolvedText && (
        <p className="text-sm text-muted-foreground">{resolvedText}</p>
      )}
      <ShadcnProgress value={percentage} />
    </div>
  );
};
