import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

interface MetricProps {
  label: string;
  value: string;
  delta?: string | null;
  deltaColor?: "normal" | "inverse" | "off";
  help?: string;
  labelVisibility?: string;
  border?: boolean;
}

export const Metric: React.FC<NodeComponentProps> = ({ props }) => {
  const {
    label,
    value,
    delta,
    deltaColor = "normal",
    help,
    labelVisibility = "visible",
    border = false,
  } = props as MetricProps;

  // Parse delta to determine direction
  const deltaNum = delta ? parseFloat(delta.replace(/[^-\d.]/g, "")) : null;
  const isPositive = deltaNum !== null && deltaNum > 0;
  const isNegative = deltaNum !== null && deltaNum < 0;

  // Determine delta color based on deltaColor prop
  let deltaColorClass = "text-gray-500";
  if (deltaColor !== "off" && delta) {
    if (deltaColor === "normal") {
      deltaColorClass = isPositive
        ? "text-green-600"
        : isNegative
          ? "text-red-600"
          : "text-gray-500";
    } else if (deltaColor === "inverse") {
      deltaColorClass = isPositive
        ? "text-red-600"
        : isNegative
          ? "text-green-600"
          : "text-gray-500";
    }
  }

  // Format delta display
  const deltaDisplay = delta
    ? `${isPositive && !delta.startsWith("+") ? "+" : ""}${delta}`
    : null;

  return (
    <div
      className={`inline-block p-4 ${border ? "border border-gray-200 rounded-lg" : ""}`}
      title={help || undefined}
    >
      {labelVisibility !== "collapsed" && (
        <p
          className={`text-sm font-medium text-gray-500 mb-1 ${
            labelVisibility === "hidden" ? "sr-only" : ""
          }`}
        >
          {label}
        </p>
      )}
      <p className="text-3xl font-semibold text-gray-900">{value}</p>
      {deltaDisplay && (
        <p className={`text-sm mt-1 flex items-center gap-1 ${deltaColorClass}`}>
          {isPositive && (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
            </svg>
          )}
          {isNegative && (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          )}
          {deltaDisplay}
        </p>
      )}
    </div>
  );
};
