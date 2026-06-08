---
title: API Documentation — Knowledge Universe Server
time: 30m
---

# API Documentation — Knowledge Universe Server

**Base URL:** `http://localhost:3000/api`

All responses are JSON. No authentication required.

---

## Tree

**GET** `/api/tree`

Full directory tree structure.

**Response:**
```json
{
  "tree": [
    {
      "name": "01-ai-ml",
      "path": "01-ai-ml",
      "type": "dir",
      "children": [...],
      "open": true
    },
    ...
  ]
}
```

---

## Files

**GET** `/api/files`

Flat list of all markdown/HTML files with metadata.

**Response:**
```json
{
  "files": [
    {
      "path": "01-ai-ml/fundamentals/01-neural-networks.md",
      "name": "01-neural-networks",
      "dir": "01-ai-ml/fundamentals",
      "size": 45230
    },
    ...
  ],
  "total": 342
}
```

---

## File Content

**GET** `/api/file?path=<file-path>`

Retrieve single file content.

**Query Params:**
- `path` (required): File path relative to data/ (e.g., `01-ai-ml/fundamentals/01-neural-networks.md`)

**Response:**
```json
{
  "path": "01-ai-ml/fundamentals/01-neural-networks.md",
  "content": "# Neural Networks\n\n...",
  "size": 45230,
  "lastModified": 1716900000000
}
```

**Errors:**
- `400 Bad Request` — missing path param
- `403 Forbidden` — path traversal attempt (contains `..`)
- `404 Not Found` — file doesn't exist

---

## Search

**GET** `/api/search?q=<query>`

Full-text search across all files.

**Query Params:**
- `q` (required): Search term (case-insensitive)

**Response:**
```json
{
  "query": "backpropagation",
  "results": [
    {
      "path": "01-ai-ml/fundamentals/01-neural-networks.md",
      "name": "01-neural-networks",
      "nameMatch": false,
      "matches": [
        {
          "line": 45,
          "text": "Backpropagation is the algorithm for training..."
        },
        ...
      ]
    },
    ...
  ],
  "count": 12
}
```

**Limits:**
- Returns max 5 matches per file
- Returns max 50 files total
- Empty query returns no results

---

## Statistics

**GET** `/api/stats`

Aggregate statistics about the knowledge base.

**Response:**
```json
{
  "files": 342,
  "mdFiles": 331,
  "htmlFiles": 11,
  "directories": 24,
  "totalBytes": 12584320,
  "totalLines": 587420,
  "avgFileSize": 36780,
  "topDomains": [
    { "name": "01-ai-ml", "fileCount": 45 },
    { "name": "15-system-design", "fileCount": 38 },
    ...
  ]
}
```

---

## Static Files

**GET** `/<relative-path>`

Serve static files (HTML, CSS, JS, MD, images).

**Supported:**
- `.html` — text/html
- `.css` — text/css
- `.js` — application/javascript
- `.md` — text/markdown
- `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.ico` — image types
- `.json` — application/json

---

## Server Setup

```bash
# Start on port 3000 (default)
node server.js

# Custom port
node server.js 8080

# Help
node server.js --help
```

**Features:**
- Zero external dependencies (Node.js built-ins only)
- CORS enabled (Access-Control-Allow-Origin: *)
- Security: path traversal protection on `/api/file`
- Cache: no-cache headers (disable browser caching)

---

## Usage in Frontend

See `read.html` for implementation examples. Key endpoints used:

```javascript
// Load directory tree
fetch('/api/tree').then(r => r.json())

// Get file content
fetch('/api/file?path=01-ai-ml/fundamentals/01-neural-networks.md')
  .then(r => r.json())

// Search
fetch('/api/search?q=backpropagation').then(r => r.json())
```

---

## Rate Limiting

None. No authentication. No rate limits. For production, add rate limiting middleware.

---

## Security Notes

✅ Path traversal protected (`..` blocked in `/api/file`)
✅ CORS enabled for cross-origin requests
⚠️ No auth — anyone can read all files
⚠️ No rate limiting — add for production
