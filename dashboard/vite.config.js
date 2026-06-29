import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { createReadStream, existsSync, statSync } from 'node:fs';
import { join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('.', import.meta.url));

// Serve the (optional, git-ignored) ../coursera video library in dev without a
// symlink in public/. Supports HTTP range requests so video seeking works.
function serveCoursera() {
  const base = normalize(join(root, '..', 'coursera'));
  const MIME = { '.mp4': 'video/mp4', '.vtt': 'text/vtt', '.webm': 'video/webm', '.m4v': 'video/mp4' };
  return {
    name: 'serve-coursera',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = (req.url || '').split('?')[0];
        if (!url.startsWith('/coursera/')) return next();
        const fp = normalize(join(base, decodeURIComponent(url.slice('/coursera/'.length))));
        if (!fp.startsWith(base) || !existsSync(fp) || statSync(fp).isDirectory()) {
          res.statusCode = 404; return res.end('Not found');
        }
        const size = statSync(fp).size;
        const ext = fp.slice(fp.lastIndexOf('.')).toLowerCase();
        const type = MIME[ext] || 'application/octet-stream';
        const range = req.headers.range;
        if (range) {
          const m = /bytes=(\d*)-(\d*)/.exec(range) || [];
          const start = m[1] ? parseInt(m[1], 10) : 0;
          const end = m[2] ? parseInt(m[2], 10) : size - 1;
          if (start >= size) { res.statusCode = 416; return res.end(); }
          res.writeHead(206, {
            'Content-Range': `bytes ${start}-${end}/${size}`,
            'Accept-Ranges': 'bytes',
            'Content-Length': end - start + 1,
            'Content-Type': type,
          });
          createReadStream(fp, { start, end }).pipe(res);
        } else {
          res.writeHead(200, { 'Content-Length': size, 'Content-Type': type, 'Accept-Ranges': 'bytes' });
          createReadStream(fp).pipe(res);
        }
      });
    },
  };
}

export default defineConfig(({ command }) => ({
  // "/" for the dev server; the GitHub Pages project subpath for the build.
  base: command === 'build' ? '/Modern-Robotics/' : '/',
  plugins: [svelte(), serveCoursera()],
  worker: { format: 'es' },
  optimizeDeps: { exclude: ['pdfjs-dist'] },
  // book PDFs + compressed slides live in public/ and are committed; the large
  // video library is served by the plugin above only when present locally.
  build: { copyPublicDir: true },
}));
