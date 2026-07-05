# 17-Google

Google's engineering practices — Borg/Kubernetes for orchestration, gRPC for service communication, Protocol Buffers for serialization, SRE for operations, and the monorepo approach — have shaped the infrastructure patterns used across the industry.

## Problem
Google built a global-scale infrastructure long before cloud was mainstream. They needed to run thousands of services (Search, Gmail, Maps, YouTube, Ads) on a shared pool of machines while maintaining resource efficiency, reliability, and fast developer iteration. No off-the-shelf systems met these requirements.

## Architecture
- **Borg → Kubernetes**: Borg was Google's internal cluster manager (2003) — it scheduled jobs (bin-packing), handled failure (restarting tasks), managed resources (CPU/memory quotas), and provided service discovery. Kubernetes (2014) was the open-source reimagining of Borg's principles, targeting cloud-native applications.
- **gRPC and Protocol Buffers**: Protocol Buffers (protobuf) are Google's language-neutral serialization format — smaller, faster, and more type-safe than JSON. gRPC uses protobuf for service definitions and provides bidirectional streaming, flow control, and pluggable auth. It's the standard for Google's internal service communication (10B+ RPCs/sec).
- **Monorepo**: Google manages a single repository with billions of lines of code and thousands of projects. All code is visible to all engineers. Refactoring across projects is done atomically. Tools (Bazel build system, code search, Tricorder static analysis) make the monorepo practical.
- **SRE (Site Reliability Engineering)**: Software engineers focused on operations — they write code to automate operational tasks. Key concepts: error budgets (100% reliability is wrong target), SLIs/SLOs/SLAs, toil reduction, blameless postmortems, and incident management.
- **Spanner**: Google's globally-distributed SQL database with external consistency (linearizability) and synchronous replication across regions. The TrueTime API (GPS + atomic clocks) enables consistent reads and writes without the performance penalty of traditional distributed coordination.

## Lessons Learned
- **Abstraction enables innovation**: Borg abstracted away individual machines, allowing Google to treat the data center as one big computer. Kubernetes brought this abstraction to the industry. The right abstraction level dramatically reduces operational complexity.
- **SRE is a mindset, not a role**: The principles of SRE (treat operations as a software problem, measure everything, automate toil, use error budgets) apply to any engineering organization. Even small teams benefit from SLOs and blameless culture.
- **Monorepo works at scale but tooling is critical**: Without the right tools (build system, code search, static analysis, ownership tracking), a monorepo becomes unmanageable. Most organizations benefit from multi-repo or a hybrid approach.
- **Open-source as strategic**: Kubernetes, gRPC, protobuf, TensorFlow, Android — Google open-sources core infrastructure to create ecosystems, drive adoption of their standards, and benefit from community contributions.

## Related Concepts
- [17-Netflix](17-Netflix.md) — Contrasting approaches to resilience (Google's SRE vs Netflix's chaos engineering)
- [03-Netflix](../15-System-Design/03-Netflix.md) — Video streaming infrastructure comparison

---

## Mental Model
Google's approach is like building a city where every building (service) connects through standardized utility pipes (gRPC) carrying standardized electricity packets (protobuf). The city planner (Borg/Kubernetes) decides which buildings go where and allocates resources. The buildings all share a library of building codes (monorepo), making cross-building renovations easier. Fire inspectors (SRE) continuously measure response times and budget for acceptable failure rates.
