import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

const colorMap: Record<string, string> = {
  blue: "bg-blue-100 text-blue-800 border-blue-200",
  green: "bg-green-100 text-green-800 border-green-200",
  red: "bg-red-100 text-red-800 border-red-200",
  orange: "bg-orange-100 text-orange-800 border-orange-200",
  violet: "bg-violet-100 text-violet-800 border-violet-200",
  yellow: "bg-yellow-100 text-yellow-800 border-yellow-200",
  gray: "bg-gray-100 text-gray-800 border-gray-200",
  grey: "bg-gray-100 text-gray-800 border-gray-200",
};

export const Badge: React.FC<NodeComponentProps> = ({ props }) => {
  const colors = colorMap[props.color] || colorMap.blue;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${colors}`}
    >
      {props.icon && <span>{props.icon}</span>}
      {props.label}
    </span>
  );
};
