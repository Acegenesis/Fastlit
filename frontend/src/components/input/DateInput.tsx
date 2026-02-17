import React, { useState } from "react";
import { DayPicker } from "react-day-picker";
import { format, parse } from "date-fns";
import * as Popover from "@radix-ui/react-popover";
import type { NodeComponentProps } from "../../registry/registry";
import { useWidgetValue } from "../../context/WidgetStore";
import { cn } from "../../lib/utils";
import "react-day-picker/dist/style.css";

export const DateInput: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const {
    label,
    isRange,
    min,
    max,
    disabled,
    help,
    labelVisibility,
  } = props;

  const [value, setValue] = useWidgetValue(nodeId, props.value);
  const [open, setOpen] = useState(false);

  // Parse date strings to Date objects
  const parseDate = (dateStr: string | undefined): Date | undefined => {
    if (!dateStr) return undefined;
    try {
      return parse(dateStr, "yyyy-MM-dd", new Date());
    } catch {
      return undefined;
    }
  };

  const formatDate = (date: Date | undefined): string => {
    if (!date) return "";
    return format(date, "yyyy-MM-dd");
  };

  const handleSelect = (date: Date | undefined) => {
    if (!date) return;
    const dateStr = formatDate(date);
    setValue(dateStr);
    sendEvent(nodeId, dateStr, { noRerun: props.noRerun });
    setOpen(false);
  };

  const handleRangeSelect = (range: { from?: Date; to?: Date } | undefined) => {
    if (!range) return;
    const fromStr = range.from ? formatDate(range.from) : value?.[0] || "";
    const toStr = range.to ? formatDate(range.to) : "";
    const newValue = [fromStr, toStr];
    setValue(newValue);
    if (range.from && range.to) {
      sendEvent(nodeId, newValue, { noRerun: props.noRerun });
      setOpen(false);
    }
  };

  const showLabel = labelVisibility !== "hidden" && labelVisibility !== "collapsed";

  const selectedDate = isRange
    ? undefined
    : parseDate(typeof value === "string" ? value : undefined);

  const selectedRange = isRange && Array.isArray(value)
    ? { from: parseDate(value[0]), to: parseDate(value[1]) }
    : undefined;

  const displayValue = isRange && Array.isArray(value)
    ? `${value[0] || "Start"} → ${value[1] || "End"}`
    : (typeof value === "string" ? value : "Select date");

  const minDate = min ? parseDate(min) : undefined;
  const maxDate = max ? parseDate(max) : undefined;

  return (
    <div className="mb-3">
      {showLabel && label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {help && (
            <span className="ml-1 text-gray-400 cursor-help" title={help}>
              ?
            </span>
          )}
        </label>
      )}

      <Popover.Root open={open} onOpenChange={setOpen}>
        <Popover.Trigger asChild>
          <button
            disabled={!!disabled}
            className={cn(
              "w-full px-3 py-2 text-left border border-gray-300 rounded-md shadow-sm",
              "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
              "flex items-center justify-between",
              disabled ? "opacity-50 cursor-not-allowed bg-gray-100" : "bg-white cursor-pointer"
            )}
          >
            <span className={!value ? "text-gray-400" : ""}>
              {displayValue}
            </span>
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </button>
        </Popover.Trigger>

        <Popover.Portal>
          <Popover.Content
            className="z-50 bg-white rounded-lg shadow-lg border border-gray-200 p-3"
            sideOffset={5}
          >
            {isRange ? (
              <DayPicker
                mode="range"
                selected={selectedRange}
                onSelect={handleRangeSelect}
                fromDate={minDate}
                toDate={maxDate}
                numberOfMonths={2}
                className="text-sm"
                classNames={{
                  day_selected: "bg-blue-600 text-white rounded-full",
                  day_today: "font-bold text-blue-600",
                  day_range_middle: "bg-blue-100",
                  day_range_start: "bg-blue-600 text-white rounded-l-full",
                  day_range_end: "bg-blue-600 text-white rounded-r-full",
                }}
              />
            ) : (
              <DayPicker
                mode="single"
                selected={selectedDate}
                onSelect={handleSelect}
                fromDate={minDate}
                toDate={maxDate}
                captionLayout="dropdown"
                className="text-sm"
                classNames={{
                  day_selected: "bg-blue-600 text-white rounded-full",
                  day_today: "font-bold text-blue-600",
                }}
              />
            )}
            <Popover.Arrow className="fill-white" />
          </Popover.Content>
        </Popover.Portal>
      </Popover.Root>
    </div>
  );
};
