import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Detectar o ambiente
  const isProduction = mode === 'production'
  const isHostinger = process.env.HOSTINGER === 'true'
  const isRender = process.env.RENDER === 'true'
  
  // Definir o target baseado no ambiente
  let apiTarget = 'http://localhost:8000'
  let ragApiTarget = 'http://localhost:8001'
  
  if (isHostinger) {
    apiTarget = 'http://31.97.16.142:8000'
    ragApiTarget = 'http://31.97.16.142:8001'
  } else if (isRender) {
    apiTarget = 'http://localhost:8000' // Render usa localhost interno
    ragApiTarget = 'http://localhost:8001'
  }
  // Em desenvolvimento local, mantém localhost

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      host: '0.0.0.0', // Aceita conexões IPv4 e IPv6
      port: 3000,
      proxy: {
        // Proxy API calls to backend
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
        // Proxy RAG API calls
        '/rag-api': {
          target: ragApiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/rag-api/, ''),
        }
      }
    }
  }
})