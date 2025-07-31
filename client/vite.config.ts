// import path from "path";
// import tailwindcss from "@tailwindcss/vite";
// import { defineConfig } from "vite";
// import react from "@vitejs/plugin-react";

// // https://vite.dev/config/
// export default defineConfig({
//   plugins: [react(), tailwindcss()],
//   resolve: {
//     alias: {
//       "@": path.resolve(__dirname, "./src"),
//     },
//   },
//   preview: {
//     port: parseInt(process.env.PORT || "3000"),
//     strictPort: true,
//     host: true, // This allows external connections
//   },
//   server: {
//     port: parseInt(process.env.PORT || "5173"),
//     strictPort: true,
//     host: true,
//   },
//   build: {
//     outDir: "dist",
//     sourcemap: false,
//     rollupOptions: {
//       output: {
//         manualChunks: {
//           vendor: ["react", "react-dom"],
//           ui: ["lucide-react", "@radix-ui/react-slot"],
//         },
//       },
//     },
//   },
// });

import path from "path";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  preview: {
    port: parseInt(process.env.PORT || "3000"),
    strictPort: true,
    host: true, // This allows external connections
    allowedHosts: ["*", "travel-assist-ui-390383760878.europe-west2.run.app"],
  },
  server: {
    port: parseInt(process.env.PORT || "5173"),
    strictPort: true,
    host: true,
  },
  build: {
    outDir: "dist",
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom"],
          ui: ["lucide-react", "@radix-ui/react-slot"],
        },
      },
    },
  },
});
