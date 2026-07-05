# 07-Staff-Level-Discussions

Staff+ engineering discussions cover organizational design, technical strategy, migration planning, incident reviews, and architecture governance — the high-leverage work that senior individual contributors drive.

## Organizational Design
- **Two-pizza teams**: Teams of 6-10 people owning a business capability (not a technical layer). Each team is cross-functional (product, engineering, QA, ops). Team owns their services end-to-end — build, test, deploy, monitor, on-call.
- **Conway's Law awareness**: System architecture mirrors communication structure. If teams are organized by layer (frontend team, backend team, DB team), the architecture will be layered. If organized by business domain (payments team, catalog team), the architecture will be domain-oriented.
- **Team topology**: Stream-aligned teams (own a business flow), enabling teams (provide tools/platforms), complicated-subsystem teams (own a complex domain like search/recommendations), platform teams (provide infrastructure). Choose the topology that matches the organization's maturity.
- **Service ownership model**: Each service has a clearly defined owner (team), SLOs, and on-call rotation. Ownership is not shared. If a service needs multiple teams to change it, split the service or formalize a platform model.

## Technical Strategy
- **Migration planning (Strangler Fig)**: Extract functionality incrementally while the monolith still runs. Route traffic between old and new implementations using feature flags or a routing layer. Every extraction should be reversible (feature flag off → old path). Measure success by deploy frequency and incident rate.
- **Technology adoption framework**: Convince with data, not authority. Build a prototype demonstrating the value. Write a technical RFC covering the problem, alternatives, tradeoffs, migration plan, and success criteria. Socialize the RFC widely before implementation.
- **Deprecation strategy**: Every new service or API should include a deprecation plan from day one. Sunset headers for APIs. Maintain backward compatibility for a minimum period (6-12 months). Use feature flags to gradually roll out replacements. Remove old code paths when usage drops below a threshold.
- **Architecture decision records (ADRs)**: Document significant architecture decisions with context, alternatives considered, the decision, and consequences. Store ADRs in the repository. They serve as institutional memory for future engineers.

## Incident Reviews and Learning
- **Blameless postmortems**: Focus on system failures, not individual mistakes. Every incident reveals a gap in the system's defenses. Ask "what prevented the system from handling this gracefully?" rather than "who made the mistake?"
- **Action item quality**: Each postmortem action item should prevent a class of failures, not just one instance. Adding a null check prevents one bug; adding a schema validation layer prevents a class of bugs.
- **Incident metrics**: Track MTTD (mean time to detect), MTTR (mean time to resolve), and incident frequency. Trend these over time. Improving MTTD often starts with better monitoring and alerting. Improving MTTR starts with runbooks and automation.
- **Game days**: Regularly scheduled failure simulations. The team practices responding to incidents in a controlled environment. Builds muscle memory. Uncovers gaps in monitoring, runbooks, and communication channels.

## Senior Engineering Behaviors
- **Saying no effectively**: Not every good idea should be implemented. Evaluate proposals against the team's strategy and capacity. Provide clear reasoning for rejection and suggest alternatives or conditions for revisiting.
- **Leveling up others**: Code reviews that explain the "why" not just the "what". Mentoring through paired debugging sessions. Writing documentation that captures context, not just API specs. Delegating high-visibility work to junior engineers.
- **Balancing speed and quality**: Understand when to take shortcuts (prototypes, experiments) and when to invest in quality (foundation infrastructure, security-critical code). Communicate the tradeoff explicitly — "I'm shipping this as a quickfix with tech debt that we should address in Q3."

## Related Concepts
- [03-Architecture-Questions](03-Architecture-Questions.md) — Architectural reasoning at scale
- [05-Production-Issues](05-Production-Issues.md) — Patterns for improving reliability
- [06-Trade-Offs](06-Trade-Offs.md) — Frameworks for evaluating architectural decisions

---

## Mental Model
A staff engineer is like a city planner, not a contractor. The contractor builds individual buildings (features). The city planner decides road layouts (architecture), zoning laws (standards), transportation systems (platforms), and growth strategy (migration plan). The city planner doesn't build any single building but makes all buildings work together as a coherent, growing city.
