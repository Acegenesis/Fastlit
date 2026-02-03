import React, { useRef, useEffect } from "react";
import type { NodeComponentProps } from "../../registry/registry";

interface AudioProps {
  src: string;
  format?: string;
  startTime?: number;
  endTime?: number;
  loop?: boolean;
  autoplay?: boolean;
}

export const Audio: React.FC<NodeComponentProps> = ({ props }) => {
  const {
    src,
    startTime = 0,
    endTime,
    loop = false,
    autoplay = false,
  } = props as AudioProps;

  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    // Set start time
    if (startTime > 0) {
      audio.currentTime = startTime;
    }

    // Handle end time
    if (endTime !== undefined && endTime !== null) {
      const handleTimeUpdate = () => {
        if (audio.currentTime >= endTime) {
          if (loop) {
            audio.currentTime = startTime;
          } else {
            audio.pause();
          }
        }
      };
      audio.addEventListener("timeupdate", handleTimeUpdate);
      return () => audio.removeEventListener("timeupdate", handleTimeUpdate);
    }
  }, [startTime, endTime, loop]);

  if (!src) {
    return (
      <div className="text-gray-400 text-sm italic p-4 border border-gray-200 rounded">
        No audio to display
      </div>
    );
  }

  return (
    <audio
      ref={audioRef}
      src={src}
      controls
      loop={loop && !endTime}
      autoPlay={autoplay}
      className="w-full"
    />
  );
};
