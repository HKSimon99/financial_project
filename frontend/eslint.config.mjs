import js from '@eslint/js'
import { FlatCompat } from '@eslint/eslintrc'
import path from 'node:path'
import url from 'node:url'

// __dirname in ESM
const __dirname = path.dirname(url.fileURLToPath(import.meta.url))

// Tell FlatCompat where to resolve extends/plugins from
const compat = new FlatCompat({ baseDirectory: __dirname })

export default [
  // ignore build outputs
  { ignores: ['.next/**', 'node_modules/**', 'dist/**'] },

  // baseline JS rules
  js.configs.recommended,

  // bring in Next’s rules (your old ".eslintrc.json" was ["next/core-web-vitals", "prettier"])
  ...compat.config({
    extends: ['next/core-web-vitals', 'prettier', 'next/typescript'], // remove 'next/typescript' if JS-only
  }),
]
