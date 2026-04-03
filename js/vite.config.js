import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
      entry: "src/index.jsx",
      name: "PitLaneAIPanel",
      fileName: "index",
      formats: ["umd"],
    },
    rollupOptions: {
      // FiftyOne provides React — don't bundle it
      external: ["react", "react-dom", "@fiftyone/plugins", "@fiftyone/components"],
      output: {
        globals: {
          react: "React",
          "react-dom": "ReactDOM",
          "@fiftyone/plugins": "fiftyone.plugins",
          "@fiftyone/components": "fiftyone.components",
        },
      },
    },
    outDir: "dist",
    emptyOutDir: true,
  },
});
