/**
 * Component registry: maps node type strings to React components.
 *
 * Naming convention:
 *   - Folders: lowercase, matching Streamlit API categories
 *       text/     — Write and magic, Text elements
 *       input/    — Input widgets
 *       layout/   — Layouts and containers
 *       data/     — Data elements (future)
 *       chart/    — Chart elements (future)
 *       media/    — Media elements (future)
 *       chat/     — Chat elements (future)
 *       status/   — Status elements (future)
 *   - Files: PascalCase.tsx, matching the exported component name
 *   - No "Component" suffix — use clean names (Expander, not ExpanderComponent)
 */

import type { ComponentType } from "react";

// ---- Text elements ----
import { Title } from "../components/text/Title";
import { Header } from "../components/text/Header";
import { Markdown } from "../components/text/Markdown";
import { Text } from "../components/text/Text";

// ---- Input widgets ----
import { Button } from "../components/input/Button";
import { Slider } from "../components/input/Slider";
import { TextInput } from "../components/input/TextInput";
import { TextArea } from "../components/input/TextArea";
import { Checkbox } from "../components/input/Checkbox";
import { Selectbox } from "../components/input/Selectbox";
import { Radio } from "../components/input/Radio";
import { NumberInput } from "../components/input/NumberInput";

// ---- Data elements ----
import { DataFrame, Table } from "../components/data/DataFrame";
import { DataEditor } from "../components/data/DataEditor";
import { Metric } from "../components/data/Metric";
import { Json } from "../components/data/Json";

// ---- Chart elements ----
import { LineChart } from "../components/chart/LineChart";
import { BarChart } from "../components/chart/BarChart";
import { AreaChart } from "../components/chart/AreaChart";
import { ScatterChart } from "../components/chart/ScatterChart";
import { Map } from "../components/chart/Map";
import { PlotlyChart } from "../components/chart/PlotlyChart";
import { VegaLiteChart } from "../components/chart/VegaLiteChart";
import { Pyplot } from "../components/chart/Pyplot";
import { GraphvizChart } from "../components/chart/GraphvizChart";

// ---- Layouts and containers ----
import { Sidebar } from "../components/layout/Sidebar";
import { Columns } from "../components/layout/Columns";
import { Column } from "../components/layout/Column";
import { Tabs } from "../components/layout/Tabs";
import { Tab } from "../components/layout/Tab";
import { Expander } from "../components/layout/Expander";
import { Container } from "../components/layout/Container";
import { Empty } from "../components/layout/Empty";
import { Form } from "../components/layout/Form";
import { FormSubmitButton } from "../components/layout/FormSubmitButton";
import { Dialog } from "../components/layout/Dialog";
import { Popover } from "../components/layout/Popover";
import { Divider } from "../components/layout/Divider";
import { Navigation } from "../components/layout/Navigation";

export interface SendEventOptions {
  noRerun?: boolean;
}

export interface NodeComponentProps {
  nodeId: string;
  props: Record<string, any>;
  children?: React.ReactNode;
  sendEvent: (id: string, value: any, options?: SendEventOptions) => void;
}

const registry: Record<string, ComponentType<NodeComponentProps>> = {
  // Text elements
  title: Title,
  header: Header,
  subheader: Header,
  markdown: Markdown,
  text: Text,

  // Input widgets
  button: Button,
  slider: Slider,
  text_input: TextInput,
  text_area: TextArea,
  checkbox: Checkbox,
  selectbox: Selectbox,
  radio: Radio,
  number_input: NumberInput,

  // Data elements
  dataframe: DataFrame,
  data_editor: DataEditor,
  table: Table,
  metric: Metric,
  json: Json,

  // Chart elements
  line_chart: LineChart,
  bar_chart: BarChart,
  area_chart: AreaChart,
  scatter_chart: ScatterChart,
  map: Map,
  plotly_chart: PlotlyChart,
  vega_lite_chart: VegaLiteChart,
  pyplot: Pyplot,
  graphviz_chart: GraphvizChart,

  // Layouts and containers
  sidebar: Sidebar,
  columns: Columns,
  column: Column,
  tabs: Tabs,
  tab: Tab,
  expander: Expander,
  container: Container,
  empty: Empty,
  form: Form,
  form_submit_button: FormSubmitButton,
  dialog: Dialog,
  popover: Popover,
  divider: Divider,
  navigation: Navigation,
};

export function getComponent(
  type: string
): ComponentType<NodeComponentProps> | null {
  return registry[type] ?? null;
}

export function registerComponent(
  type: string,
  component: ComponentType<NodeComponentProps>
): void {
  registry[type] = component;
}