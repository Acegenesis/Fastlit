import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

export const Caption: React.FC<NodeComponentProps> = ({ props }) => {
  const { text, help, unsafeAllowHtml } = props;

  return (
    <p
      className="text-sm text-gray-500 mb-2"
      title={help || undefined}
      {...(unsafeAllowHtml
        ? { dangerouslySetInnerHTML: { __html: text } }
        : { children: text })}
    />
  );
};
