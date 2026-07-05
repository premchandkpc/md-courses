# 11-Context-Mapping

Context Mapping describes the relationships and integration patterns between bounded contexts. Each relationship type defines a different level of coupling, autonomy, and translation. Choosing the right context map is a critical strategic DDD decision that shapes how microservices interact.

## Overview
Context maps are the "integration contract" between bounded contexts. Eric Evans defines several relationship patterns: Partnership (two teams coordinate jointly), Shared Kernel (shared subset of model), Customer-Supplier (upstream/downstream with negotiated contracts), Conformist (downstream accepts upstream's model without adaptation), Anti-Corruption Layer (ACL — downstream translates upstream model), Open-Host Service (well-defined published protocol), Separated Ways (no integration), and Big Ball of Mud (legacy mess). The choice depends on team autonomy needs, organizational structure, and system evolution requirements.

## Key Characteristics
- **Partnership**: Two teams coordinate on joint deliverables. High trust, frequent communication, reciprocal adaptation.
- **Shared Kernel**: A small, agreed-upon subset of the domain model shared across contexts. Changes require coordination.
- **Customer-Supplier**: Upstream context provides capabilities; downstream (customer) negotiates needs. Upstream wins if not contractually bound.
- **Conformist**: Downstream simply adopts upstream's model for simplicity. Fast integration, zero model ownership.
- **Anti-Corruption Layer (ACL)**: Downstream translates upstream's model into its own. Most defensive pattern — protects the downstream model's integrity.
- **Open-Host Service**: Upstream publishes a stable, versioned protocol (API/events). Many downstreams consume without special arrangements.
- **Separated Ways**: Contexts operate completely independently. No integration at all.

## Why It Matters
Context mapping choices determine microservice coupling. An ACL between services protects each service's independent evolution. A Shared Kernel may be appropriate for closely related services but creates coordination overhead. Choosing Conformist when downstream needs autonomy leads to technical debt. The context map should reflect both the technical integration and the organizational team boundaries (Conway's Law).

## Related Concepts
- [Bounded Context](03-Bounded-Context.md) — the contexts being mapped
- [Ubiquitous Language](02-Ubiquitous-Language.md) — translation occurs when languages differ across contexts
- [Domain Events](10-Domain-Events.md) — common mechanism for Open-Host Service pattern
- [DDD in Microservices](12-DDD-in-Microservices.md) — how context map shapes service architecture

---

## Mental Model
Context mapping is like international trade agreements between countries. Some countries form a close union (Shared Kernel) with shared standards. Some tightly coordinate on joint projects (Partnership). Some impose their standards and others adopt them (Conformist). The smart country builds a customs office (Anti-Corruption Layer) that translates foreign goods into local standards, protecting its internal economy from disruption.
