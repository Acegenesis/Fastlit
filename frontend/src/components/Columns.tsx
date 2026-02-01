import React from "react";
import type { NodeComponentProps } from "../registry/registry";

export const Columns: React.FC<NodeComponentProps> = ({ props, children }) => {
  const widths = (props.widths as number[]) ?? [];
  const total = (props.total as number) ?? (widths.reduce((a, b) => a + b, 0) || 1);

  return (
    <div
      className="grid gap-4 mb-3"
      style={{
        gridTemplateColumns: widths.map((w) => `${(w / total) * 100}%`).join(" "),
      }}
    >
      {children}
    </div>
  );
};
