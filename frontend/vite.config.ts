import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    outDir: path.resolve(__dirname, "../fastlit/server/static"),
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) return;

          if (
            id.includes("plotly.js") ||
            id.includes("react-plotly.js") ||
            id.includes("recharts") ||
            id.includes("vega") ||
            id.includes("vega-lite") ||
            id.includes("vega-embed")
          ) {
            return "vendor-charts";
          }

          if (id.includes("leaflet") || id.includes("react-leaflet")) {
            return "vendor-maps";
          }

          if (id.includes("@duckdb") || id.includes("duckdb-wasm")) {
            return "vendor-duckdb";
          }

          if (id.includes("@hpcc-js/wasm")) {
            return "vendor-graphviz";
          }

          if (id.includes("react") || id.includes("scheduler")) {
            return "vendor-react";
          }

          if (id.includes("@radix-ui") || id.includes("lucide-react")) {
            return "vendor-ui";
          }

          if (id.includes("katex") || id.includes("dompurify")) {
            return "vendor-markdown";
          }
        },
      },
    },
  },
  server: {
    proxy: {
      "/ws": {
        target: "ws://localhost:8501",
        ws: true,
      },
    },
  },
});
