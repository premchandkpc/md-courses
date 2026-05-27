# 10: SSR & Next.js — Deep Reference

> **Scope**: SSR, SSG, ISR, RSC, edge runtime, streaming SSR, PPR, server actions, middleware, routing, data fetching, caching

## 1. SSR Fundamentals

Server-Side Rendering converts React components to HTML on the server per request. Three phases:

```jsx
// 1. Server: fetch data → render to HTML → send to client
// 2. Client: show HTML immediately (no JS needed)
// 3. Hydration: React attaches event handlers to server DOM
import { hydrateRoot } from "react-dom/client";
hydrateRoot(document.getElementById("root"), <App />);
```

### SSR vs SSG vs ISR

| Strategy | When HTML is built | Data freshness | Use case |
|----------|-------------------|----------------|----------|
| SSR | Every request | Latest | Personalized dashboards |
| SSG | Build time | Stale | Marketing pages, blogs |
| ISR | Build time + revalidation interval | Near-latest | Product listings, docs |
| PPR (Partial Prerendering) | Build + request hybrid | Mixed | Landing + dynamic widgets |

## 2. React Server Components (RSC)

React 19 introduces a fundamental split: components run on the server OR the client, not both.

### Server vs Client Boundaries

```jsx
// ServerComponent.server.jsx — default in App Router
// Can: fetch data, access DB, read files, keep secrets
// Cannot: useState, useEffect, event handlers, browser APIs
async function ProfilePage({ userId }) {
  const user = await db.users.findUnique(userId);
  return <h1>{user.name}</h1>;
}

// ClientComponent.client.jsx — opt in with "use client"
"use client";
import { useState } from "react";

function LikeButton({ postId }) {
  const [liked, setLiked] = useState(false);
  return <button onClick={() => setLiked(!liked)}>♥</button>;
}
```

### RSC Streaming

Server components stream incrementally. Suspense boundaries let the page render before all data loads:

```jsx
import { Suspense } from "react";

async function Comments() {
  const comments = await fetchComments(); // slow
  return comments.map((c) => <div key={c.id}>{c.text}</div>);
}

export default function PostPage({ params }) {
  return (
    <article>
      <h1>{params.slug}</h1>
      <Suspense fallback={<Spinner />}>
        <Comments />
      </Suspense>
    </article>
  );
}
```

### Server Actions ("use server")

```jsx
// Form action — runs on server, no API route needed
async function updateProfile(formData) {
  "use server";
  const name = formData.get("name");
  await db.users.update({ name });
  revalidatePath("/profile");
}

function ProfileForm() {
  return (
    <form action={updateProfile}>
      <input name="name" />
      <button type="submit">Save</button>
    </form>
  );
}
```

## 3. Next.js App Router

### Route Groups & Conventions

| File | Purpose |
|------|---------|
| `page.jsx` | Route UI (must export default component) |
| `layout.jsx` | Shared wrapper (persists across navigations) |
| `loading.jsx` | Suspense fallback for segment |
| `error.jsx` | Error boundary (catches errors in children) |
| `not-found.jsx` | 404 page for segment |
| `template.jsx` | Like layout but re-mounts on navigation |
| `default.jsx` | Parallel route fallback |

```jsx
// app/layout.jsx — root layout (required)
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

// app/blog/[slug]/page.jsx
export default async function BlogPost({ params }) {
  const post = await getPost(params.slug);
  return <article>{post.content}</article>;
}
```

### Data Fetching

```jsx
// Default: cached and deduplicated
async function getPost(slug) {
  const res = await fetch(`https://api.example.com/posts/${slug}`);
  // fetch automatically cached (next: { revalidate: 3600 })
  return res.json();
}

// Revalidation options
fetch(url, { next: { revalidate: 3600 } });     // ISR — time-based
fetch(url, { next: { tags: ["posts"] } });       // Tag for on-demand
fetch(url, { cache: "no-store" });               // SSR — no cache

// On-demand revalidation
import { revalidateTag, revalidatePath } from "next/cache";
revalidateTag("posts");    // invalidate all fetches with tag "posts"
revalidatePath("/blog");   // revalidate specific path

// Dynamic functions opt out of caching
import { cookies, headers } from "next/headers";
const token = cookies().get("token");
const userAgent = headers().get("user-agent");
```

### Static Generation & Metadata

```jsx
// generateStaticParams — pre-build pages at build time
export async function generateStaticParams() {
  const posts = await getPostSlugs();
  return posts.map((slug) => ({ slug }));
}

// generateMetadata — dynamic meta tags
export async function generateMetadata({ params }) {
  const post = await getPost(params.slug);
  return {
    title: post.title,
    description: post.excerpt,
    openGraph: { images: [post.coverImage] },
  };
}
```

## 4. Rendering Strategies

```jsx
// Static (default) — fetch without dynamic functions or revalidate
export default function Page() {
  return <div>Static HTML at build time</div>;
}

// Dynamic — use cookies(), headers(), searchParams, or cache: "no-store"
export default async function Page({ searchParams }) {
  const data = await fetch(url, { cache: "no-store" });
  return <div>{data.now}</div>;
}

// ISR — revalidate in fetch or segment config
export const revalidate = 3600; // seconds

// Streaming — wrap slow sections in Suspense
// PPR — Partial Prerendering (Next.js 15+)
// Static shell + dynamic holes streamed in
```

### Edge Runtime

```jsx
// app/api/edge/route.js
export const runtime = "edge";

export async function GET(request) {
  const geo = request.geo; // geolocation data
  const ua = request.headers.get("user-agent");
  return new Response(`Hello from ${geo?.city || "unknown"}`);
}
```

Middleware runs on the Edge before every route request:

```jsx
// middleware.js
import { NextResponse } from "next/server";

export function middleware(request) {
  const country = request.geo?.country || "US";
  const url = request.nextUrl;

  // A/B testing
  if (url.pathname === "/") {
    const variant = Math.random() > 0.5 ? "a" : "b";
    url.searchParams.set("v", variant);
    return NextResponse.rewrite(url);
  }

  // Bot detection
  const ua = request.headers.get("user-agent") || "";
  if (ua.includes("GPTBot") || ua.includes("CCBot")) {
    return new NextResponse("Blocked", { status: 403 });
  }

  // Redirect based on country
  if (country === "DE") {
    url.pathname = "/de" + url.pathname;
    return NextResponse.redirect(url);
  }

  // Security headers
  const res = NextResponse.next();
  res.headers.set("X-Frame-Options", "DENY");
  res.headers.set("Content-Security-Policy", "script-src 'self'");
  return res;
}

export const config = {
  matcher: ["/((?!api|_next/static|favicon.ico).*)"],
};
```

## 5. Image Optimization

```jsx
import Image from "next/image";

<Image
  src="https://cdn.example.com/photo.jpg"
  alt="Description"
  width={800}
  height={600}
  priority={false}            // true for above-the-fold
  placeholder="blur"          // or "empty"
  blurDataURL="data:image/..." // tiny blurred placeholder
  quality={85}
  sizes="(max-width: 768px) 100vw, 50vw"
  // remote images need config in next.config.js
/>

// next.config.js
module.exports = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "cdn.example.com" },
    ],
    formats: ["image/avif", "image/webp"],
  },
};
```

## 6. Security

```jsx
// Server Actions — built-in CSRF protection (unforgeable action IDs)
"use server";
export async function deletePost(id) {
  // Always re-verify auth server-side
  const session = await getSession();
  if (!session?.isAdmin) throw new Error("Unauthorized");
  await db.post.delete(id);
  revalidatePath("/admin");
}

// RSC serialization — server → client data is serialized (not hydrated)
// No XSS from server data — React escapes by default

// CSP headers (via middleware or next.config)
const csp = {
  "default-src": "'self'",
  "script-src": "'self'",
  "style-src": "'self' 'unsafe-inline'",
  "img-src": "'self' https://cdn.example.com",
  "frame-ancestors": "'none'",
};
```

## 7. Caching Layers

Next.js has a multi-layered cache system:

| Cache | Scope | Invalidated by |
|-------|-------|----------------|
| Request Memoization | Per-request `fetch` dedup | End of request |
| Data Cache | Persistent `fetch` results | `revalidateTag`, `revalidatePath`, TTL |
| Full Route Cache | Static HTML pages | `revalidatePath`, redeployment |
| Router Cache | Client-side RSC payload cache | Navigation, `revalidatePath`, 30s TTL |

```jsx
// Request memoization — automatic within a render pass
// Two fetches with same URL + options → one request
async function Post({ id }) {
  const post = await getPost(id);  // 1st call
  const author = await getAuthor(post.authorId); // may call getPost somewhere
  // getPost(id) memoized — no second network request
}
```

### Cache Tags & On-Demand Revalidation

```jsx
// Tag any fetch
fetch(url, { next: { tags: [`post-${id}`] } });

// Revalidate from anywhere (webhook, server action, route handler)
import { revalidateTag } from "next/cache";

// POST /api/revalidate
export async function POST(request) {
  const { tag } = await request.json();
  revalidateTag(tag);
  return Response.json({ revalidated: true });
}
```

## 8. Streaming SSR Architecture

```
Request → Server renders Suspense boundaries in parallel
          ↓
HTML shell + inline <script> placeholders
          ↓
Client shows shell immediately (e.g. layout + sidebar)
          ↓
Each Suspense fallback replaced as chunk streams in
          ↓
Hydration proceeds incrementally — interactive as each chunk arrives
```

## 9. Summary

| Need | Solution |
|------|----------|
| SEO + fast FCP | SSR / SSG / ISR |
| Personalized content | Dynamic rendering |
| Fresh data without full rebuild | ISR + revalidation |
| Reduce client JS | RSC — keep logic on server |
| Fast page transitions | App Router + RSC payloads |
| Form mutations | Server Actions |
| Geolocation / auth check | Middleware (Edge) |
| Large images | next/image + remotePatterns |
| Security headers | Middleware or next.config |

---

## Related

- [Networking](../../11-networking/) — HTTP, performance, optimization
- [Security](../../13-security/) — CORS, authentication, XSS prevention
- [Backend](../../03-backend/) — API design and contracts
- [Performance Engineering](../../18-performance-engineering/) — Browser rendering
- [Testing](../../19-testing/) — E2E and component testing
