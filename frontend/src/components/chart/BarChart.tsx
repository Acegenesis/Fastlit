import React from "react";
import {
  BarChart as RechartsBarChart,
  Bar,
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
  horizontal?: boolean;
}

export const BarChart: React.FC<NodeComponentProps> = ({ props }) => {
  const {
    data = [],
    xKey = "x",
    yKeys = ["y"],
    colors = ["#8884d8", "#82ca9d", "#ffc658"],
    height = 300,
    useContainerWidth = true,
    horizontal = false,
  } = props as ChartProps;

  if (!data.length) {
    return (
      <div className="text-gray-400 text-sm italic p-4 border border-gray-200 rounded">
        No data to display
      </div>
    );
  }

  const chartContent = (
    <RechartsBarChart
      data={data}
      layout={horizontal ? "vertical" : "horizontal"}
      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
    >
      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
      {horizontal ? (
        <>
          <XAxis type="number" tick={{ fontSize: 12 }} stroke="#6b7280" />
          <YAxis dataKey={xKey} type="category" tick={{ fontSize: 12 }} stroke="#6b7280" />
        </>
      ) : (
        <>
          <XAxis dataKey={xKey} tick={{ fontSize: 12 }} stroke="#6b7280" />
          <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" />
        </>
      )}
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
        <Bar
          key={key}
          dataKey={key}
          fill={colors[idx % colors.length]}
          radius={[4, 4, 0, 0]}
        />
      ))}
    </RechartsBarChart>
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
