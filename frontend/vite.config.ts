import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies API + WebSocket to the backend (`uvicorn app:app` on
// :8000), matching the core's default API base of "/api". In production the
// backend serves the built bundle itself (see ../app.py), so no proxy is used.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/ws": { target: "http://localhost:8000", ws: true },
    },
  },
});
