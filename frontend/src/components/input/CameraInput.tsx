import React, { useRef, useState, useCallback, useEffect } from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { Label } from "@/components/ui/label";

export const CameraInput: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const { label, help, disabled, labelVisibility } = props;
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [captured, setCaptured] = useState<string | null>(null);
  const [isVideoReady, setIsVideoReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const stopStream = useCallback(() => {
    stream?.getTracks().forEach((t) => t.stop());
    setStream(null);
  }, [stream]);

  const startCamera = useCallback(async () => {
    if (disabled) return;
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Camera API not available in this browser.");
      return;
    }
    try {
      stopStream();
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user" },
      });
      setStream(mediaStream);
      setIsVideoReady(false);
      setCaptured(null);
      setError(null);
    } catch {
      setError("Unable to access camera. Check browser permission settings.");
    }
  }, [disabled, stopStream]);

  useEffect(() => {
    if (!stream || !videoRef.current) return;
    const video = videoRef.current;
    video.srcObject = stream;

    const onLoadedMetadata = () => {
      setIsVideoReady(true);
    };

    video.addEventListener("loadedmetadata", onLoadedMetadata);
    const playPromise = video.play();
    if (playPromise) {
      void playPromise.catch(() => {
        // Browser autoplay policy edge cases.
      });
    }
    if (video.readyState >= 1) {
      setIsVideoReady(true);
    }

    return () => {
      video.removeEventListener("loadedmetadata", onLoadedMetadata);
      if (video.srcObject === stream) {
        video.srcObject = null;
      }
    };
  }, [stream]);

  useEffect(() => {
    return () => {
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, [stream]);

  const capture = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    if (!isVideoReady || video.videoWidth <= 0 || video.videoHeight <= 0) {
      return;
    }
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0);

    const dataUrl = canvas.toDataURL("image/png");
    const base64 = dataUrl.split(",")[1];
    setCaptured(dataUrl);

    // Stop camera
    stopStream();

    sendEvent(nodeId, {
      name: "camera_capture.png",
      type: "image/png",
      content: base64,
    });
  }, [isVideoReady, stopStream, nodeId, sendEvent]);

  const clear = useCallback(() => {
    setCaptured(null);
    setIsVideoReady(false);
    setError(null);
    stopStream();
    sendEvent(nodeId, null);
  }, [stopStream, nodeId, sendEvent]);

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

      {captured ? (
        <div className="space-y-2">
          <img
            src={captured}
            alt="Captured"
            className="rounded-md border max-w-sm"
          />
          <button
            onClick={clear}
            className="px-3 py-1 text-sm border rounded-md hover:bg-muted"
          >
            Retake
          </button>
        </div>
      ) : stream ? (
        <div className="space-y-2">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="rounded-md border max-w-sm"
          />
          {!isVideoReady && (
            <p className="text-xs text-muted-foreground">Starting camera preview...</p>
          )}
          <button
            onClick={capture}
            disabled={!isVideoReady}
            className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Capture
          </button>
        </div>
      ) : (
        <button
          onClick={startCamera}
          disabled={!!disabled}
          className="px-4 py-2 text-sm border rounded-md hover:bg-muted disabled:opacity-50"
        >
          Open Camera
        </button>
      )}
      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
};
