import React from "react";
import {
  LineChart as RechartsLineChart,
  Line,
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
}

export const LineChart: React.FC<NodeComponentProps> = ({ props }) => {
  const {
    data = [],
    xKey = "x",
    yKeys = ["y"],
    colors = ["#8884d8", "#82ca9d", "#ffc658"],
    height = 300,
    useContainerWidth = true,
  } = props as ChartProps;

  if (!data.length) {
    return (
      <div className="text-gray-400 text-sm italic p-4 border border-gray-200 rounded">
        No data to display
      </div>
    );
  }

  const chartContent = (
    <RechartsLineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
      <XAxis
        dataKey={xKey}
        tick={{ fontSize: 12 }}
        stroke="#6b7280"
      />
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
        <Line
          key={key}
          type="monotone"
          dataKey={key}
          stroke={colors[idx % colors.length]}
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
        />
      ))}
    </RechartsLineChart>
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
