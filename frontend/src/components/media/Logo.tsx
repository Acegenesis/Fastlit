import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

interface LogoProps {
  src: string;
  size?: "small" | "medium" | "large";
  link?: string;
  iconSrc?: string;
}

const sizeMap = {
  small: "h-8",
  medium: "h-12",
  large: "h-16",
};

export const Logo: React.FC<NodeComponentProps> = ({ props }) => {
  const {
    src,
    size = "medium",
    link,
    iconSrc,
  } = props as LogoProps;

  if (!src) {
    return null;
  }

  const sizeClass = sizeMap[size] || sizeMap.medium;

  const logoElement = (
    <img
      src={src}
      alt="Logo"
      className={`${sizeClass} w-auto object-contain`}
    />
  );

  if (link) {
    return (
      <a
        href={link}
        target="_blank"
        rel="noopener noreferrer"
        className="block hover:opacity-80 transition-opacity"
      >
        {logoElement}
      </a>
    );
  }

  return logoElement;
};
