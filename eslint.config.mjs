// eslint.config.mjs (repo root)
import js from "@eslint/js";
import tseslint from "typescript-eslint";
import eslintConfigPrettier from "eslint-config-prettier";

const APP_JS = ["apps/**/*.{js,jsx}", "packages/**/*.{js,jsx}"];
const APP_TS = ["apps/**/*.{ts,tsx}", "packages/**/*.{ts,tsx}"];
const NODE_SCRIPTS = ["scripts/**/*.{js,cjs,mjs,ts}"];
const NODE_CONFIGS = [
  "**/next.config.{js,mjs,ts}",
  "**/tailwind.config.{js,mjs,ts}",
  "**/postcss.config.{js,mjs,ts}",
  "**/vitest.config.{js,mjs,ts}",
];

// ❗️Ignore compiled junk & outputs
const IGNORES = [
  "node_modules/**",
  "dist/**",
  "build/**",
  // Compiled JS output for the TS scanner should never be linted in repo
  "scripts/scan_frontend_usage.js",
  "**/*.d.ts",
];

export default [
  { ignores: IGNORES },

  // JS/JSX (browser)
  js.configs.recommended,
  {
    files: APP_JS,
    languageOptions: {
      sourceType: "module",
      parserOptions: { ecmaVersion: "latest", ecmaFeatures: { jsx: true } },
    },
    rules: {},
  },

  // TS/TSX (browser) — apply TS rules ONLY to TS files
  ...tseslint.config({
    files: APP_TS,
    extends: [tseslint.configs.recommended],
    languageOptions: {
      sourceType: "module",
      parser: tseslint.parser,
      parserOptions: { ecmaVersion: "latest", ecmaFeatures: { jsx: true } },
    },
  }),

  // Node scripts (CJS/ESM): allow require, console, etc.
  {
    files: NODE_SCRIPTS,
    languageOptions: {
      sourceType: "script",
      globals: {
        require: "readonly",
        module: "readonly",
        __dirname: "readonly",
        __filename: "readonly",
        process: "readonly",
        console: "readonly",
      },
    },
    rules: {
      "no-console": "off",
      "@typescript-eslint/no-require-imports": "off",
      "@typescript-eslint/no-var-requires": "off",
      // Compiled/utility scripts often trip these; keep them off for scripts/*
      "@typescript-eslint/no-unused-expressions": "off",
      "no-fallthrough": "off",
    },
  },

  // Node configs
  {
    files: NODE_CONFIGS,
    languageOptions: {
      sourceType: "module",
      globals: {
        process: "readonly",
        require: "readonly",
        module: "readonly",
        __dirname: "readonly",
        console: "readonly",
      },
    },
  },

  // Service worker globals
  {
    files: ["apps/web/public/sw.js"],
    languageOptions: {
      sourceType: "script",
      globals: {
        self: "readonly",
        clients: "readonly",
        caches: "readonly",
        fetch: "readonly",
      },
    },
  },

  // Disable formatting rules to avoid conflicts with Prettier
  eslintConfigPrettier,
];
