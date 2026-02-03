import React, { useRef, useEffect } from "react";
import type { NodeComponentProps } from "../../registry/registry";

interface SubtitleTrack {
  label: string;
  src: string;
}

interface VideoProps {
  src: string;
  format?: string;
  startTime?: number;
  endTime?: number;
  loop?: boolean;
  autoplay?: boolean;
  muted?: boolean;
  subtitles?: SubtitleTrack[];
}

export const Video: React.FC<NodeComponentProps> = ({ props }) => {
  const {
    src,
    startTime = 0,
    endTime,
    loop = false,
    autoplay = false,
    muted = false,
    subtitles,
  } = props as VideoProps;

  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    // Set start time
    if (startTime > 0) {
      video.currentTime = startTime;
    }

    // Handle end time
    if (endTime !== undefined && endTime !== null) {
      const handleTimeUpdate = () => {
        if (video.currentTime >= endTime) {
          if (loop) {
            video.currentTime = startTime;
          } else {
            video.pause();
          }
        }
      };
      video.addEventListener("timeupdate", handleTimeUpdate);
      return () => video.removeEventListener("timeupdate", handleTimeUpdate);
    }
  }, [startTime, endTime, loop]);

  if (!src) {
    return (
      <div className="text-gray-400 text-sm italic p-4 border border-gray-200 rounded">
        No video to display
      </div>
    );
  }

  return (
    <video
      ref={videoRef}
      src={src}
      controls
      loop={loop && !endTime}
      autoPlay={autoplay}
      muted={muted}
      className="w-full rounded"
    >
      {subtitles?.map((track, idx) => (
        <track
          key={idx}
          kind="subtitles"
          label={track.label}
          src={track.src}
          default={idx === 0}
        />
      ))}
    </video>
  );
};
