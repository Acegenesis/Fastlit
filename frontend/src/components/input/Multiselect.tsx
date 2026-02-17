import React, { useState, useRef, useEffect } from "react";
import type { NodeComponentProps } from "../../registry/registry";
import { useWidgetValue } from "../../context/WidgetStore";
import { cn } from "../../lib/utils";

export const Multiselect: React.FC<NodeComponentProps> = ({
  nodeId,
  props,
  sendEvent,
}) => {
  const {
    label,
    options = [],
    defaultValues = [],
    maxSelections,
    placeholder = "Select...",
    disabled,
    help,
    labelVisibility,
  } = props;

  // Store actual values (strings) instead of indices for real-time text interpolation
  const [selectedValues, setSelectedValues] = useWidgetValue(
    nodeId,
    props.selectedValues ?? defaultValues
  );
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredOptions = options.filter((opt: string) =>
    opt.toLowerCase().includes(search.toLowerCase())
  );

  const toggleOption = (optionValue: string) => {
    let newValues: string[];
    if (selectedValues.includes(optionValue)) {
      newValues = selectedValues.filter((v: string) => v !== optionValue);
    } else {
      if (maxSelections && selectedValues.length >= maxSelections) {
        return; // Max selections reached
      }
      newValues = [...selectedValues, optionValue];
    }
    setSelectedValues(newValues);
    sendEvent(nodeId, newValues, { noRerun: props.noRerun });
  };

  const removeOption = (optionValue: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newValues = selectedValues.filter((v: string) => v !== optionValue);
    setSelectedValues(newValues);
    sendEvent(nodeId, newValues, { noRerun: props.noRerun });
  };

  const showLabel = labelVisibility !== "hidden" && labelVisibility !== "collapsed";

  return (
    <div className="mb-3" ref={containerRef}>
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

      <div
        className={cn(
          "relative border rounded-md bg-white",
          disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer",
          isOpen ? "ring-2 ring-blue-500 border-blue-500" : "border-gray-300"
        )}
        onClick={() => !disabled && setIsOpen(!isOpen)}
      >
        {/* Selected chips */}
        <div className="flex flex-wrap gap-1 p-2 min-h-[38px]">
          {selectedValues.length === 0 ? (
            <span className="text-gray-400">{placeholder}</span>
          ) : (
            selectedValues.map((value: string) => (
              <span
                key={value}
                className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-800 text-sm rounded"
              >
                {value}
                {!disabled && (
                  <button
                    onClick={(e) => removeOption(value, e)}
                    className="hover:text-blue-600"
                  >
                    ×
                  </button>
                )}
              </span>
            ))
          )}
        </div>

        {/* Dropdown */}
        {isOpen && !disabled && (
          <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
            {/* Search input */}
            <div className="p-2 border-b">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search..."
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                onClick={(e) => e.stopPropagation()}
              />
            </div>

            {/* Options */}
            {filteredOptions.map((opt: string) => {
              const isSelected = selectedValues.includes(opt);
              const isDisabledOption =
                !isSelected && maxSelections && selectedValues.length >= maxSelections;

              return (
                <div
                  key={opt}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (!isDisabledOption) toggleOption(opt);
                  }}
                  className={cn(
                    "px-3 py-2 text-sm cursor-pointer flex items-center gap-2",
                    isSelected && "bg-blue-50 text-blue-800",
                    isDisabledOption && "opacity-50 cursor-not-allowed",
                    !isSelected && !isDisabledOption && "hover:bg-gray-100"
                  )}
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    readOnly
                    className="h-4 w-4 rounded border-gray-300 text-blue-600"
                  />
                  {opt}
                </div>
              );
            })}

            {filteredOptions.length === 0 && (
              <div className="px-3 py-2 text-sm text-gray-500">No options found</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
