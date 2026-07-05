# 09-Banking

Banking system design covers the core infrastructure for financial services — ledger management, transaction processing, balance computation, compliance screening, fraud detection, and integration with legacy core banking systems.

## Key Components
- **Ledger Service**: Double-entry accounting engine. Every transaction creates two entries (debit one account, credit another). The sum of all entries across all accounts must always equal zero. Ledger entries are immutable — append-only with no deletes or updates.
- **Account Service**: Manages account state (balances, status, ownership). Balance is derived from summing all ledger entries for that account. Supports account types: checking, savings, loan, credit card.
- **Transaction Processing**: Handles payment initiation, clearing (exchange between banks), and settlement (final transfer). Split into authorization (reserve funds) and posting (finalize). For wire transfers, uses ISO 20022 messages.
- **Fraud Detection**: ML-based real-time scoring of transactions (velocity, pattern of life, geolocation, device fingerprint). Rules engine for regulatory checks (OFAC sanctions screening, AML monitoring). Accept/review/block decisions within milliseconds.
- **Compliance Service**: Screens all parties against sanctions lists (OFAC, UN, EU), Politically Exposed Persons (PEP) databases, and internal watchlists. Must run before transaction completion and then retrospectively for pattern detection.
- **Interest Calculation**: Batch process computing accrued interest on deposits and loans. Runs daily (end of day) or continuously for some products. Uses average daily balance method or daily compounding.

## Key Challenges
- **Consistency is non-negotiable**: Money movement requires strict ACID within an account and eventual consistency across systems. A double-spend scenario means real financial loss. Use pessimistic locking on accounts during transfers.
- **Reconciliation**: Internal ledger must match external partners (correspondent banks, card networks). Discrepancies are common (fees, exchange rates, timing differences) and must be flagged and resolved.
- **Auditability**: Every financial event must be traceable. Use event sourcing — the ledger is the event store. Every balance is a projection. Compliance examiners can replay any account's transaction history.
- **System of record vs system of engagement**: Core banking (legacy mainframe) handles the official ledger. Modern APIs (engagement layer) must gracefully handle latency and batch-oriented interfaces of the core system.
- **Regulatory reporting**: Daily/weekly/monthly reports to central banks and regulators (BASEL III, IFRS 9, AML reports). These are high-stakes — incorrect reporting can result in fines.

## Key Design Decisions
- **Double-entry ledger as event store**: Instead of storing current balances, store every transaction event. Balance is computed as the projection of all events for that account. Immutable append-only log provides perfect audit trail.
- **Saga for multi-account transfers**: Credit one account → debit another is a saga. If the debit fails, the credit must be reversed. Each step has a compensating action, coordinated by a saga manager.
- **CQRS for reads**: Account balances are projected into a read-optimized table updated by the ledger event stream. This separates the fast read (balance check) from the append-heavy write (transaction recording).
- **Batch for core banking**: Real-time APIs translate into batch files (NACHA, SWIFT MT/MX) sent to core systems. The translation layer maps ISO 20022 JSON messages to legacy formats with reconciliation IDs.

## Related Concepts
- [07-Payment-System](07-Payment-System.md) — Payment authorization, capture, and settlement flows
- [01-Ecommerce](01-Ecommerce.md) — Merchant payment processing and payout reconciliation

---

## Mental Model
A banking ledger is a book where every page is a transaction, and the book is printed in permanent ink — no erasing, no white-out. Your balance is simply whatever the sum of those indelible entries says it is. If you send money to a friend, the book records that as two entries: -100 from your column, +100 to theirs. The bookkeeper (ledger service) never loses count.
