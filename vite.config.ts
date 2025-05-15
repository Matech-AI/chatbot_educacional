import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { nodePolyfills } from 'vite-plugin-node-polyfills';

export default defineConfig({
  plugins: [
    react(),
    nodePolyfills({
      globals: {
        process: true,
        Buffer: true
      },
      protocolImports: true,
      console: true
    })
  ],
  optimizeDeps: {
    exclude: ['lucide-react']
  },
  define: {
    'process.env.NODE_DEBUG': 'false',
    'process.platform': JSON.stringify('browser'),
    'process.version': JSON.stringify('v16.0.0'),
    'process.env.READABLE_STREAM': 'false'
  }
});