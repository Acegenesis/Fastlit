import React, { useState, useCallback } from "react";
import type { NodeComponentProps } from "../../registry/registry";

interface JsonProps {
  data: any;
  expanded?: boolean | number;
}

export const Json: React.FC<NodeComponentProps> = ({ props }) => {
  const { data, expanded = true } = props as JsonProps;

  return (
    <div className="font-mono text-sm bg-gray-50 border border-gray-200 rounded-lg p-4 overflow-auto max-h-[500px]">
      <JsonNode value={data} depth={0} expanded={expanded} />
    </div>
  );
};

interface JsonNodeProps {
  value: any;
  depth: number;
  expanded: boolean | number;
  keyName?: string;
}

const JsonNode: React.FC<JsonNodeProps> = ({ value, depth, expanded, keyName }) => {
  const shouldExpand =
    expanded === true || (typeof expanded === "number" && depth < expanded);
  const [isExpanded, setIsExpanded] = useState(shouldExpand);

  const toggle = useCallback(() => setIsExpanded((prev) => !prev), []);

  const indent = depth * 16;

  // Render key if present
  const keyElement = keyName !== undefined && (
    <span className="text-purple-600">"{keyName}"</span>
  );

  // Null
  if (value === null) {
    return (
      <div style={{ marginLeft: indent }}>
        {keyElement}
        {keyElement && <span className="text-gray-600">: </span>}
        <span className="text-gray-500">null</span>
      </div>
    );
  }

  // Primitives
  if (typeof value === "string") {
    return (
      <div style={{ marginLeft: indent }}>
        {keyElement}
        {keyElement && <span className="text-gray-600">: </span>}
        <span className="text-green-600">"{escapeString(value)}"</span>
      </div>
    );
  }

  if (typeof value === "number") {
    return (
      <div style={{ marginLeft: indent }}>
        {keyElement}
        {keyElement && <span className="text-gray-600">: </span>}
        <span className="text-blue-600">{value}</span>
      </div>
    );
  }

  if (typeof value === "boolean") {
    return (
      <div style={{ marginLeft: indent }}>
        {keyElement}
        {keyElement && <span className="text-gray-600">: </span>}
        <span className="text-orange-600">{value ? "true" : "false"}</span>
      </div>
    );
  }

  // Array
  if (Array.isArray(value)) {
    if (value.length === 0) {
      return (
        <div style={{ marginLeft: indent }}>
          {keyElement}
          {keyElement && <span className="text-gray-600">: </span>}
          <span className="text-gray-600">[]</span>
        </div>
      );
    }

    return (
      <div style={{ marginLeft: indent }}>
        <span
          onClick={toggle}
          className="cursor-pointer select-none hover:bg-gray-200 rounded px-1"
        >
          {isExpanded ? "▼" : "▶"}
        </span>
        {keyElement}
        {keyElement && <span className="text-gray-600">: </span>}
        <span className="text-gray-600">[</span>
        {!isExpanded && (
          <span className="text-gray-400 ml-1">
            {value.length} items
          </span>
        )}
        {isExpanded && (
          <>
            {value.map((item, idx) => (
              <JsonNode
                key={idx}
                value={item}
                depth={depth + 1}
                expanded={expanded}
              />
            ))}
            <div style={{ marginLeft: indent }}>
              <span className="text-gray-600">]</span>
            </div>
          </>
        )}
        {!isExpanded && <span className="text-gray-600">]</span>}
      </div>
    );
  }

  // Object
  if (typeof value === "object") {
    const keys = Object.keys(value);
    if (keys.length === 0) {
      return (
        <div style={{ marginLeft: indent }}>
          {keyElement}
          {keyElement && <span className="text-gray-600">: </span>}
          <span className="text-gray-600">{"{}"}</span>
        </div>
      );
    }

    return (
      <div style={{ marginLeft: indent }}>
        <span
          onClick={toggle}
          className="cursor-pointer select-none hover:bg-gray-200 rounded px-1"
        >
          {isExpanded ? "▼" : "▶"}
        </span>
        {keyElement}
        {keyElement && <span className="text-gray-600">: </span>}
        <span className="text-gray-600">{"{"}</span>
        {!isExpanded && (
          <span className="text-gray-400 ml-1">
            {keys.length} keys
          </span>
        )}
        {isExpanded && (
          <>
            {keys.map((key) => (
              <JsonNode
                key={key}
                keyName={key}
                value={value[key]}
                depth={depth + 1}
                expanded={expanded}
              />
            ))}
            <div style={{ marginLeft: indent }}>
              <span className="text-gray-600">{"}"}</span>
            </div>
          </>
        )}
        {!isExpanded && <span className="text-gray-600">{"}"}</span>}
      </div>
    );
  }

  // Unknown type - stringify
  return (
    <div style={{ marginLeft: indent }}>
      {keyElement}
      {keyElement && <span className="text-gray-600">: </span>}
      <span className="text-gray-600">{String(value)}</span>
    </div>
  );
};

function escapeString(str: string): string {
  return str
    .replace(/\\/g, "\\\\")
    .replace(/"/g, '\\"')
    .replace(/\n/g, "\\n")
    .replace(/\r/g, "\\r")
    .replace(/\t/g, "\\t");
}
