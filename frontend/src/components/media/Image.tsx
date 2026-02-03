import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

interface ImageProps {
  src: string;
  caption?: string;
  width?: number;
  useContainerWidth?: boolean;
}

export const Image: React.FC<NodeComponentProps> = ({ props }) => {
  const {
    src,
    caption,
    width,
    useContainerWidth = true,
  } = props as ImageProps;

  if (!src) {
    return (
      <div className="text-gray-400 text-sm italic p-4 border border-gray-200 rounded">
        No image to display
      </div>
    );
  }

  return (
    <figure className={`${useContainerWidth ? "w-full" : "inline-block"}`}>
      <img
        src={src}
        alt={caption || "Image"}
        className={`${useContainerWidth ? "w-full" : ""} h-auto rounded`}
        style={{
          width: width ? `${width}px` : undefined,
          maxWidth: "100%",
        }}
      />
      {caption && (
        <figcaption className="mt-2 text-sm text-gray-500 text-center">
          {caption}
        </figcaption>
      )}
    </figure>
  );
};
