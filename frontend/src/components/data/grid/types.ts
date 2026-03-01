export type GridPinned = "left" | "right" | null;
export type GridSortDirection = "asc" | "desc";

export interface GridSort {
  column: string;
  direction: GridSortDirection;
}

export interface GridFilter {
  id: string;
  column: string;
  op: string;
  value: any;
}

export interface GridColumn {
  name: string;
  type: string;
  label: string;
  help?: string | null;
  hidden?: boolean;
  disabled?: boolean;
  required?: boolean;
  width?: string | number | null;
  minWidth?: number | null;
  maxWidth?: number | null;
  resizable?: boolean | null;
  pinned?: GridPinned;
  options?: string[];
  displayText?: string | null;
  format?: string | null;
  default?: any;
  min?: number | string | null;
  max?: number | string | null;
  step?: number | string | null;
  maxChars?: number | null;
  validate?: string | null;
  yMin?: number | null;
  yMax?: number | null;
}

export interface GridRowModel {
  rowId: string;
  originalPosition: number;
  indexValue?: any;
  cells: any[];
}

export interface GridViewState {
  search: string;
  sorts: GridSort[];
  filters: GridFilter[];
  hiddenColumns: string[];
  manualWidths: Record<string, number>;
  pinnedColumns: Record<string, GridPinned>;
  columnOrder: string[];
  scrollTop: number;
  scrollLeft: number;
}

export interface GridResolvedColumn extends GridColumn {
  originalIndex: number;
  widthPx: number;
  pinned: GridPinned;
  leftOffset?: number;
  rightOffset?: number;
}
