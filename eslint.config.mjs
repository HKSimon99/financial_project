// eslint.config.mjs
import js from "@eslint/js";

export default [
  js.configs.recommended,

  // default rules for app js/ts files
  {
    files: ["**/*.{js,jsx,ts,tsx}"],
    languageOptions: { sourceType: "module" },
    rules: {},
  },

  // service worker override
  {
    files: ["apps/web/public/sw.js"], // adjust path if different
    languageOptions: {
      // most SW files are scripts, not modules
      sourceType: "script",
      globals: {
        self: "readonly",
        clients: "readonly",
        caches: "readonly",
        fetch: "readonly",
      },
    },
    // optional: keep "no-undef" on since we declared globals above
    // rules: { "no-undef": "off" },
  },
];
