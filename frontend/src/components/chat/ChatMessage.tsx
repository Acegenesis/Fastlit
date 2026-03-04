import React from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useResolvedPropText } from "../../context/WidgetStore";

const defaultAvatars: Record<string, string> = {
  user: "\u{1F464}",
  human: "\u{1F464}",
  assistant: "\u{1F916}",
  ai: "\u{1F916}",
};

export const ChatMessage: React.FC<NodeComponentProps> = ({
  props,
  children,
}) => {
  const name = useResolvedPropText(props, "name");
  const avatar = useResolvedPropText(props, "avatar");
  const normalizedName = name?.toLowerCase() || "";
  const displayAvatar = avatar || defaultAvatars[normalizedName] || "\u{1F4AC}";
  const isUser = normalizedName === "user" || normalizedName === "human";

  return (
    <div
      className={`flex gap-3 mb-4 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center text-lg">
        {displayAvatar}
      </div>
      <div
        className={`flex-1 rounded-lg px-4 py-2 ${
          isUser ? "bg-primary/10 ml-12" : "bg-muted mr-12"
        }`}
      >
        {children}
      </div>
    </div>
  );
};
