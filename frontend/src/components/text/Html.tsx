import React from "react";
import DOMPurify from "dompurify";
import type { NodeComponentProps } from "../../registry/registry";

export const Html: React.FC<NodeComponentProps> = ({ props }) => {
  const sanitized = DOMPurify.sanitize(props.body || "");

  return (
    <div
      className="mb-2"
      dangerouslySetInnerHTML={{ __html: sanitized }}
    />
  );
};
