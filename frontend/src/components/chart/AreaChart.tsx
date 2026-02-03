import React from "react";
import {
  AreaChart as RechartsAreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { NodeComponentProps } from "../../registry/registry";

interface ChartProps {
  data: any[];
  xKey: string;
  yKeys: string[];
  colors?: string[];
  width?: number;
  height?: number;
  useContainerWidth?: boolean;
  stack?: boolean;
}

export const AreaChart: React.FC<NodeComponentProps> = ({ props }) => {
  const {
    data = [],
    xKey = "x",
    yKeys = ["y"],
    colors = ["#8884d8", "#82ca9d", "#ffc658"],
    height = 300,
    useContainerWidth = true,
    stack = false,
  } = props as ChartProps;

  if (!data.length) {
    return (
      <div className="text-gray-400 text-sm italic p-4 border border-gray-200 rounded">
        No data to display
      </div>
    );
  }

  const chartContent = (
    <RechartsAreaChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
      <defs>
        {yKeys.map((key, idx) => (
          <linearGradient key={key} id={`gradient-${key}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={colors[idx % colors.length]} stopOpacity={0.8} />
            <stop offset="95%" stopColor={colors[idx % colors.length]} stopOpacity={0.1} />
          </linearGradient>
        ))}
      </defs>
      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
      <XAxis dataKey={xKey} tick={{ fontSize: 12 }} stroke="#6b7280" />
      <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" />
      <Tooltip
        contentStyle={{
          backgroundColor: "#fff",
          border: "1px solid #e5e7eb",
          borderRadius: "0.375rem",
          fontSize: "0.875rem",
        }}
      />
      {yKeys.length > 1 && <Legend />}
      {yKeys.map((key, idx) => (
        <Area
          key={key}
          type="monotone"
          dataKey={key}
          stackId={stack ? "1" : undefined}
          stroke={colors[idx % colors.length]}
          fill={`url(#gradient-${key})`}
        />
      ))}
    </RechartsAreaChart>
  );

  if (useContainerWidth) {
    return (
      <div style={{ width: "100%", height }}>
        <ResponsiveContainer width="100%" height="100%">
          {chartContent}
        </ResponsiveContainer>
      </div>
    );
  }

  return chartContent;
};
