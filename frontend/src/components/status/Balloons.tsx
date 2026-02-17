import React, { useEffect, useState } from "react";
import type { NodeComponentProps } from "../../registry/registry";

const BALLOON_COLORS = [
  "#FF6B6B",
  "#4ECDC4",
  "#45B7D1",
  "#96CEB4",
  "#FFEAA7",
  "#DDA0DD",
  "#98D8C8",
  "#F7DC6F",
];

interface Balloon {
  id: number;
  x: number;
  color: string;
  delay: number;
  duration: number;
  size: number;
}

export const Balloons: React.FC<NodeComponentProps> = () => {
  const [balloons, setBalloons] = useState<Balloon[]>([]);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    // Generate balloons
    const newBalloons: Balloon[] = Array.from({ length: 20 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      color: BALLOON_COLORS[Math.floor(Math.random() * BALLOON_COLORS.length)],
      delay: Math.random() * 0.5,
      duration: 2 + Math.random() * 2,
      size: 30 + Math.random() * 20,
    }));
    setBalloons(newBalloons);

    // Hide after animation
    const timer = setTimeout(() => {
      setVisible(false);
    }, 5000);

    return () => clearTimeout(timer);
  }, []);

  if (!visible || balloons.length === 0) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
      {balloons.map((balloon) => (
        <div
          key={balloon.id}
          className="absolute animate-balloon"
          style={{
            left: `${balloon.x}%`,
            bottom: "-100px",
            animationDelay: `${balloon.delay}s`,
            animationDuration: `${balloon.duration}s`,
          }}
        >
          <svg
            width={balloon.size}
            height={balloon.size * 1.2}
            viewBox="0 0 40 48"
            fill="none"
          >
            <ellipse cx="20" cy="18" rx="18" ry="18" fill={balloon.color} />
            <path
              d="M20 36 L18 48 M20 36 L22 48"
              stroke={balloon.color}
              strokeWidth="1.5"
              opacity="0.7"
            />
          </svg>
        </div>
      ))}
      <style>{`
        @keyframes balloon-rise {
          0% {
            transform: translateY(0) rotate(0deg);
            opacity: 1;
          }
          100% {
            transform: translateY(-120vh) rotate(20deg);
            opacity: 0;
          }
        }
        .animate-balloon {
          animation: balloon-rise ease-out forwards;
        }
      `}</style>
    </div>
  );
};
