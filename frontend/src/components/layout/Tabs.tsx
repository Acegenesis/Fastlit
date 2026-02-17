import React, { useState } from "react";
import type { NodeComponentProps } from "../../registry/registry";
import {
  Tabs as ShadcnTabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";

export const Tabs: React.FC<NodeComponentProps> = ({
  props,
  children,
}) => {
  const labels = (props.labels as string[]) ?? [];
  const defaultIndex = (props.defaultIndex as number) ?? 0;
  const [activeIndex, setActiveIndex] = useState(defaultIndex);

  const childArray = React.Children.toArray(children);

  return (
    <ShadcnTabs
      value={String(activeIndex)}
      onValueChange={(val) => setActiveIndex(parseInt(val, 10))}
      className="mb-3"
    >
      <TabsList>
        {labels.map((label, i) => (
          <TabsTrigger key={i} value={String(i)}>
            {label}
          </TabsTrigger>
        ))}
      </TabsList>
      {childArray.map((child, i) => (
        <TabsContent key={i} value={String(i)}>
          {child}
        </TabsContent>
      ))}
    </ShadcnTabs>
  );
};
