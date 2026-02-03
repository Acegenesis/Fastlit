import React from "react";
import {
  ScatterChart as RechartsScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ZAxis,
} from "recharts";
import type { NodeComponentProps } from "../../registry/registry";

interface ChartProps {
  data: any[];
  xKey: string;
  yKeys: string[];
  color?: string;
  sizeKey?: string;
  width?: number;
  height?: number;
  useContainerWidth?: boolean;
}

export const ScatterChart: React.FC<NodeComponentProps> = ({ props }) => {
  const {
    data = [],
    xKey = "x",
    yKeys = ["y"],
    color = "#8884d8",
    sizeKey,
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

  const yKey = yKeys[0] || "y";

  const chartContent = (
    <RechartsScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
      <XAxis
        type="number"
        dataKey={xKey}
        name={xKey}
        tick={{ fontSize: 12 }}
        stroke="#6b7280"
      />
      <YAxis
        type="number"
        dataKey={yKey}
        name={yKey}
        tick={{ fontSize: 12 }}
        stroke="#6b7280"
      />
      {sizeKey && <ZAxis type="number" dataKey={sizeKey} range={[60, 400]} />}
      <Tooltip
        cursor={{ strokeDasharray: "3 3" }}
        contentStyle={{
          backgroundColor: "#fff",
          border: "1px solid #e5e7eb",
          borderRadius: "0.375rem",
          fontSize: "0.875rem",
        }}
      />
      <Scatter data={data} fill={color} />
    </RechartsScatterChart>
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
