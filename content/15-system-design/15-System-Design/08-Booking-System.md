# 08-Booking-System

Booking system design covers reservation management for domains like hotels, flights, event ticketing, and appointment scheduling — focusing on inventory management, double-booking prevention, time-slot handling, and overbooking strategies.

## Key Components
- **Inventory Service**: Manages available units (rooms, seats, tables) across time dimensions (dates, slots). Each unit has a calendar of availability. Inventory is updated atomically on reserve → confirm → cancel transitions.
- **Reservation Service**: State machine (pending → confirmed → checked-in → completed → cancelled). Holds inventory for a limited time (e.g., 15-minute payment window for pending reservations).
- **Time Slot Management**: For appointment-based systems — defines available windows, duration, buffer between slots, and recurrence rules. Must prevent overlapping bookings for the same resource.
- **Pricing Engine**: Dynamic pricing based on demand, seasonality, length of stay, and customer segment. Needs last-room availability (LRA) calculations to decide discount levels.
- **Overbooking Strategy**: Accepts more reservations than available inventory (airlines do this at ~5-10% overbooking). Requires statistical models predicting no-show rate and a compensation policy for bumped customers.

## Key Challenges
- **Double-booking prevention**: Two concurrent requests for the same resource in the same time window. Requires pessimistic locking (SELECT FOR UPDATE) or optimistic locking with version stamps on the inventory row.
- **Temporary holds**: Cart-like approach where inventory is reserved for a limited time (e.g., 10 minutes). The hold timer is managed server-side. On expiry, inventory is released back to the pool.
- **Distributed transactions**: Booking across multiple resources (hotel + flight) requires either sagas or two-phase commit. Usually a saga with compensating actions (cancel hotel if flight booking fails).
- **Time zone handling**: A booking at "3 PM" depends on the resource's time zone, not the customer's. Store all times in UTC with the resource's timezone offset. Convert for display only.
- **Overbooking risk**: Bumping customers is expensive (compensation, reputation). The overbooking model must be carefully calibrated with real no-show data.

## Key Design Decisions
- **Pessimistic locking for high-value bookings**: SELECT FOR UPDATE on the inventory row during the booking transaction. Ensures no race condition on the last available unit.
- **Timeout-based hold release**: A background job scans for expired holds (pending reservations past the payment window) and atomically releases the inventory. Uses a partitioned job to avoid scanning the full table.
- **CQRS for availability reads**: Current availability is a frequent read (users searching). Maintain a denormalized availability summary in Redis that is updated on every reservation event. Read from Redis, write to PostgreSQL.
- **Saga pattern for multi-resource**: Each step (book hotel, book flight) has a compensating action. The saga coordinator tracks state and executes rollbacks in reverse order on failure.

## Related Concepts
- [01-Ecommerce](01-Ecommerce.md) — Shopping cart hold patterns translate to temporary booking holds
- [07-Payment-System](07-Payment-System.md) — Payment capture tied to booking confirmation/release

---

## Mental Model
A booking system works like a restaurant with limited tables. The host (inventory service) marks a table as "reserved" on a paper chart when you call. If you don't show within 15 minutes, they erase the mark and give the table to a walk-in. Overbooking means the host accepts 12 parties for 10 tables, knowing 2 likely won't show — but has a contingency plan (free drinks, waitlist) if everyone arrives.
