import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import yaml from '@rollup/plugin-yaml';
import path from 'path';
import fs from 'fs';

// Resolve the active theme at build time from template.yaml so the theme SCSS
// can be a *static* import (extracted into a <link> in <head>) instead of a
// runtime dynamic import. We only need the `theme:` line, so a tiny regex read
// avoids pulling in a YAML parser at config time.
const templateYaml = fs.readFileSync(
  path.resolve(__dirname, 'template.yaml'),
  'utf-8'
);
const themeMatch = templateYaml.match(/^\s*theme:\s*['"]?([\w-]+)['"]?/m);
const activeTheme =
  themeMatch && themeMatch[1] === 'dark' ? 'dark-theme.scss' : 'theme.scss';

// https://vite.dev/config/
export default defineConfig({
  base: './',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@active-theme': path.resolve(__dirname, 'src/scss', activeTheme),
    },
  },
  plugins: [react(), yaml()],
  ssgOptions: {
    entry: 'src/pages/index.jsx',
    script: 'async',
  },
  build: {
    outDir: 'build',
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html'),
      },
    },
    target: 'es2015',
  },
  server: {
    host: '0.0.0.0',
    port: 8080,
  },
  css: {
    preprocessorOptions: {
      scss: {
        silenceDeprecations: ['import'],
        quietDeps: true,
      },
    },
  },
});
