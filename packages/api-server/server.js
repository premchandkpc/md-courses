#!/usr/bin/env node
/**
 * Engineering Knowledge Universe — Local HTTP Server
 *
 * Usage:
 *   node server.js              # serves content/ on http://localhost:3000
 *   node server.js 8080         # custom port
 *   node server.js --help       # help
 *
 * Zero external dependencies — uses only Node.js built-ins.
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = parseInt(process.argv[2], 10) || 3000;
const ROOT = path.resolve(__dirname, '../..');
const DATA_DIR = path.join(ROOT, 'content');
const HTML_FILE = path.join(ROOT, 'packages/legacy-viewer/read.html');

// ── File cache — built once at startup, invalidated every 5 minutes ──
let fileCache = null;
let fileCacheTime = 0;
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

function getCachedFileMap() {
  const now = Date.now();
  if (fileCache && (now - fileCacheTime) < CACHE_TTL) return fileCache;
  fileCache = getFileMap(DATA_DIR);
  fileCacheTime = now;
  return fileCache;
}

function invalidateCache() {
  fileCache = null;
  fileCacheTime = 0;
}

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.js':   'application/javascript; charset=utf-8',
  '.md':   'text/markdown; charset=utf-8',
  '.json': 'application/json',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif':  'image/gif',
  '.svg':  'image/svg+xml',
  '.ico':  'image/x-icon',
  '.txt':  'text/plain; charset=utf-8',
  '.yaml': 'text/plain; charset=utf-8',
  '.yml':  'text/plain; charset=utf-8',
  '.toml': 'text/plain; charset=utf-8',
};

// ═══════════════════════════════════════════════════════════════
// DIRECTORY SCANNER
// ═══════════════════════════════════════════════════════════════

function scanDir(dirPath, relativePath = '') {
  const result = [];
  let entries;
  try {
    entries = fs.readdirSync(dirPath, { withFileTypes: true });
  } catch {
    return result;
  }

  entries.sort((a, b) => {
    if (a.isDirectory() !== b.isDirectory()) return a.isDirectory() ? -1 : 1;
    return a.name.localeCompare(b.name);
  });

  for (const entry of entries) {
    if (entry.name.startsWith('.') || entry.name === 'node_modules' || entry.name === 'server.js') continue;
    const fullPath = path.join(dirPath, entry.name);
    const relPath = relativePath ? `${relativePath}/${entry.name}` : entry.name;

    if (entry.isDirectory()) {
      const children = scanDir(fullPath, relPath);
      result.push({
        name: entry.name,
        path: relPath,
        type: 'dir',
        children,
        open: true,
      });
    } else if (
      entry.name.endsWith('.md') ||
      entry.name.endsWith('.html') ||
      entry.name.endsWith('.yaml') ||
      entry.name.endsWith('.yml') ||
      entry.name.endsWith('.json')
    ) {
      try {
        const stat = fs.statSync(fullPath);
        result.push({
          name: entry.name,
          path: relPath,
          type: 'file',
          size: stat.size,
        });
      } catch { /* skip */ }
    }
  }

  return result;
}

function getFileMap(dirPath, basePath = '') {
  const map = {};
  function walk(d, p) {
    let entries;
    try { entries = fs.readdirSync(d, { withFileTypes: true }); } catch { return; }
    for (const entry of entries) {
      if (entry.name.startsWith('.') || entry.name === 'node_modules') continue;
      const full = path.join(d, entry.name);
      const rel = p ? `${p}/${entry.name}` : entry.name;
      if (entry.isDirectory()) {
        walk(full, rel);
      } else if (entry.name.endsWith('.md') || entry.name.endsWith('.html')) {
        try {
          const content = fs.readFileSync(full, 'utf-8');
          const stat = fs.statSync(full);
          map[rel] = { content, size: stat.size, lastModified: stat.mtimeMs };
        } catch { /* skip */ }
      }
    }
  }
  walk(dirPath, basePath);
  return map;
}

// ═══════════════════════════════════════════════════════════════
// ROUTING
// ═══════════════════════════════════════════════════════════════

function serveFile(res, filePath, contentType) {
  try {
    const content = fs.readFileSync(filePath);
    res.writeHead(200, {
      'Content-Type': contentType,
      'Content-Length': content.length,
      'Cache-Control': 'no-cache',
      'Access-Control-Allow-Origin': '*',
    });
    res.end(content);
  } catch {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'File not found' }));
  }
}

function serveJson(res, data, statusCode = 200) {
  const json = JSON.stringify(data);
  res.writeHead(statusCode, {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(json),
    'Access-Control-Allow-Origin': '*',
    'Cache-Control': 'no-cache',
  });
  res.end(json);
}

function serveApi(res, url, method) {
  const parsed = new URL(url, 'http://localhost');
  const pathname = parsed.pathname;

  // GET /api/tree — full directory tree
  if (pathname === '/api/tree' && method === 'GET') {
    const tree = scanDir(DATA_DIR);
    return serveJson(res, { tree });
  }

  // GET /api/health — health check
  if (pathname === '/api/health' && method === 'GET') {
    return serveJson(res, {
      status: 'ok',
      uptime: process.uptime(),
      cacheAge: fileCache ? Math.floor((Date.now() - fileCacheTime) / 1000) + 's' : 'cold',
      port: PORT,
    });
  }

  // GET /api/files — flat list of all files with metadata
  if (pathname === '/api/files' && method === 'GET') {
    const map = getCachedFileMap();
    const list = Object.entries(map).map(([path, data]) => ({
      path,
      name: path.split('/').pop().replace(/\.md$/, ''),
      dir: path.includes('/') ? path.substring(0, path.lastIndexOf('/')) : '',
      size: data.size,
    }));
    list.sort((a, b) => a.path.localeCompare(b.path));
    return serveJson(res, { files: list, total: list.length });
  }

  // GET /api/file?path=... — file content
  if (pathname === '/api/file' && method === 'GET') {
    const filePath = parsed.searchParams.get('path');
    if (!filePath) return serveJson(res, { error: 'Missing path parameter' }, 400);

    const fullPath = path.resolve(DATA_DIR, filePath);
    // Security: ensure path is within DATA_DIR
    if (!fullPath.startsWith(DATA_DIR)) {
      return serveJson(res, { error: 'Invalid path' }, 403);
    }

    try {
      const content = fs.readFileSync(fullPath, 'utf-8');
      const stat = fs.statSync(fullPath);
      return serveJson(res, {
        path: filePath,
        content,
        size: stat.size,
        lastModified: stat.mtimeMs,
      });
    } catch {
      return serveJson(res, { error: 'File not found' }, 404);
    }
  }

  // GET /api/search?q=... — search files
  if (pathname === '/api/search' && method === 'GET') {
    const query = parsed.searchParams.get('q')?.toLowerCase() || '';
    if (!query) return serveJson(res, { results: [] });

    const map = getCachedFileMap();
    const results = [];

    for (const [filePath, data] of Object.entries(map)) {
      const name = filePath.split('/').pop().replace(/\.md$/, '');
      const nameMatch = name.toLowerCase().includes(query);
      const matches = [];

      if (data.content) {
        const lines = data.content.split('\n');
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].toLowerCase().includes(query)) {
            matches.push({ line: i + 1, text: lines[i].trim().substring(0, 150) });
            if (matches.length >= 5) break;
          }
        }
      }

      if (nameMatch || matches.length > 0) {
        results.push({ path: filePath, name, matches, nameMatch });
      }

      if (results.length >= 50) break;
    }

    return serveJson(res, { results, query, count: results.length });
  }

  // GET /api/graph — knowledge graph (nodes + edges)
  if (pathname === '/api/graph' && method === 'GET') {
    const map = getCachedFileMap();
    const nodes = [];
    const edges = [];
    const nodeSet = new Set();
    const dirSet = new Set();

    for (const [filePath] of Object.entries(map)) {
      const parts = filePath.split('/');
      const name = parts.pop().replace(/\.(md|html)$/, '');
      const dir = parts.join('/');
      const id = filePath.replace(/\.(md|html)$/, '');

      if (!nodeSet.has(id)) {
        nodeSet.add(id);
        nodes.push({
          id,
          name,
          path: filePath,
          dir,
          type: parts.length > 0 ? 'file' : 'root',
          group: dir.split('/')[0] || 'root',
        });
      }

      // Edge: parent directory → file
      if (dir && !dirSet.has(dir)) {
        dirSet.add(dir);
        nodeSet.add(dir);
        nodes.push({
          id: dir,
          name: dir.split('/').pop(),
          path: dir,
          type: 'dir',
          group: dir.split('/')[0] || 'root',
        });
      }
      if (dir && nodeSet.has(dir)) {
        edges.push({ source: dir, target: id, label: 'contains' });
      }
    }

    // Cross-reference edges from CONNECTION_MAP.md
    const cmapPath = 'CONNECTION_MAP.md';
    const cmap = map[cmapPath];
    if (cmap) {
      const linkRe = /\[([^\]]+)\]\(([^)]+)\)/g;
      let m;
      while ((m = linkRe.exec(cmap.content)) !== null) {
        const target = m[2].replace(/\.(md|html)$/, '').replace(/^\//, '');
        for (const node of nodes) {
          if (node.id === target || node.id.endsWith('/' + target)) {
            edges.push({ source: cmapPath.replace(/\.md$/, ''), target: node.id, label: 'cross-ref' });
            break;
          }
        }
      }
    }

    return serveJson(res, { nodes, edges, nodeCount: nodes.length, edgeCount: edges.length });
  }

  // GET /api/stats — aggregate stats
  if (pathname === '/api/stats' && method === 'GET') {
    const map = getCachedFileMap();
    let totalLines = 0;
    let totalBytes = 0;
    let mdCount = 0;
    const dirs = new Set();

    for (const [filePath, data] of Object.entries(map)) {
      if (filePath.endsWith('.md')) mdCount++;
      totalBytes += data.size || 0;
      totalLines += (data.content?.match(/\n/g) || []).length + 1;
      const dir = filePath.includes('/') ? filePath.substring(0, filePath.lastIndexOf('/')) : '/';
      dirs.add(dir);
    }

    const tree = scanDir(DATA_DIR);
    const dirCount = countDirs(tree);

    return serveJson(res, {
      files: Object.keys(map).length,
      mdFiles: mdCount,
      totalLines,
      totalBytes,
      directories: dirCount,
      sizeHuman: formatBytes(totalBytes),
    });
  }

  // 404 for unknown API routes
  serveJson(res, { error: 'Not found' }, 404);
}

function countDirs(nodes) {
  let count = 0;
  for (const n of nodes) {
    if (n.type === 'dir') {
      count++;
      count += countDirs(n.children || []);
    }
  }
  return count;
}

function formatBytes(bytes) {
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  let size = bytes;
  while (size >= 1024 && i < units.length - 1) { size /= 1024; i++; }
  return `${size.toFixed(1)} ${units[i]}`;
}

// ═══════════════════════════════════════════════════════════════
// HTTP SERVER
// ═══════════════════════════════════════════════════════════════

const server = http.createServer((req, res) => {
  const { url, method } = req;
  const parsed = new URL(url, 'http://localhost');
  const pathname = parsed.pathname;

  // CORS headers for all responses
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (method === 'OPTIONS') {
    res.writeHead(204);
    return res.end();
  }

  // API routes
  if (pathname.startsWith('/api/')) {
    return serveApi(res, url, method);
  }

  // Serve read.html for root
  if (pathname === '/' || pathname === '/index.html') {
    return serveFile(res, HTML_FILE, 'text/html; charset=utf-8');
  }

  // Serve static files (resolved from project root)
  const filePath = path.resolve(ROOT, pathname.startsWith('/') ? '.' + pathname : pathname);

  // Security check: must stay within project root and not access dotfiles
  if (!filePath.startsWith(ROOT) || pathname.split('/').some(p => p.startsWith('.'))) {
    res.writeHead(403);
    return res.end('Forbidden');
  }

  try {
    if (fs.statSync(filePath).isDirectory()) {
      // Directory — look for read.html or index
      const dirHtml = path.join(filePath, 'read.html');
      const indexHtml = path.join(filePath, 'index.html');
      if (fs.existsSync(dirHtml)) return serveFile(res, dirHtml, 'text/html; charset=utf-8');
      if (fs.existsSync(indexHtml)) return serveFile(res, indexHtml, 'text/html; charset=utf-8');
      // Directory listing — redirect to API
      return serveJson(res, { path: pathname, type: 'directory' });
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';
    serveFile(res, filePath, contentType);
  } catch {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not found' }));
  }
});

// ═══════════════════════════════════════════════════════════════
// START
// ═══════════════════════════════════════════════════════════════

server.listen(PORT, '0.0.0.0', () => {
  const tree = scanDir(DATA_DIR);
  const mdCount = countMds(tree);

  console.log(`
╔══════════════════════════════════════════════╗
║  📚 Engineering Knowledge Universe          ║
║──────────────────────────────────────────────║
║  Local:  http://localhost:${String(PORT).padEnd(5)}               ║
║  Files:  ${String(mdCount).padEnd(4)} markdown documents          ║
║                                            ║
║  API endpoints:                            ║
║  ├─ /api/tree    — directory tree          ║
║  ├─ /api/files   — flat file list          ║
║  ├─ /api/file    — file content            ║
║  ├─ /api/search  — full-text search        ║
║  ├─ /api/graph   — knowledge graph         ║
║  ├─ /api/stats   — aggregate statistics    ║
║  └─ /api/health  — health check            ║
╚══════════════════════════════════════════════╝
`);
});

function countMds(nodes) {
  let count = 0;
  for (const n of nodes) {
    if (n.type === 'file' && n.name.endsWith('.md')) count++;
    if (n.children) count += countMds(n.children);
  }
  return count;
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\nShutting down...');
  server.close(() => process.exit(0));
});
process.on('SIGTERM', () => {
  server.close(() => process.exit(0));
});
