import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

interface PdfProps {
  src: string;
  width?: number;
  height?: number;
}

export const Pdf: React.FC<NodeComponentProps> = ({ props }) => {
  const { src, width, height = 600 } = props as PdfProps;

  if (!src) {
    return (
      <div className="text-gray-400 text-sm italic p-4 border border-gray-200 rounded">
        No PDF to display
      </div>
    );
  }

  // Use object tag for better PDF rendering with data URLs
  return (
    <div
      className="border border-gray-200 rounded overflow-hidden bg-gray-100"
      style={{ width: width ? `${width}px` : "100%" }}
    >
      <object
        data={src}
        type="application/pdf"
        width="100%"
        height={height}
        className="block"
      >
        {/* Fallback for browsers that don't support object tag for PDFs */}
        <div className="p-8 text-center">
          <p className="text-gray-600 mb-4">
            Unable to display PDF inline.
          </p>
          <a
            href={src}
            download="document.pdf"
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Download PDF
          </a>
        </div>
      </object>
    </div>
  );
};
