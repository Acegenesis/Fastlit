import React, { useRef, useState, useCallback } from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { Label } from "@/components/ui/label";

export const AudioInput: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, help, disabled, labelVisibility } = props;
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [recording, setRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  const startRecording = useCallback(async () => {
    if (disabled) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setAudioUrl(URL.createObjectURL(blob));

        // Convert to base64
        const reader = new FileReader();
        reader.onload = () => {
          const base64 = (reader.result as string).split(",")[1];
          sendEvent(nodeId, {
            name: "recording.webm",
            type: "audio/webm",
            content: base64,
          });
        };
        reader.readAsDataURL(blob);
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setRecording(true);
      setAudioUrl(null);
    } catch {
      // Microphone access denied
    }
  }, [disabled, nodeId, sendEvent]);

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  }, []);

  const clear = useCallback(() => {
    setAudioUrl(null);
    sendEvent(nodeId, null);
  }, [nodeId, sendEvent]);

  return (
    <div className="mb-3" title={help || undefined}>
      {labelVisibility !== "collapsed" && (
        <Label
          className={`mb-2 block ${
            labelVisibility === "hidden" ? "sr-only" : ""
          }`}
        >
          {label}
        </Label>
      )}

      <div className="flex items-center gap-2">
        {recording ? (
          <button
            onClick={stopRecording}
            className="px-4 py-2 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 flex items-center gap-2"
          >
            <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
            Stop Recording
          </button>
        ) : (
          <button
            onClick={startRecording}
            disabled={!!disabled}
            className="px-4 py-2 text-sm border rounded-md hover:bg-muted disabled:opacity-50"
          >
            Record Audio
          </button>
        )}

        {audioUrl && !recording && (
          <>
            <audio src={audioUrl} controls className="h-8" />
            <button
              onClick={clear}
              className="px-2 py-1 text-xs border rounded hover:bg-muted"
            >
              Clear
            </button>
          </>
        )}
      </div>
    </div>
  );
};
