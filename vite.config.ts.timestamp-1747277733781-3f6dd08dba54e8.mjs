// vite.config.ts
import { defineConfig } from "file:///home/project/node_modules/vite/dist/node/index.js";
import react from "file:///home/project/node_modules/@vitejs/plugin-react/dist/index.mjs";
import { nodePolyfills } from "file:///home/project/node_modules/vite-plugin-node-polyfills/dist/index.js";
var vite_config_default = defineConfig({
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
    exclude: ["lucide-react"]
  },
  define: {
    "process.env.NODE_DEBUG": "false",
    "process.platform": JSON.stringify("browser"),
    "process.version": JSON.stringify("v16.0.0"),
    "process.env.READABLE_STREAM": "false"
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCIvaG9tZS9wcm9qZWN0XCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCIvaG9tZS9wcm9qZWN0L3ZpdGUuY29uZmlnLnRzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9ob21lL3Byb2plY3Qvdml0ZS5jb25maWcudHNcIjtpbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tICd2aXRlJztcbmltcG9ydCByZWFjdCBmcm9tICdAdml0ZWpzL3BsdWdpbi1yZWFjdCc7XG5pbXBvcnQgeyBub2RlUG9seWZpbGxzIH0gZnJvbSAndml0ZS1wbHVnaW4tbm9kZS1wb2x5ZmlsbHMnO1xuXG5leHBvcnQgZGVmYXVsdCBkZWZpbmVDb25maWcoe1xuICBwbHVnaW5zOiBbXG4gICAgcmVhY3QoKSxcbiAgICBub2RlUG9seWZpbGxzKHtcbiAgICAgIGdsb2JhbHM6IHtcbiAgICAgICAgcHJvY2VzczogdHJ1ZSxcbiAgICAgICAgQnVmZmVyOiB0cnVlXG4gICAgICB9LFxuICAgICAgcHJvdG9jb2xJbXBvcnRzOiB0cnVlLFxuICAgICAgY29uc29sZTogdHJ1ZVxuICAgIH0pXG4gIF0sXG4gIG9wdGltaXplRGVwczoge1xuICAgIGV4Y2x1ZGU6IFsnbHVjaWRlLXJlYWN0J11cbiAgfSxcbiAgZGVmaW5lOiB7XG4gICAgJ3Byb2Nlc3MuZW52Lk5PREVfREVCVUcnOiAnZmFsc2UnLFxuICAgICdwcm9jZXNzLnBsYXRmb3JtJzogSlNPTi5zdHJpbmdpZnkoJ2Jyb3dzZXInKSxcbiAgICAncHJvY2Vzcy52ZXJzaW9uJzogSlNPTi5zdHJpbmdpZnkoJ3YxNi4wLjAnKSxcbiAgICAncHJvY2Vzcy5lbnYuUkVBREFCTEVfU1RSRUFNJzogJ2ZhbHNlJ1xuICB9XG59KTsiXSwKICAibWFwcGluZ3MiOiAiO0FBQXlOLFNBQVMsb0JBQW9CO0FBQ3RQLE9BQU8sV0FBVztBQUNsQixTQUFTLHFCQUFxQjtBQUU5QixJQUFPLHNCQUFRLGFBQWE7QUFBQSxFQUMxQixTQUFTO0FBQUEsSUFDUCxNQUFNO0FBQUEsSUFDTixjQUFjO0FBQUEsTUFDWixTQUFTO0FBQUEsUUFDUCxTQUFTO0FBQUEsUUFDVCxRQUFRO0FBQUEsTUFDVjtBQUFBLE1BQ0EsaUJBQWlCO0FBQUEsTUFDakIsU0FBUztBQUFBLElBQ1gsQ0FBQztBQUFBLEVBQ0g7QUFBQSxFQUNBLGNBQWM7QUFBQSxJQUNaLFNBQVMsQ0FBQyxjQUFjO0FBQUEsRUFDMUI7QUFBQSxFQUNBLFFBQVE7QUFBQSxJQUNOLDBCQUEwQjtBQUFBLElBQzFCLG9CQUFvQixLQUFLLFVBQVUsU0FBUztBQUFBLElBQzVDLG1CQUFtQixLQUFLLFVBQVUsU0FBUztBQUFBLElBQzNDLCtCQUErQjtBQUFBLEVBQ2pDO0FBQ0YsQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K
