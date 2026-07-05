# State

The State pattern manages state transitions by representing each distinct state as a separate object. In microservices, it models business workflows with explicit lifecycles — orders, shipments, user accounts, payment transactions.

## Overview
State pattern encapsulates state-specific behavior in dedicated objects and delegates to the current state object for actions. When the state changes, the context switches to a different state object. In microservices, this is commonly used for order lifecycles (pending → confirmed → shipped → delivered → returned), payment transactions, approval workflows, and subscription management. The pattern makes state transitions explicit, auditable, and resistant to invalid transitions.

## Key Characteristics
- **Explicit Transitions**: Allowed and disallowed transitions are clearly defined; invalid moves are rejected at the code level.
- **State-Specific Behavior**: Each state defines its own rules for what actions are permitted and how they behave.
- **No Giant Switch Blocks**: Eliminates sprawling switch statements by distributing state logic across classes.
- **Transition Events**: States can emit events on entry, exit, or when specific actions occur.
- **Auditability**: Each state change can be logged with timestamp, previous state, and context.

## Why It Matters
Business processes rarely traverse simple linear paths. An order can be canceled only if it hasn't shipped; a payment can be refunded only if it was captured. Without explicit state management, these rules are scattered across conditionals, leading to bugs when edge cases are missed. The State pattern centralizes lifecycle rules, making the system's behavior predictable and safe.

## Related Concepts
- [Strategy](06-Strategy.md) — both compose behavior; State changes behavior when state changes, Strategy changes behavior when algorithm is selected.
- [Workflow](11-Workflow.md) — coordinates multi-step business processes; State models the transitions within a single entity's lifecycle.
- [Observer](08-Observer.md) — can notify listeners when state transitions occur (e.g., order confirmed → email service).

---

## Mental Model
A traffic light. The light is always in one of three states: green, yellow, or red. Each state defines different behavior — cars may go on green, slow down on yellow, stop on red. Transitions are strictly defined (green → yellow → red → green). The light doesn't use conditional checks like "if current color is green and timer > 30, switch to yellow" — instead it delegates to the current state object which knows the next transition.
