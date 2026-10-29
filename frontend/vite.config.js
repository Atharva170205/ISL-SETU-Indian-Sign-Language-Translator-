import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

const CERT_DIR = path.resolve(__dirname, '../certs')

export default defineConfig({
  plugins: [react()],
  server: {
    https: {
      key: fs.readFileSync(path.join(CERT_DIR, '10.39.242.125+2-key.pem')),
      cert: fs.readFileSync(path.join(CERT_DIR, '10.39.242.125+2.pem')),
    },
    host: true,
  },
})