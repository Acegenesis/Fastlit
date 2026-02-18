import React from "react";
import type { NodeComponentProps } from "../../registry/registry";

const defaultAvatars: Record<string, string> = {
  user: "👤",
  human: "👤",
  assistant: "🤖",
  ai: "🤖",
};

export const ChatMessage: React.FC<NodeComponentProps> = ({
  props,
  children,
}) => {
  const { name, avatar } = props;
  const displayAvatar = avatar || defaultAvatars[name?.toLowerCase()] || "💬";
  const isUser = name?.toLowerCase() === "user" || name?.toLowerCase() === "human";

  return (
    <div
      className={`flex gap-3 mb-4 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center text-lg">
        {displayAvatar}
      </div>
      <div
        className={`flex-1 rounded-lg px-4 py-2 ${
          isUser
            ? "bg-primary/10 ml-12"
            : "bg-muted mr-12"
        }`}
      >
        {children}
      </div>
    </div>
  );
};
