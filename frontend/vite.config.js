import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      // Lets the frontend call relative "/api/v1/..." paths in every
      // environment (dev server, Docker) without an env-specific base
      // URL. Also means the httpOnly refresh-token cookie set by the
      // backend is scoped to this same origin as far as the browser is
      // concerned, side-stepping cross-origin cookie complications
      // entirely during local development.
      //
      // Target is overridable via VITE_API_PROXY_TARGET because
      // "localhost" means something different inside a Docker container
      // (the container itself) than it does when running `npm run dev`
      // directly on the host - docker-compose.yml sets this to
      // "http://backend:8000" for the containerized dev workflow.
      "/api": {
        target: process.env.VITE_API_PROXY_TARGET || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
