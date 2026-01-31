import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: path.resolve(__dirname, "../fastlit/server/static"),
    emptyOutDir: true,
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
