import React, { useEffect, useState } from "react";
import type { NodeComponentProps } from "../../registry/registry";

interface Snowflake {
  id: number;
  x: number;
  delay: number;
  duration: number;
  size: number;
  opacity: number;
}

export const Snow: React.FC<NodeComponentProps> = ({ props }) => {
  const [snowflakes, setSnowflakes] = useState<Snowflake[]>([]);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    setVisible(true);
    // Generate snowflakes
    const newSnowflakes: Snowflake[] = Array.from({ length: 50 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      delay: Math.random() * 3,
      duration: 3 + Math.random() * 4,
      size: 4 + Math.random() * 8,
      opacity: 0.4 + Math.random() * 0.6,
    }));
    setSnowflakes(newSnowflakes);

    // Hide after animation
    const timer = setTimeout(() => {
      setVisible(false);
    }, 8000);

    return () => clearTimeout(timer);
  }, [props._ts]);

  if (!visible || snowflakes.length === 0) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
      {snowflakes.map((flake) => (
        <div
          key={flake.id}
          className="absolute animate-snowfall"
          style={{
            left: `${flake.x}%`,
            top: "-20px",
            width: flake.size,
            height: flake.size,
            opacity: flake.opacity,
            animationDelay: `${flake.delay}s`,
            animationDuration: `${flake.duration}s`,
          }}
        >
          <div
            className="w-full h-full rounded-full bg-white shadow-sm"
            style={{
              boxShadow: "0 0 4px rgba(255, 255, 255, 0.8)",
            }}
          />
        </div>
      ))}
      <style>{`
        @keyframes snowfall {
          0% {
            transform: translateY(0) rotate(0deg) translateX(0);
            opacity: 1;
          }
          100% {
            transform: translateY(110vh) rotate(360deg) translateX(20px);
            opacity: 0;
          }
        }
        .animate-snowfall {
          animation: snowfall linear forwards;
        }
      `}</style>
    </div>
  );
};
