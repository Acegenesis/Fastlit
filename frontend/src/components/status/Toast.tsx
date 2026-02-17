import React, { useEffect } from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { toast } from "sonner";

export const Toast: React.FC<NodeComponentProps> = ({ props }) => {
  const { body, icon } = props;

  useEffect(() => {
    toast(body, {
      icon: icon ? <span className="text-lg">{icon}</span> : undefined,
      duration: 4000,
    });
  }, [body, icon]);

  return null;
};
