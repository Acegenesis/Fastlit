import React from "react";
import type { NodeComponentProps } from "../registry/registry";

export const Markdown: React.FC<NodeComponentProps> = ({ props }) => {
  // For MVP, render as plain text in a paragraph.
  // Phase 7 will add proper markdown rendering.
  return (
    <p className="text-gray-700 mb-2 whitespace-pre-wrap leading-relaxed">
      {props.text}
    </p>
  );
};
