import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react-swc";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const backendTarget = env.VITE_BACKEND_URL ?? "http://127.0.0.1:8089";

  return {
    plugins: [react()],
    server: {
      port: 5171,
      host: "0.0.0.0",
      proxy: {
        "/chatkit": {
          target: backendTarget,
          changeOrigin: true,
        },
        "/api": {
          target: backendTarget,
          changeOrigin: true,
        },
      },
      allowedHosts: [
        ".ngrok.io",
        ".trycloudflare.com",
      ],
    },
  };
});
