import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy API requests to the backend
      "/v1": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true,
        secure: false,
      },
      "/api": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true,
        secure: false,
      },
      "/healthz": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true,
        secure: false,
      },
      "/health": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true,
        secure: false,
      },
      "/docs": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
