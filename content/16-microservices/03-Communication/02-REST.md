# 02-REST

REST (Representational State Transfer) is an architectural style for designing networked APIs using HTTP methods and resource-oriented URLs. It is the most widely adopted synchronous communication protocol for microservices.

## Overview

REST treats everything as a resource identified by a URL. Operations on resources are performed using standard HTTP methods: GET (read), POST (create), PUT (replace), PATCH (partial update), DELETE (remove). REST APIs are stateless — each request contains all the information needed to process it. This simplicity, combined with the ubiquity of HTTP, makes REST the default choice for service-to-service and external APIs.

## Key Characteristics

- **Resource-Oriented**: URLs represent nouns, not verbs. `/orders/123` not `/getOrder?id=123`. This creates a consistent, discoverable API surface.
- **HTTP Methods as Verbs**: GET, POST, PUT, PATCH, DELETE provide a universal vocabulary for CRUD operations. Idempotency is built in: GET, PUT, DELETE are idempotent; POST is not.
- **Statelessness**: Each request is self-contained. No server-side session state. This enables horizontal scaling and load balancing.
- **Status Codes**: HTTP status codes communicate results: 200 (OK), 201 (Created), 400 (Bad Request), 404 (Not Found), 409 (Conflict), 500 (Internal Server Error). Consistent status code usage makes error handling predictable.
- **HATEOAS (Hypermedia as the Engine of Application State)**: Resources include links to related actions. Rarely implemented in practice but valuable for truly self-documenting APIs.

## Why It Matters

REST is the lingua franca of microservices APIs. Its ubiquity means every language and framework has mature HTTP tooling. The tradeoff is performance — JSON serialization is slower than binary formats, and HTTP/1.1 has overhead that gRPC avoids. For public and external APIs, REST remains the standard because of its simplicity, cacheability, and universal client support.

## Related Concepts

- [03-gRPC](03-gRPC.md) — the main alternative for sync communication
- [06-API-First](../02-Service-Design/06-API-First.md) — OpenAPI defines REST contracts
- [08-Backward-Compatibility](../02-Service-Design/08-Backward-Compatibility.md) — REST API evolution best practices

---

## Mental Model

A REST API is like a library catalog. Each book (resource) has a unique shelf location (URL). The card catalog (API documentation) tells you how to find books and what operations you can do: look up (GET), check out (POST — non-idempotent), return (PUT — idempotent). You don't need to know how the library is organized internally; the catalog is your interface.
