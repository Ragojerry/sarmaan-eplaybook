import { readFileSync } from "node:fs";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The browser tab title comes from the one brand file (src/brand/brand.json, copied
// from brand/brand.json by scripts/brand_sync.py).
const brand = JSON.parse(readFileSync(new URL("./src/brand/brand.json", import.meta.url), "utf8"));

export default defineConfig({
  plugins: [
    react(),
    {
      name: "brand-title",
      transformIndexHtml: (html) => html.replace(/%BRAND_TITLE%/g, brand.title),
    },
  ],
  server: {
    port: 5173,
  },
});
