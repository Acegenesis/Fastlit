import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

const GAP_MAP: Record<string, string> = {
  xxsmall: "gap-0.5",
  xsmall: "gap-1",
  small: "gap-4",
  medium: "gap-6",
  large: "gap-8",
  xlarge: "gap-10",
  xxlarge: "gap-12",
};

const VALIGN_MAP: Record<string, string> = {
  top: "items-start",
  center: "items-center",
  bottom: "items-end",
};

export const Columns: React.FC<NodeComponentProps> = ({ props, children }) => {
  const widths = (props.widths as number[]) ?? [];
  const total = (props.total as number) ?? (widths.reduce((a, b) => a + b, 0) || 1);
  const gap = GAP_MAP[props.gap as string] ?? "gap-4";
  const valign = VALIGN_MAP[props.verticalAlignment as string] ?? "items-start";

  return (
    <div
      className={`grid ${gap} ${valign} mb-3`}
      style={{
        gridTemplateColumns: widths.map((w) => `${(w / total) * 100}%`).join(" "),
      }}
    >
      {children}
    </div>
  );
};
