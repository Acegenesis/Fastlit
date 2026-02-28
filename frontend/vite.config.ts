import fs from "fs";
import { defineConfig, normalizePath, type PluginOption } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

const backendTarget =
  process.env.FASTLIT_DEV_BACKEND_URL || "http://127.0.0.1:8501";
const pythonWatchDirs = (process.env.FASTLIT_DEV_WATCH_DIRS || "")
  .split(path.delimiter)
  .map((dir) => dir.trim())
  .filter(Boolean)
  .map((dir) => normalizePath(path.resolve(dir)))
  .filter((dir) => fs.existsSync(dir));

function fastlitPythonReloadPlugin(): PluginOption {
  return {
    name: "fastlit-python-full-reload",
    apply: "serve",
    configureServer(server) {
      if (pythonWatchDirs.length === 0) {
        return;
      }

      server.watcher.add(pythonWatchDirs);

      let reloadTimer: ReturnType<typeof setTimeout> | null = null;
      let changedFile = "";

      const scheduleReload = (file: string) => {
        const normalizedFile = normalizePath(path.resolve(file));
        if (!normalizedFile.endsWith(".py")) {
          return;
        }
        const matchesWatchedDir = pythonWatchDirs.some(
          (dir) => normalizedFile === dir || normalizedFile.startsWith(`${dir}/`)
        );
        if (!matchesWatchedDir) {
          return;
        }

        changedFile = normalizedFile;
        if (reloadTimer) {
          clearTimeout(reloadTimer);
        }
        reloadTimer = setTimeout(() => {
          reloadTimer = null;
          server.config.logger.info(
            `fastlit python reload ${path.relative(server.config.root, changedFile)}`,
            { clear: true, timestamp: true }
          );
          server.ws.send({ type: "full-reload", path: "*" });
        }, 400);
      };

      server.watcher.on("change", scheduleReload);
      server.watcher.on("add", scheduleReload);
      server.watcher.on("unlink", scheduleReload);
    },
  };
}

export default defineConfig({
  plugins: [react(), fastlitPythonReloadPlugin()],
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
