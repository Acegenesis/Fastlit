import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { sanitizeHtml } from "../../utils/sanitize";

export const Html: React.FC<NodeComponentProps> = ({ props }) => {
  const sanitized = sanitizeHtml(props.body || "");

  return (
    <div
      className="mb-2"
      dangerouslySetInnerHTML={{ __html: sanitized }}
    />
  );
};
