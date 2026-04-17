import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  // shadcn-generated UI primitives are vendor-style files we don't lint.
  globalIgnores(['dist', 'src/components/ui/**']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    rules: {
      // shadcn theme provider exports both the component and the useTheme hook.
      'react-refresh/only-export-components': 'off',
      // Form editors mirror server-fetched data into local state on load — the
      // intentional pattern this rule warns about. Refactoring all of them to
      // derived render-time state would obscure the editor flow.
      'react-hooks/set-state-in-effect': 'off',
    },
  },
  {
    // Tests use `any` for msw handler bodies and other loose mocks.
    files: ['tests/**/*.{ts,tsx}'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
])
