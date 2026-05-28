# 🧩 Service Decomposition & Domain-Driven Design

**Related**: [Architecture Patterns](/16-microservices/01-architecture-patterns.md) · [API Gateway](/16-microservices/04-api-gateway.md) · [Distributed Transactions](/16-microservices/06-distributed-transactions-saga.md)

---

## Table of Contents

- [Domain-Driven Design Overview](#-domain-driven-design-overview)
- [1. Bounded Context](#1-bounded-context)
- [2. Decomposition Strategies](#2-decomposition-strategies)
- [3. Domain Events](#3-domain-events)
- [4. Anti-Corruption Layer](#4-anti-corruption-layer)
- [5. Strangler Fig Pattern](#5-strangler-fig-pattern)
- [Decomposition Checklist](#-decomposition-checklist)
- [Simplest Mental Model](#-simplest-mental-model)

---

## 🧭 Domain-Driven Design Overview

```mermaid
mindmap
  root((DDD))
    Strategic
      Bounded Context
      Ubiquitous Language
      Context Map
    Tactical
      Entity
      Value Object
      Aggregate
      Repository
      Domain Event
      Domain Service
    Patterns
      Anti-Corruption Layer
      Shared Kernel
      Open-Host Service
      Published Language
      Separate Ways
```

---

## 1. Bounded Context

#### Step-by-Step

1. **Identify Domain Language**: In each context, determine what terms mean (Customer = buyer vs. support requester)
2. **Define Aggregate Boundaries**: Group entities that change together (Order + OrderItems as one aggregate)
3. **Separate Data Models**: Each context maintains its own Customer table with only relevant columns
4. **API Contracts**: Define how contexts communicate (REST, gRPC, or events) without exposing internal models
5. **Ubiquitous Language**: Use context-specific terminology in code (SalesContext uses "placeOrder", SupportContext uses "createTicket")
6. **Test Boundaries**: Verify services can operate independently if communication fails

#### Code Example

```python
# Python example showing bounded context separation
# Sales context owns customer creditworthiness
class SalesCustomer:
    def __init__(self, id: str, name: str, credit_limit: float):
        self.id = id
        self.name = name
        self.credit_limit = credit_limit
    
    def can_place_order(self, order_amount: float) -> bool:
        """Business logic for sales"""
        return order_amount <= self.credit_limit

# Support context owns customer satisfaction
class SupportCustomer:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self.open_tickets: List[str] = []
        self.satisfaction_score = 100
    
    def add_ticket(self, ticket_id: str):
        """Business logic for support"""
        self.open_tickets.append(ticket_id)
        # Support cares about tickets, not credit
    
    def rate_interaction(self, rating: int):
        self.satisfaction_score = max(0, min(100, self.satisfaction_score + rating))

# When Sales Service needs customer info, it queries its own Customer
sales_db = {"customer_123": SalesCustomer("123", "Alice", 5000)}

# When Support Service needs customer info, it queries its own Customer
support_db = {"customer_123": SupportCustomer("123", "Alice")}

# Both contexts are independent — neither depends on the other's schema
```

#### Real-World Scenario

Spotify decomposed their monolith by bounded context: Playback team owns user listening history and recommendations (core domain — complex ML algorithms). Account team owns subscriptions and billing (supporting — somewhat commodity). These teams never shared tables; when Playback needed subscriber info, Account Service exposed a simple REST API. This allowed Playback to scale independently during peak listening hours without affecting billing operations.

### What is a Bounded Context?

```text
Each service owns its domain model. The same "Customer" concept
may mean different things in different contexts:

┌────────────────────┐    ┌────────────────────┐
│  Sales Context     │    │  Support Context   │
│                    │    │                    │
│  Customer = Buyer  │    │  Customer =        │
│  • name            │    │    Ticket Creator  │
│  • email           │    │  • name            │
│  • creditLimit     │    │  • email           │
│  • paymentMethod   │    │  • openTickets     │
│  • shippingAddress │    │  • satisfactionScore│
└────────────────────┘    └────────────────────┘
```

### Code: Bounded Context in Action

```java
// Sales context — Customer is a buyer
package com.company.sales.domain;

@Entity
@Table(name = "customers")
public class Customer {
    @Id private Long id;
    private String name;
    private String email;
    private Money creditLimit;
    private PaymentMethod preferredPayment;
    private Address shippingAddress;

    public boolean canPlaceOrder(Money orderTotal) {
        return creditLimit.isGreaterThanOrEqual(orderTotal);
    }
}

// Support context — Customer is a ticket creator
package com.company.support.domain;

@Entity
@Table(name = "customers")
public class Customer {
    @Id private Long id;
    private String name;
    private String email;
    private int satisfactionScore;

    @OneToMany(mappedBy = "customer")
    private List<SupportTicket> tickets;

    public void incrementSatisfaction() {
        this.satisfactionScore++;
    }
}
```

---

## 2. Decomposition Strategies

#### Step-by-Step (General Decomposition Process)

1. **Map Business Capabilities**: List all business functions (ordering, payment, shipping, support)
2. **Identify Boundaries**: Use Conway's Law — organization structure informs system structure
3. **Define Data Ownership**: Which aggregate owns which data? Orders own items and total, Payment owns transaction records
4. **Check Independence**: Can each service exist without others? Can one be deployed without coordinating with others?
5. **Plan Communication**: What events/APIs connect services? Order → PaymentProcessed event → Invoice Service
6. **Establish Teams**: Ideally one team owns one service (two-pizza rule — team size that can be fed with two pizzas)

#### Code Example

```go
// Go example: decomposing an e-commerce system by business capability
package main

// STEP 1: Map Business Capabilities (domain model)
type BusinessCapability struct {
    Name        string
    Ownership   string  // Team responsible
    DataOwned   []string
}

var capabilities = []BusinessCapability{
    {
        Name:      "Product Catalog",
        Ownership: "Product Team",
        DataOwned: []string{"products", "categories", "descriptions"},
    },
    {
        Name:      "Order Management",
        Ownership: "Order Team",
        DataOwned: []string{"orders", "order_items", "shipping_address"},
    },
    {
        Name:      "Payment Processing",
        Ownership: "Payments Team",
        DataOwned: []string{"payments", "refunds", "transaction_logs"},
    },
    {
        Name:      "Inventory Management",
        Ownership: "Inventory Team",
        DataOwned: []string{"stock_levels", "reservations", "warehouse_locations"},
    },
}

// STEP 2: Define service boundaries
type ProductService struct {
    // Owns product_db exclusively
    db *sql.DB
}

type OrderService struct {
    // Owns order_db exclusively
    db                *sql.DB
    productServiceURL string  // Calls Product Service via HTTP
    paymentClient     PaymentClient
}

type PaymentService struct {
    // Owns payment_db exclusively
    db *sql.DB
}

// STEP 3: Define boundaries with aggregates
type Order struct {
    ID       string
    CustomerID string
    Items    []OrderItem  // Order aggregate includes items
    Total    float64
}

type OrderItem struct {
    ProductID string     // Just the ID, not full Product entity
    Quantity  int
    Price     float64    // Denormalized price at order time
}

// STEP 4: Communication between services
type OrderCreatedEvent struct {
    OrderID    string
    CustomerID string
    Items      []OrderItem
    Total      float64
}

func (os *OrderService) CreateOrder(req CreateOrderRequest) (*Order, error) {
    // First, verify product exists and get current price
    product, err := os.getProductFromCatalog(req.ProductID)
    if err != nil {
        return nil, err  // Fail if product service down
    }

    // Create order in our database
    order := &Order{
        ID:         generateID(),
        CustomerID: req.CustomerID,
        Items: []OrderItem{
            {
                ProductID: product.ID,
                Quantity:  req.Quantity,
                Price:     product.Price,  // Capture price at order time
            },
        },
        Total: product.Price * float64(req.Quantity),
    }

    // Save to order_db
    if err := os.saveOrder(order); err != nil {
        return nil, err
    }

    // Publish event (async) — Payment Service will consume
    eventBus.Publish("order.created", OrderCreatedEvent{
        OrderID:    order.ID,
        CustomerID: order.CustomerID,
        Items:      order.Items,
        Total:      order.Total,
    })

    return order, nil
}

// STEP 5: Define data ownership clearly
func (is *InventoryService) ReserveStock(orderID string, items []OrderItem) error {
    // Inventory owns stock_levels table
    // It does NOT own orders — it gets notified via events
    for _, item := range items {
        stock, err := is.getCurrentStock(item.ProductID)
        if err != nil || stock < item.Quantity {
            return fmt.Errorf("insufficient stock for %s", item.ProductID)
        }
        // Deduct from inventory
        is.deductStock(item.ProductID, item.Quantity)
    }
    return nil
}

// STEP 6: Team ownership
type TeamService struct {
    Name      string
    Service   string
    OnCall    string
    SlackChannel string
}

var teamOwnership = []TeamService{
    {"Product Team", "ProductService", "alice@company.com", "#product-oncall"},
    {"Order Team", "OrderService", "bob@company.com", "#order-oncall"},
    {"Payment Team", "PaymentService", "charlie@company.com", "#payment-oncall"},
    {"Inventory Team", "InventoryService", "diana@company.com", "#inventory-oncall"},
}
```

#### Real-World Scenario

Amazon decomposed by business capability in the early 2000s: Customer Relationship Management, Order Processing, Fulfillment, and Payments became separate services. Each team built their own service using whatever tech they preferred. When order processing team needed to make Orders 100x faster, they rewrote their service in a faster language without coordinating with 8 other teams. This organizational structure enabled Amazon's rapid scaling.

### 2.1 Decompose by Business Capability

```text
Identify business functions and map to services:

Business Capability Map:

┌────────────────────────────────────────────────────────────┐
│                      E-Commerce                            │
├─────────┬─────────┬──────────┬─────────┬──────────────────┤
│Product  │ Order   │ Inventory│ Payment │ Customer Service │
│Catalog  │ Mgmt    │ Mgmt     │ Process │   & Support      │
├─────────┼─────────┼──────────┼─────────┼──────────────────┤
│ Product │ Order   │ Stock    │ Payment │ Customer         │
│ DB      │ DB      │ DB       │ DB      │   DB             │
└─────────┴─────────┴──────────┴─────────┴──────────────────┘
```

### 2.2 Decompose by Subdomain (DDD)

```java
// Core domain — competitive advantage, complex logic
@Service
public class PricingEngine {
    public Price calculatePrice(Product product, Customer customer) {
        // Complex pricing algorithm — core business value
        Money basePrice = product.getBasePrice();
        Money discount = calculateDiscount(customer);
        Money tax = calculateTax(product, customer.getAddress());
        return basePrice.subtract(discount).add(tax);
    }
}

// Supporting domain — necessary but not unique
@Service
public class EmailService {
    public void sendEmail(Email email) {
        // Could be replaced by SaaS (SendGrid, SES)
        mailSender.send(email);
    }
}

// Generic domain — buy, don't build
// Use Stripe for payments, Auth0 for auth, etc.
```

### 2.3 Decompose by Volatility

```text
Services that change together should be together.
Services that change at different rates should be separate.

Example:
  ┌──────────────────────────────────────┐
  │ Frequently Changing    │ Stable      │
  │ ───────────────────────│─────────────│
  │ • Pricing Engine      │ • User Auth │
  │ • Recommendation UI   │ • Logging   │
  │ • Checkout Flow       │ • Audit     │
  │ • Promotion Engine    │ • Reporting │
  └──────────────────────────────────────┘
  ➜ Split into separate services so stable ones don't
    get redeployed for pricing changes
```

### 2.4 Transaction Boundaries

```java
// ❌ BAD — different aggregates in same transaction
@Service
public class CheckoutService {
    @Transactional
    public void checkout(Long userId, List<Item> items) {
        Order order = new Order(userId, items);     // Order aggregate
        orderRepo.save(order);
        InventoryDeduction deduction = new InventoryDeduction(items); // Inventory aggregate!
        inventoryRepo.save(deduction);   // TWO aggregates in one TX = wrong!
    }
}

// ✅ GOOD — each aggregate in its own transaction boundary
@Service
public class CheckoutService {
    @Transactional  // Only Order aggregate
    public Order checkout(Long userId, List<Item> items) {
        Order order = new Order(userId, items);
        orderRepo.save(order);
        eventPublisher.publish(new OrderPlacedEvent(order));
        return order;
    }
}

// Separate handler for Inventory aggregate
@Component
public class InventoryHandler {
    @Transactional  // Own transaction boundary
    public void handle(OrderPlacedEvent event) {
        inventoryService.deductStock(event.getItems());
    }
}
```

---

## 3. Domain Events

### Event Definition

```java
// Base event class
public abstract class DomainEvent {
    private final String eventId = UUID.randomUUID().toString();
    private final Instant occurredAt = Instant.now();

    public String getEventId() { return eventId; }
    public Instant getOccurredAt() { return occurredAt; }
}

// Specific event
public class OrderPlacedEvent extends DomainEvent {
    private final Long orderId;
    private final Long customerId;
    private final Money total;
    private final List<OrderItem> items;

    public OrderPlacedEvent(Long orderId, Long customerId, Money total,
                            List<OrderItem> items) {
        this.orderId = orderId;
        this.customerId = customerId;
        this.total = total;
        this.items = items;
    }

    // getters
}
```

### Event Publishing

```java
// Aggregate root — publishes events
@Entity
public class Order {
    @Id private Long id;
    private OrderStatus status;

    @Transient
    private final List<DomainEvent> events = new ArrayList<>();

    public void place() {
        validateState();
        this.status = OrderStatus.PLACED;
        events.add(new OrderPlacedEvent(id, customerId, total, items));
    }

    public void confirm() {
        this.status = OrderStatus.CONFIRMED;
        events.add(new OrderConfirmedEvent(id));
    }

    public List<DomainEvent> getEvents() {
        return List.copyOf(events);
    }

    public void clearEvents() {
        events.clear();
    }
}

// Service — publishes events after save
@Service
public class OrderService {
    private final OrderRepository orderRepository;
    private final EventPublisher eventPublisher;

    @Transactional
    public Order placeOrder(CreateOrderRequest request) {
        Order order = new Order(request);
        order.place();  // creates OrderPlacedEvent
        order = orderRepository.save(order);

        // Publish all domain events
        for (DomainEvent event : order.getEvents()) {
            eventPublisher.publish(event);
        }
        order.clearEvents();
        return order;
    }
}
```

### Outbox Pattern (Reliable Publishing)

```text
The Problem:
  ┌────────────┐     save     ┌────────────┐
  │ Save Order │────────────> │  Database  │  ✅
  │ to DB      │              └────────────┘
  │            │     publish  ┌────────────┐
  │ Publish    │────────────> │  Kafka     │  ❌ Crash here!
  │ Event      │              │  (Message  │  → Event lost
  │            │              │   lost!)   │  → Inconsistency
  └────────────┘              └────────────┘

Solution — Outbox Pattern:
  ┌────────────┐     save     ┌────────────────────┐
  │ Save Order ├────────────> │  Database           │
  │ AND Event  │              │  ┌──────────────┐   │
  │ (same TX!)  │              │  │ orders       │   │
  │            │              │  │ outbox       │   │
  └────────────┘              │  └──────────────┘   │
                              └────────┬───────────┘
                                       │
                     Poll + publish ───┘
                          (separate process)
                                       │
                              ┌────────▼───────────┐
                              │  Kafka              │
                              │  (reliable now!)    │
                              └────────────────────┘
```

```java
// Outbox entity — same DB as aggregate
@Entity
@Table(name = "outbox")
public class OutboxEvent {
    @Id private String id;
    private String aggregateType;
    private String aggregateId;
    private String eventType;
    @Lob private String payload;  // JSON serialized event
    private Instant createdAt;
    private boolean published;

    public static OutboxEvent from(DomainEvent event, String aggregateType) {
        OutboxEvent outbox = new OutboxEvent();
        outbox.id = event.getEventId();
        outbox.aggregateType = aggregateType;
        outbox.eventType = event.getClass().getSimpleName();
        outbox.payload = serialize(event);
        outbox.createdAt = Instant.now();
        outbox.published = false;
        return outbox;
    }
}

// Scheduled publisher — polls and publishes
@Component
public class OutboxPublisher {
    private final OutboxRepository outboxRepository;
    private final KafkaTemplate<String, String> kafkaTemplate;

    @Scheduled(fixedDelay = 1000)  // every second
    @Transactional
    public void publishPendingEvents() {
        List<OutboxEvent> pending = outboxRepository
            .findByPublishedFalseOrderByCreatedAtAsc();

        for (OutboxEvent event : pending) {
            try {
                kafkaTemplate.send(event.getEventType(), event.getPayload());
                event.setPublished(true);
                outboxRepository.save(event);
            } catch (Exception e) {
                log.error("Failed to publish event: {}", event.getId(), e);
                // Will retry next cycle
            }
        }
    }
}
```

---

## 4. Anti-Corruption Layer

### Purpose

```text
Prevents external domain models from leaking into your domain.

Context 1 (Legacy)          ACL                 Context 2 (New)
┌────────────┐         ┌────────────┐         ┌────────────┐
│ Old CRM    │         │ Translator │         │ New Order  │
│            │         │            │         │ Service    │
│ CustomerDTO│────────>│ Adapts     │────────>│ Customer   │
│ {          │         │ Old model  │         │ {          │
│   fname    │         │ → New      │         │   firstName│
│   lname    │         │   model    │         │   lastName │
│   cid      │         │            │         │   id       │
│   emailAddr│         │            │         │   email    │
│ }          │         │            │         │ }          │
└────────────┘         └────────────┘         └────────────┘
```

### Code: Anti-Corruption Layer

```java
// EXTERNAL — legacy CRM data model (don't let this leak!)
public class LegacyCustomerDTO {
    private int cid;           // customer ID as int
    private String fname;      // first name
    private String lname;      // last name
    private String emailAddr;  // called emailAddr
    private String addrLine1;  // flat address structure
    private String addrLine2;
    private String addrCity;
    private String addrZip;
    // getters/setters
}

// ANTI-CORRUPTION LAYER — translator
@Component
public class CustomerTranslator {
    public Customer toDomain(LegacyCustomerDTO legacy) {
        return new Customer(
            String.valueOf(legacy.getCid()),   // int → String ID
            new PersonName(
                legacy.getFname(),              // fname → firstName
                legacy.getLname()               // lname → lastName
            ),
            new EmailAddress(legacy.getEmailAddr()),
            new Address(
                legacy.getAddrLine1(),
                legacy.getAddrLine2(),
                legacy.getAddrCity(),
                legacy.getAddrZip()
            )
        );
    }
}

// ACL — service that calls legacy system and translates
@Service
public class LegacyCustomerService {
    private final LegacyCrmClient legacyClient;
    private final CustomerTranslator translator;

    public Customer findCustomer(String id) {
        LegacyCustomerDTO legacy = legacyClient.getCustomer(Integer.parseInt(id));
        return translator.toDomain(legacy);  // return clean domain object
    }
}

// Domain — pure, unaffected by legacy format
public class Customer {
    private final CustomerId id;
    private final PersonName name;
    private final EmailAddress email;
    private final Address address;

    // Clean domain constructor
    public Customer(CustomerId id, PersonName name,
                    EmailAddress email, Address address) {
        this.id = id;
        this.name = name;
        this.email = email;
        this.address = address;
    }
}
```

---

## 5. Strangler Fig Pattern

### Migration Strategy

```text
Slowly replace monolith functionality with microservices.

Phase 1: Start small
  ┌──────────────────────┐
  │    Monolith          │
  │ ┌─────┐ ┌─────┐ ┌──┐│
  │ │Auth │ │User │ │..││
  │ └─────┘ └─────┘ └──┘│
  └──────────────────────┘

Phase 2: Extract a service
  ┌────────────┐         ┌──────────────────┐
  │  API GW    │────────>│  Auth Service    │ (new)
  │ (routes)   │         └──────────────────┘
  └─────┬──────┘
        │ fallback
  ┌─────▼────────┐
  │  Monolith    │
  │ (old auth)   │
  └──────────────┘

Phase 3: Full replacement
  ┌─────────────────────────────────────────┐
  │  API Gateway                            │
  ├──────┬──────────┬───────────┬──────────┤
  │ Auth │  User    │  Order    │  Payment │
  │ Svc  │  Svc     │  Svc      │  Svc     │
  └──────┴──────────┴───────────┴──────────┘
  │ Monolith fully retired │
```

### Code: Strangler Fig Implementation

```java
// API Gateway with strangle routing
@RestController
public class BackendController {
    private final RestTemplate rest;

    public BackendController(RestTemplate rest) {
        this.rest = rest;
    }

    @GetMapping("/api/auth/{id}")
    public ResponseEntity<?> getAuth(@PathVariable String id) {
        // Try new microservice first
        try {
            String url = "http://auth-service/api/internal/auth/" + id;
            return ResponseEntity.ok(rest.getForObject(url, AuthDTO.class));
        } catch (Exception e) {
            log.info("Auth service unavailable, falling back to monolith");
        }

        // Fallback to monolith
        String url = "http://monolith.internal/rest/api/auth/" + id;
        return ResponseEntity.ok(rest.getForObject(url, AuthDTO.class));
    }

    // Feature flag — gradually shift traffic
    @GetMapping("/api/users/{id}")
    public ResponseEntity<?> getUser(@PathVariable String id,
                                     @RequestHeader("X-New-User-Service")
                                     String forceNew) {
        if ("true".equals(forceNew) || shouldUseNewService(id)) {
            return callNewUserService(id);
        }
        return callLegacyUserService(id);
    }

    private boolean shouldUseNewService(String id) {
        // Gradual rollout: 10% of traffic → new service
        return Math.random() < 0.1;
    }
}
```

### Strangler Fig with Feature Flags

```yaml
# Feature toggle configuration
feature-flags:
  use-new-user-service: false      # default off
  use-new-order-service: true      # fully rolled out
  use-new-payment-service: 10%     # graduated rollout
```

---

## 📋 Decomposition Checklist

```text
Before splitting a service, ask:

☐ Does it have a clear bounded context? (DDD)
☐ Does it own its data? (No shared tables)
☐ Can it be deployed independently?
☐ Does it have a well-defined API?
☐ Can it scale independently?
☐ Does it make sense to fail independently?
☐ Does it have its own team ownership?
☐ Can it use a different tech stack if needed?
☐ Is the transaction boundary clear?
☐ Is there a clear event/API contract?

If YES to all → Good candidate for microservice
If NO to any → Consider keeping in current service
```

---

## 🧠 Simplest Mental Model

```text
BOUNDED        =  The Pizza Place menu is different from the Dessert
CONTEXT           Shop menu. Both sell "Cheese" but they mean different
                  things. Each service speaks its own language.

DECOMPOSITION   =  Cutting a large cake (monolith) into slices.
                   Each slice has its own plate (database),
                   its own recipe (business logic), and can be
                   eaten independently (deployed separately).

DOMAIN EVENT    =  When pizza is ready, the kitchen rings a bell.
                   Anyone listening can react: "Notify customer",
                   "Update inventory", "Start delivery timer".

ANTI-             A translator who sits between two people speaking
CORRUPTION        different languages. Makes sure neither person's
LAYER             strange grammar infects the other's speech patterns.

STRANGLER FIG  =  A vine that grows around an old tree, gradually
                   replacing it. The new system grows alongside the
                   old one until the old one can be removed entirely.

OUTBOX PATTERN =  Writing a letter (event) and immediately putting
                   it in your OUTBOX safe (same DB transaction).
                   A mail carrier (background process) picks it up
                   reliably. Even if the carrier crashes, the letter
                   is still safe in the outbox.
```

---

**Next**: [Service Discovery](/16-microservices/03-service-discovery.md)

## Related

- [Cap Consistency](/09-distributed-systems/01-cap-consistency.md)
- [Consensus Replication](/09-distributed-systems/01-consensus-replication.md)
- [Consensus Raft](/09-distributed-systems/02-consensus-raft.md)
- [Distributed Transactions](/09-distributed-systems/02-distributed-transactions.md)
- [Distributed Caching](/09-distributed-systems/03-distributed-caching.md)
- [Distributed Storage](/09-distributed-systems/03-distributed-storage.md)
