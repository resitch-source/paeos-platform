import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// PAEOS-FX frontend dev/build config. The API base is injected via
// VITE_API_BASE so the shell can target local or containerized backends.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_API_BASE ?? "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
