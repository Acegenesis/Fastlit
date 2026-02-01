import React, { useState, useEffect } from "react";
import type { NodeComponentProps } from "../registry/registry";
import { useWidgetPublish } from "../context/WidgetStore";

export const Checkbox: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label } = props;
  const [checked, setChecked] = useState<boolean>(!!props.value);
  const publish = useWidgetPublish();

  useEffect(() => { publish(nodeId, !!props.value); }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setChecked(e.target.checked);
    publish(nodeId, e.target.checked);
    sendEvent(nodeId, e.target.checked);
  };

  return (
    <div className="mb-3 flex items-center gap-2">
      <input
        type="checkbox"
        checked={checked}
        onChange={handleChange}
        className="h-4 w-4 rounded border-gray-300 text-blue-600
                   focus:ring-2 focus:ring-blue-500"
      />
      <label className="text-sm text-gray-700">{label}</label>
    </div>
  );
};
