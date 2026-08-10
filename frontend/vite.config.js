import path from "node:path";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    // Absolute imports: `@/shared/ui/Button` instead of `../../../shared/ui/Button`.
    alias: { "@": path.resolve(import.meta.dirname, "src") },
  },
  server: {
    port: 5173,
    // Proxying keeps the browser on one origin in dev, so the session cookie
    // is same-origin and CORS never enters the picture — the same shape as
    // production, where nginx does the proxying.
    proxy: {
      "/api": {
        target: process.env.VITE_API_TARGET || "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
