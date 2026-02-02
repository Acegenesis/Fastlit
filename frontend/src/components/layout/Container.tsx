import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

export const Container: React.FC<NodeComponentProps> = ({
  props,
  children,
}) => {
  const border = props.border;
  const height = props.height;

  const style: React.CSSProperties = {};
  if (typeof height === "number") {
    style.height = `${height}px`;
    style.overflowY = "auto";
  } else if (height === "stretch") {
    style.flex = "1";
    style.overflowY = "auto";
  }

  return (
    <div
      className={`mb-3${border ? " border border-gray-200 rounded-lg p-4" : ""}`}
      style={style}
    >
      {children}
    </div>
  );
};
