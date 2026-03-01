import { createLogger, defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

const backendTarget =
  process.env.FASTLIT_DEV_BACKEND_URL || "http://127.0.0.1:8501";
const backendUrl = new URL(backendTarget);
const frontendTarget =
  process.env.FASTLIT_DEV_SERVER_URL || "http://127.0.0.1:5173";
const frontendUrl = new URL(frontendTarget);

function createFastlitDevLogger() {
  const logger = createLogger();
  const baseInfo = logger.info.bind(logger);
  const baseWarn = logger.warn.bind(logger);
  const baseError = logger.error.bind(logger);

  const shouldSuppress = (msg: string) =>
    msg.includes("Local:") ||
    msg.includes("Network:") ||
    msg.includes("press h + enter to show help") ||
    msg.includes("proxy error:") ||
    msg.includes("ECONNREFUSED");

  logger.info = (msg, options) => {
    if (shouldSuppress(msg)) {
      return;
    }
    baseInfo(msg, options);
  };

  logger.warn = (msg, options) => {
    if (shouldSuppress(msg)) {
      return;
    }
    baseWarn(msg, options);
  };

  logger.error = (msg, options) => {
    if (shouldSuppress(msg)) {
      return;
    }
    baseError(msg, options);
  };

  return logger;
}

export default defineConfig({
  customLogger: createFastlitDevLogger(),
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
    hmr: {
      host: frontendUrl.hostname,
      clientPort:
        Number(frontendUrl.port) || (frontendUrl.protocol === "https:" ? 443 : 80),
      path: "/_vite_hmr",
      protocol: frontendUrl.protocol === "https:" ? "wss" : "ws",
    },
    proxy: {
      "/ws": {
        target: backendTarget.replace(/^http/, "ws"),
        ws: true,
      },
      "/_fastlit": {
        target: backendTarget,
        changeOrigin: true,
      },
      "/_components": {
        target: backendTarget,
        changeOrigin: true,
      },
      "/auth": {
        target: backendTarget,
        changeOrigin: true,
      },
    },
  },
});
