/**
 * Component registry: maps node type strings to React components.
 */

import type { ComponentType } from "react";
import { Title } from "../components/Title";
import { Header } from "../components/Header";
import { Markdown } from "../components/Markdown";
import { TextBlock } from "../components/TextBlock";
import { Button } from "../components/Button";
import { Slider } from "../components/Slider";
import { TextInput } from "../components/TextInput";
import { TextArea } from "../components/TextArea";
import { Checkbox } from "../components/Checkbox";
import { Selectbox } from "../components/Selectbox";
import { Radio } from "../components/Radio";
import { NumberInput } from "../components/NumberInput";
import { Sidebar } from "../components/Sidebar";
import { Columns } from "../components/Columns";
import { ColumnComponent } from "../components/ColumnComponent";
import { TabsComponent } from "../components/TabsComponent";
import { TabPanel } from "../components/TabPanel";
import { ExpanderComponent } from "../components/ExpanderComponent";

export interface NodeComponentProps {
  nodeId: string;
  props: Record<string, any>;
  children?: React.ReactNode;
  sendEvent: (id: string, value: any) => void;
}

const registry: Record<string, ComponentType<NodeComponentProps>> = {
  title: Title,
  header: Header,
  subheader: Header,
  markdown: Markdown,
  text: TextBlock,
  button: Button,
  slider: Slider,
  text_input: TextInput,
  text_area: TextArea,
  checkbox: Checkbox,
  selectbox: Selectbox,
  radio: Radio,
  number_input: NumberInput,
  sidebar: Sidebar,
  columns: Columns,
  column: ColumnComponent,
  tabs: TabsComponent,
  tab: TabPanel,
  expander: ExpanderComponent,
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
