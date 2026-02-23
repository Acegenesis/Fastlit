/**
 * Component registry: maps node type strings to React components.
 */

import React, { Suspense } from "react";
import type { ComponentType } from "react";

// ---- Text elements ----
import { Title } from "../components/text/Title";
import { Header } from "../components/text/Header";
import { Markdown } from "../components/text/Markdown";
import { Text } from "../components/text/Text";
import { Code } from "../components/text/Code";
import { Caption } from "../components/text/Caption";
import { Latex } from "../components/text/Latex";
import { Html } from "../components/text/Html";
import { Badge } from "../components/text/Badge";

// ---- Input widgets ----
import { Button } from "../components/input/Button";
import { Slider } from "../components/input/Slider";
import { TextInput } from "../components/input/TextInput";
import { TextArea } from "../components/input/TextArea";
import { Checkbox } from "../components/input/Checkbox";
import { Selectbox } from "../components/input/Selectbox";
import { Radio } from "../components/input/Radio";
import { NumberInput } from "../components/input/NumberInput";
import { Multiselect } from "../components/input/Multiselect";
import { DateInput } from "../components/input/DateInput";
import { TimeInput } from "../components/input/TimeInput";
import { Toggle } from "../components/input/Toggle";
import { ColorPicker } from "../components/input/ColorPicker";
import { LinkButton } from "../components/input/LinkButton";
import { DownloadButton } from "../components/input/DownloadButton";
import { PageLink } from "../components/input/PageLink";
import { SelectSlider } from "../components/input/SelectSlider";
import { Feedback } from "../components/input/Feedback";
import { Pills } from "../components/input/Pills";
import { SegmentedControl } from "../components/input/SegmentedControl";

// ---- Chat elements ----
import { ChatMessage } from "../components/chat/ChatMessage";
import { ChatInput } from "../components/chat/ChatInput";

// ---- Data elements ----
import { DataFrame, Table } from "../components/data/DataFrame";
import { Metric } from "../components/data/Metric";

// ---- Chart elements (already lazy) ----
import {
  LineChart,
  BarChart,
  AreaChart,
  ScatterChart,
  Map,
  PlotlyChart,
  VegaLiteChart,
  Pyplot,
  GraphvizChart,
  BokehChart,
  PydeckChart,
} from "../components/chart/LazyCharts";

// ---- Media elements ----
import { Image } from "../components/media/Image";

// ---- Status elements ----
import { Alert } from "../components/status/Alert";
import { Progress } from "../components/status/Progress";
import { Spinner } from "../components/status/Spinner";

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
import { Divider } from "../components/layout/Divider";
import { Navigation } from "../components/layout/Navigation";
import { PageConfig } from "../components/layout/PageConfig";
import { Fragment } from "../components/layout/Fragment";

export interface SendEventOptions {
  noRerun?: boolean;
}

export interface NodeComponentProps {
  nodeId: string;
  props: Record<string, any>;
  children?: React.ReactNode;
  sendEvent: (id: string, value: any, options?: SendEventOptions) => void;
}

function lazyNode(
  loader: () => Promise<{ default: ComponentType<NodeComponentProps> }>
): ComponentType<NodeComponentProps> {
  const LazyComp = React.lazy(loader);
  const Wrapped: React.FC<NodeComponentProps> = (props) =>
    React.createElement(
      Suspense,
      { fallback: null },
      React.createElement(LazyComp, props)
    );
  return Wrapped;
}

const loadDataEditor = () =>
  import("../components/data/DataEditor").then((m) => ({ default: m.DataEditor }));
const loadJson = () =>
  import("../components/data/Json").then((m) => ({ default: m.Json }));
const loadFileUploader = () =>
  import("../components/input/FileUploader").then((m) => ({ default: m.FileUploader }));
const loadCameraInput = () =>
  import("../components/input/CameraInput").then((m) => ({ default: m.CameraInput }));
const loadAudioInput = () =>
  import("../components/input/AudioInput").then((m) => ({ default: m.AudioInput }));
const loadAudio = () =>
  import("../components/media/Audio").then((m) => ({ default: m.Audio }));
const loadVideo = () =>
  import("../components/media/Video").then((m) => ({ default: m.Video }));
const loadLogo = () =>
  import("../components/media/Logo").then((m) => ({ default: m.Logo }));
const loadPdf = () =>
  import("../components/media/Pdf").then((m) => ({ default: m.Pdf }));
const loadDialog = () =>
  import("../components/layout/Dialog").then((m) => ({ default: m.Dialog }));
const loadPopover = () =>
  import("../components/layout/Popover").then((m) => ({ default: m.Popover }));
const loadException = () =>
  import("../components/status/Exception").then((m) => ({ default: m.Exception }));
const loadStatus = () =>
  import("../components/status/Status").then((m) => ({ default: m.Status }));
const loadToast = () =>
  import("../components/status/Toast").then((m) => ({ default: m.Toast }));
const loadBalloons = () =>
  import("../components/status/Balloons").then((m) => ({ default: m.Balloons }));
const loadSnow = () =>
  import("../components/status/Snow").then((m) => ({ default: m.Snow }));

const DataEditor = lazyNode(loadDataEditor);
const Json = lazyNode(loadJson);
const FileUploader = lazyNode(loadFileUploader);
const CameraInput = lazyNode(loadCameraInput);
const AudioInput = lazyNode(loadAudioInput);
const Audio = lazyNode(loadAudio);
const Video = lazyNode(loadVideo);
const Logo = lazyNode(loadLogo);
const Pdf = lazyNode(loadPdf);
const Dialog = lazyNode(loadDialog);
const Popover = lazyNode(loadPopover);
const Exception = lazyNode(loadException);
const Status = lazyNode(loadStatus);
const Toast = lazyNode(loadToast);
const Balloons = lazyNode(loadBalloons);
const Snow = lazyNode(loadSnow);

const chunkPrefetchers: Record<string, () => Promise<unknown>> = {
  data_editor: loadDataEditor,
  json: loadJson,
  file_uploader: loadFileUploader,
  camera_input: loadCameraInput,
  audio_input: loadAudioInput,
  audio: loadAudio,
  video: loadVideo,
  logo: loadLogo,
  pdf: loadPdf,
  dialog: loadDialog,
  popover: loadPopover,
  exception: loadException,
  status: loadStatus,
  toast: loadToast,
  balloons: loadBalloons,
  snow: loadSnow,
};

// Control nodes that render nothing (processed by App.tsx as side-effects)
const NullComponent: ComponentType<NodeComponentProps> = () => null as any;
const Subheader: ComponentType<NodeComponentProps> = (nodeProps) =>
  React.createElement(Header, {
    ...nodeProps,
    props: { ...nodeProps.props, _level: 3 },
  } as NodeComponentProps);

const registry: Record<string, ComponentType<NodeComponentProps>> = {
  // Text elements
  title: Title,
  header: Header,
  subheader: Subheader,
  markdown: Markdown,
  text: Text,
  code: Code,
  caption: Caption,
  latex: Latex,
  html: Html,
  badge: Badge,

  // Input widgets
  button: Button,
  slider: Slider,
  text_input: TextInput,
  text_area: TextArea,
  checkbox: Checkbox,
  selectbox: Selectbox,
  radio: Radio,
  number_input: NumberInput,
  multiselect: Multiselect,
  date_input: DateInput,
  time_input: TimeInput,
  toggle: Toggle,
  color_picker: ColorPicker,
  link_button: LinkButton,
  download_button: DownloadButton,
  page_link: PageLink,
  select_slider: SelectSlider,
  file_uploader: FileUploader,
  feedback: Feedback,
  pills: Pills,
  segmented_control: SegmentedControl,
  camera_input: CameraInput,
  audio_input: AudioInput,

  // Chat elements
  chat_message: ChatMessage,
  chat_input: ChatInput,

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
  bokeh_chart: BokehChart,
  pydeck_chart: PydeckChart,

  // Media elements
  image: Image,
  audio: Audio,
  video: Video,
  logo: Logo,
  pdf: Pdf,

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
  page_config: PageConfig,
  sidebar_state: NullComponent,
  fragment: Fragment,

  // Status elements
  alert: Alert,
  exception: Exception,
  progress: Progress,
  spinner: Spinner,
  status: Status,
  toast: Toast,
  balloons: Balloons,
  snow: Snow,
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

export async function prefetchLikelyChunks(nodeTypes: Iterable<string>): Promise<void> {
  const unique = new Set(nodeTypes);
  const tasks: Promise<unknown>[] = [];
  for (const t of unique) {
    const loader = chunkPrefetchers[t];
    if (loader) tasks.push(loader());
  }
  if (tasks.length > 0) {
    await Promise.allSettled(tasks);
  }
}

export function prefetchDefaultChunks(): Promise<void> {
  return Promise.allSettled([
    loadFileUploader(),
    loadDataEditor(),
    loadPdf(),
    loadDialog(),
    loadStatus(),
  ]).then(() => undefined);
}
