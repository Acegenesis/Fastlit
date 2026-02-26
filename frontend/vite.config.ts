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
    // Skip preloading heavy lazy-loaded chunks so they don't compete with
    // critical resources (vendor-react, vendor-ui) on initial page load.
    modulePreload: {
      resolveDependencies(url, deps) {
        const HEAVY = [
          "vendor-graphviz",
          "vendor-plotly",
          "vendor-vega",
          "vendor-maps",
          "vendor-duckdb",
          "vendor-markdown",
        ];
        return deps.filter((dep) => !HEAVY.some((h) => dep.includes(h)));
      },
    },
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Keep Vite's dynamic import preload helper and lightweight class
          // merging utils in the base vendor chunk to avoid pulling heavy
          // optional chunks into the initial entry graph.
          if (id.includes("vite/preload-helper")) {
            return "vendor-react";
          }
          if (!id.includes("node_modules")) return;
          if (id.includes("clsx") || id.includes("tailwind-merge")) return "vendor-react";

          if (id.includes("plotly.js") || id.includes("react-plotly.js")) {
            return "vendor-plotly";
          }

          if (id.includes("vega") || id.includes("vega-lite") || id.includes("vega-embed")) {
            return "vendor-vega";
          }

          if (id.includes("recharts")) {
            return "vendor-recharts";
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

          if (id.includes("katex")) {
            return "vendor-katex";
          }

          if (id.includes("dompurify")) {
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
