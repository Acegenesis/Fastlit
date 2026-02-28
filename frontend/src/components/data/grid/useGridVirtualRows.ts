import { useVirtualizer } from "@tanstack/react-virtual";

export function useGridVirtualRows({
  rowCount,
  parentRef,
  rowHeight,
}: {
  rowCount: number;
  parentRef: React.RefObject<HTMLElement>;
  rowHeight: number;
}) {
  return useVirtualizer({
    count: rowCount,
    getScrollElement: () => parentRef.current,
    estimateSize: () => rowHeight,
    overscan: 6,
  });
}
