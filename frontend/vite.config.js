import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import {
  transformManagementPosDefaultsPage,
  transformManagementPosPage,
} from './scripts/pos-print-transform.mjs'
import {
  transformPosProductPanel,
  transformPosReliabilityPage,
} from './scripts/pos-reliability-transform.mjs'
import {
  transformPosBackgroundPage,
  transformPosProductPanelAvailability,
} from './scripts/pos-background-transform.mjs'
import { transformManagementProductsPage } from './scripts/management-products-reliability-transform.mjs'

function posThermalPrintTransform() {
  return {
    name: 'restaurant-pos-thermal-print-transform',
    enforce: 'pre',
    transform(code, id) {
      const rawId = String(id || '')

      // Vue invokes Vite transforms again for virtual submodules such as
      // `Component.vue?vue&type=style...`. These transforms operate on the
      // whole SFC source and must never run against extracted CSS/JS blocks.
      if (rawId.includes('?')) return null

      const cleanId = rawId.replace(/\\/g, '/')
      if (cleanId.endsWith('/src/pages/management/ManagementPosPage.vue')) {
        return {
          code: transformPosBackgroundPage(
            transformPosReliabilityPage(transformManagementPosPage(code)),
          ),
          map: null,
        }
      }
      if (cleanId.endsWith('/src/pages/management/ManagementPosDefaultsPage.vue')) {
        return { code: transformManagementPosDefaultsPage(code), map: null }
      }
      if (cleanId.endsWith('/src/pages/management/ManagementProductsPage.vue')) {
        return { code: transformManagementProductsPage(code), map: null }
      }
      if (cleanId.endsWith('/src/components/management/pos/PosProductPanel.vue')) {
        return {
          code: transformPosProductPanelAvailability(transformPosProductPanel(code)),
          map: null,
        }
      }
      return null
    },
  }
}

export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/assets/restaurant/frontend/' : '/',
  plugins: [posThermalPrintTransform(), vue()],
  server: {
    host: '0.0.0.0',
    port: 5000,
    allowedHosts: true,
    proxy: {
      '^/(api|assets|files)': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  build: {
    outDir: '../restaurant/public/frontend',
    emptyOutDir: true,
    sourcemap: false,
    rollupOptions: {
      output: {
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name].[ext]',
        inlineDynamicImports: true,
      },
    },
  },
}))
