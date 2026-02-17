import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { Alert as ShadcnAlert, AlertDescription } from "@/components/ui/alert";
import { CheckCircle, Info, AlertTriangle, XCircle } from "lucide-react";

const iconMap = {
  success: CheckCircle,
  info: Info,
  warning: AlertTriangle,
  error: XCircle,
};

const variantMap: Record<string, "default" | "destructive" | "success" | "warning" | "info"> = {
  success: "success",
  info: "info",
  warning: "warning",
  error: "destructive",
};

export const Alert: React.FC<NodeComponentProps> = ({ props }) => {
  const { type = "info", body, icon } = props;
  const IconComponent = iconMap[type as keyof typeof iconMap] || Info;
  const variant = variantMap[type as keyof typeof variantMap] || "default";

  return (
    <ShadcnAlert variant={variant} className="mb-3">
      {icon ? (
        <span className="flex-shrink-0 text-lg mr-2">{icon}</span>
      ) : (
        <IconComponent className="h-4 w-4" />
      )}
      <AlertDescription>{body}</AlertDescription>
    </ShadcnAlert>
  );
};
