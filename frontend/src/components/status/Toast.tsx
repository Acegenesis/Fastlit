import React, { useEffect } from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { toast } from "sonner";
import { useResolvedPropText } from "../../context/WidgetStore";

export const Toast: React.FC<NodeComponentProps> = ({ props }) => {
  const { _ts } = props;
  const body = useResolvedPropText(props, "body");
  const icon = useResolvedPropText(props, "icon");

  useEffect(() => {
    toast(body, {
      icon: icon ? <span className="text-lg">{icon}</span> : undefined,
      duration: 4000,
    });
  }, [_ts]);

  return null;
};
