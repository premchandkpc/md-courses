# 07-Payment-System

Payment system design covers the architecture for processing monetary transactions securely — handling authorization, capture, settlement, reconciliation, fraud detection, and compliance with PCI-DSS, PSD2, and regional regulations.

## Key Components
- **Payment Gateway**: Accepts payment requests from merchants, validates card data (via tokenization — never passes raw PAN), and routes to the appropriate processor. Handles PCI-DSS compliance scope.
- **Processor/PSP**: External partner (Stripe, Adyen, Chase) that communicates with card networks (Visa, Mastercard) for settlement. The gateway abstracts multiple PSPs for failover and least-cost routing.
- **Authorization**: Checks if funds are available and places a hold. Returns an authorization code. Auths expire after a few days if not captured.
- **Capture**: Completes the transaction, moving funds from the authorization hold to the merchant account. Usually occurs at shipment (not at cart submission).
- **Settlement**: Batch process at end of day — all captured transactions are batched to the card network and funds transferred to the merchant's acquiring bank account.
- **Reconciliation**: Matches internal transaction logs against PSP settlement reports and bank statements. Detects mismatches (unmatched payments, incorrect fees, chargebacks).
- **Fraud Detection**: Rule engine + ML models scoring transactions in real-time (velocity checks, geolocation anomalies, card testing detection, device fingerprinting).

## Key Challenges
- **Idempotency**: The same payment request may arrive twice (network retry, user double-click). Use an idempotency key (typically a UUID per request), stored with result status. Retry with same key returns cached result.
- **Exactly-once processing**: Achieved through a two-phase protocol: create payment intent (reserved), confirm (irreversible). The confirm endpoint is idempotent — first success is final.
- **Double-charge prevention**: Must prevent charging the same authorization twice. The authorization → capture flow with a state machine ensures each auth is captured at most once.
- **Consistency across services**: Payment status must be consistent between checkouts, orders, and notifications. Use a transactional outbox pattern — write event to outbox in same DB transaction as payment state change; a separate process publishes the event.
- **Fraud without friction**: Blocking fraudulent transactions while minimizing false declines. A 1% false decline rate at scale means millions in lost revenue.

## Key Design Decisions
- **Separate auth and capture**: Auth at checkout, capture at fulfillment. Avoids charging for items that are later found out-of-stock.
- **Idempotency key as a primary concept**: Every payment mutation endpoint requires an idempotency key. The key is typically the order ID + attempt counter.
- **State machine for payment lifecycle**: Created → Authorized → Captured → Settled → Reconciled. Failed states: AuthFailed, CaptureFailed, Refunded, ChargedBack. Strict transitions enforced by the payment service.
- **Database**: PostgreSQL for ledger (ACID required), with careful index design on payment_id, merchant_id, and idempotency_key.

## Related Concepts
- [01-Ecommerce](01-Ecommerce.md) — Payment integration within the broader e-commerce checkout flow
- [09-Banking](09-Banking.md) — Ledger management and reconciliation patterns

---

## Mental Model
A payment system is like a restaurant bill: the waiter (gateway) brings the bill (authorization), you accept the hold by signing (confirm), and the restaurant only runs the card (capture) after you've finished your meal and the kitchen confirms everything was available.
