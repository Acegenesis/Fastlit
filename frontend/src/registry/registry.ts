/**
 * Component registry: maps node type strings to React components.
 */

import type { ComponentType } from "react";
import { Title } from "../components/Title";
import { Header } from "../components/Header";
import { Markdown } from "../components/Markdown";
import { TextBlock } from "../components/TextBlock";
import { Button } from "../components/Button";

export interface NodeComponentProps {
  nodeId: string;
  props: Record<string, any>;
  children?: React.ReactNode;
  sendEvent: (id: string, value: any) => void;
}

const registry: Record<string, ComponentType<NodeComponentProps>> = {
  title: Title,
  header: Header,
  subheader: Header, // reuse with prop
  markdown: Markdown,
  text: TextBlock,
  button: Button,
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
