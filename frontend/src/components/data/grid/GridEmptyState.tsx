import React from "react";

export const GridEmptyState: React.FC<{ message?: string | null }> = ({ message }) => {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm italic text-slate-500">
      {message || "No rows to display."}
    </div>
  );
};
