import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

interface PyplotProps {
  image: string; // Base64 data URL
  useContainerWidth?: boolean;
}

export const Pyplot: React.FC<NodeComponentProps> = ({ props }) => {
  const { image, useContainerWidth = true } = props as PyplotProps;

  if (!image) {
    return (
      <div className="text-gray-400 text-sm italic p-4 border border-gray-200 rounded">
        No image to display
      </div>
    );
  }

  return (
    <div className={useContainerWidth ? "w-full" : "inline-block"}>
      <img
        src={image}
        alt="Matplotlib figure"
        className={`${useContainerWidth ? "w-full" : ""} h-auto`}
        style={{ maxWidth: "100%" }}
      />
    </div>
  );
};
