# 01-Ecommerce

E-commerce system design covers the architecture behind online shopping platforms — handling product catalog browsing, shopping cart management, checkout flows, payment processing, inventory tracking, and order fulfillment at scale.

## Key Components
- **Product Catalog**: Searchable, filterable inventory with structured attributes (SKU, price, category, variants). Requires indexing for full-text search, faceted navigation, and image serving.
- **Shopping Cart**: Temporary session-bound state with add/remove/update operations. Must survive login transitions (merge anonymous → authenticated cart) and device changes via server-side persistence.
- **Checkout**: Multi-step flow (address → shipping → payment → review). Designed as a state machine with idempotent transitions to prevent double-charge and allow resume on failure.
- **Payment Gateway**: Integrates with PSPs (Stripe, Adyen) via tokenization. Card details never touch the server — payment intents are created server-side, confirmed client-side.
- **Inventory Service**: Real-time stock tracking with optimistic reservation at add-to-cart and hard decrement at order placement. Handles oversell via atomic decrement operations.
- **Order Management**: State machine (pending → confirmed → shipped → delivered → returned). Drives fulfillment pipeline, notifications, and analytics.

## Key Challenges
- **Consistency vs availability**: Inventory counts must be strongly consistent; catalog views can be eventually consistent.
- **Concurrency control**: Two users buying the last item — use optimistic locking or distributed locks on SKU.
- **Session management**: Cart state must survive browser close, device switch, and session expiry.
- **Idempotency**: Payment confirmation and order submission must be safe to retry without double-charge.
- **Peak load**: Black Friday traffic demands aggressive caching, CDN offload, and auto-scaling.

## Key Design Decisions
- **Read vs write paths**: Catalog queries route to read replicas; checkout writes go to primary DB. Use CQRS for separation at extreme scale.
- **Cache strategy**: Product detail pages cached at CDN edge. Inventory counts cached with short TTL (seconds), invalidated on purchase.
- **Database choice**: PostgreSQL for orders/inventory (ACID required), Elasticsearch for product search, Redis for cart/session state.
- **Service decomposition**: Typically split into Catalog, Cart, Checkout, Payment, Inventory, Order, and Notification services.

## Related Concepts
- [07-Payment-System](07-Payment-System.md) — Payment processing patterns shared across e-commerce platforms
- [08-Booking-System](08-Booking-System.md) — Inventory management and double-booking prevention parallels

---

## Mental Model
Think of an e-commerce platform as a physical store with shopping assistants. The catalog is the shelves (fast lookup by aisle), carts are the baskets, checkout is the register (one-person-at-a-time with a lock on that register), and inventory is the stockroom count that updates every time something leaves the floor.
