import React, { useState, useCallback } from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { Input } from "@/components/ui/input";

export const ChatInput: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { placeholder, disabled, maxChars } = props;
  const [text, setText] = useState("");

  const handleSubmit = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    sendEvent(nodeId, trimmed);
    setText("");
  }, [text, disabled, nodeId, sendEvent]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  return (
    <div className="sticky bottom-0 bg-background border-t py-3 px-4 mt-4">
      <div className="flex gap-2 max-w-4xl mx-auto">
        <Input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder || "Type a message..."}
          disabled={!!disabled}
          maxLength={maxChars || undefined}
          className="flex-1"
        />
        <button
          onClick={handleSubmit}
          disabled={!!disabled || !text.trim()}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  );
};
