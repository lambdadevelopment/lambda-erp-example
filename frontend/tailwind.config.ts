import type { Config } from "tailwindcss";
import erpPreset from "@lambda-development/erp-core/tailwind-preset";

// "Consumer scans source": our own Tailwind build generates the utility classes,
// scanning BOTH our source and the core library's built JS (where the shared
// components' class names live). The preset supplies the token-backed colours,
// shadows, and font so our components match the core's look.
export default {
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx}",
    "./node_modules/@lambda-development/erp-core/dist/**/*.js",
  ],
  presets: [erpPreset as Config],
} satisfies Config;
