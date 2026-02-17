import React, { useRef, useState } from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { cn } from "../../lib/utils";

interface UploadedFile {
  name: string;
  type: string;
  size: number;
  content: string; // base64
}

export const FileUploader: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const {
    label,
    allowedTypes,
    acceptMultiple,
    help,
    disabled,
    labelVisibility,
  } = props;

  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const showLabel = labelVisibility !== "hidden" && labelVisibility !== "collapsed";

  // Build accept string for input
  const acceptStr = allowedTypes
    ? allowedTypes.map((t: string) => (t.startsWith(".") ? t : `.${t}`)).join(",")
    : undefined;

  const processFiles = async (fileList: FileList) => {
    const newFiles: UploadedFile[] = [];

    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i];

      // Check file type if restrictions exist
      if (allowedTypes && allowedTypes.length > 0) {
        const ext = file.name.split(".").pop()?.toLowerCase();
        const allowed = allowedTypes.some((t: string) => {
          const cleanType = t.replace(".", "").toLowerCase();
          return ext === cleanType || file.type.includes(cleanType);
        });
        if (!allowed) continue;
      }

      // Read file as base64
      const content = await new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onload = () => {
          const result = reader.result as string;
          // Remove data URL prefix
          const base64 = result.split(",")[1] || "";
          resolve(base64);
        };
        reader.readAsDataURL(file);
      });

      newFiles.push({
        name: file.name,
        type: file.type,
        size: file.size,
        content,
      });

      if (!acceptMultiple) break;
    }

    const updatedFiles = acceptMultiple ? [...files, ...newFiles] : newFiles;
    setFiles(updatedFiles);
    sendEvent(nodeId, acceptMultiple ? updatedFiles : updatedFiles[0] || null);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (!disabled && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const handleRemoveFile = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    setFiles(newFiles);
    sendEvent(nodeId, acceptMultiple ? newFiles : null);
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="mb-3">
      {showLabel && label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {help && (
            <span className="ml-1 text-gray-400 cursor-help" title={help}>
              ?
            </span>
          )}
        </label>
      )}

      <div
        onClick={() => !disabled && inputRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors",
          isDragging
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 hover:border-gray-400",
          disabled && "opacity-50 cursor-not-allowed hover:border-gray-300"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={acceptStr}
          multiple={acceptMultiple}
          onChange={handleChange}
          disabled={!!disabled}
          className="hidden"
        />

        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>

        <p className="mt-2 text-sm text-gray-600">
          <span className="font-medium text-blue-600 hover:text-blue-500">
            Click to upload
          </span>{" "}
          or drag and drop
        </p>
        {allowedTypes && (
          <p className="mt-1 text-xs text-gray-500">
            {allowedTypes.join(", ").toUpperCase()}
          </p>
        )}
      </div>

      {/* File list */}
      {files.length > 0 && (
        <ul className="mt-3 space-y-2">
          {files.map((file, index) => (
            <li
              key={`${file.name}-${index}`}
              className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-md"
            >
              <div className="flex items-center gap-2 min-w-0">
                <svg
                  className="w-5 h-5 text-gray-400 flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <span className="text-sm text-gray-700 truncate">{file.name}</span>
                <span className="text-xs text-gray-500">({formatSize(file.size)})</span>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemoveFile(index);
                }}
                className="text-gray-400 hover:text-red-500 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
