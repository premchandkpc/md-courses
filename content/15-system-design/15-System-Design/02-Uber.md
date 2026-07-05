# 02-Uber

Ride-hailing system design covers real-time matching of riders with drivers, location tracking, dynamic pricing, route optimization, ETA calculation, and trip lifecycle management across millions of concurrent users.

## Key Components
- **Rider App**: Request flow (pickup → destination → ride type → match → track → pay → rate)
- **Driver App**: Go online → receive trip offers → accept → navigate → complete → earnings
- **Matching Service**: Geospatial index (quadtree/geohash) to find nearby drivers. Runs match logic on each new request, considering proximity, driver score, surge pricing.
- **Location Service**: Drivers publish GPS coordinates every ~4 seconds via WebSocket. Ingested into a stream (Kafka) and stored in a time-series DB for replay and analytics.
- **Pricing Engine**: Dynamic surge pricing based on supply/demand ratio in geohash regions. Uses real-time signals: number of open requests vs available drivers in each cell.
- **ETA Calculator**: Computes estimated time using real-time traffic data and historical route patterns. Road network graph with edge weights updated by live traffic feed.
- **Trip Service**: Manages trip lifecycle (requesting → matched → en-route → arrived → in-trip → completed → paid). State machine with strict transitions.

## Key Challenges
- **Spatial indexing**: Query "all drivers within 2km" must return in milliseconds. Geohash or Google S2 cells with grid refinement.
- **Real-time consistency**: Driver state (available, busy, offline) must be accurate within seconds. Stale data causes bad matches.
- **Race conditions**: Two requests matching same driver simultaneously — use atomic state transition on the driver record or a distributed lock per driver.
- **Surge pricing fairness**: Must be transparent, bounded, and not exploitable (the "surge shadow" problem).
- **Scalability at events**: Concerts, sports games create demand hotspots. Pre-positioning and predictive surge modeling help.

## Key Design Decisions
- **Geohash precision**: Use dynamic precision — coarse grid for sparse areas, fine grid for dense urban centers. Quadtree partitioning for spatial sharding.
- **Dispatch algorithm**: Not nearest-driver but a batched optimization — consider multiple requests and drivers simultaneously, maximizing global matching score using minimum-weight bipartite matching.
- **Communication**: WebSocket for real-time location/status updates, HTTP/2 for API calls, push notifications as fallback.
- **Storage**: Cassandra for trip history (write-heavy), Redis for driver location cache, PostgreSQL for financial records.

## Related Concepts
- [09-Banking](09-Banking.md) — Payment settlement and payout processing for driver earnings
- [10-Notification-System](10-Notification-System.md) — Push notifications for trip status updates to riders and drivers

---

## Mental Model
Uber is a two-sided marketplace where supply (drivers) moves through physical space. Think of it like an air-traffic control system for cars — a control tower constantly knows each vehicle's position, matches incoming "landings" (ride requests) to the nearest available plane (driver), charges a dynamic fee based on how many planes are circling vs how many passengers are waiting.
