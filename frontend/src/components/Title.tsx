import React from "react";
import type { NodeComponentProps } from "../registry/registry";

export const Title: React.FC<NodeComponentProps> = ({ props }) => {
  return (
    <h1 className="text-3xl font-bold text-gray-900 mb-4">
      {props.text}
    </h1>
  );
};
