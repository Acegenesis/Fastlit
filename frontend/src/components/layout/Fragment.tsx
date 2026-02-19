import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

/**
 * Fragment container — renders as a transparent wrapper.
 *
 * The backend patches only this subtree when one of its widgets changes,
 * leaving the rest of the page untouched.
 */
export const Fragment: React.FC<NodeComponentProps> = ({ children }) => {
  return <>{children}</>;
};
