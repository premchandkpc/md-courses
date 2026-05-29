# Discrete Mathematics — Foundations of Computing

The mathematical language of computer science. Discrete math underpins algorithms, data structures, cryptography, and all of computing theory.

## Set Theory

- **Sets**: unordered collection of distinct elements; notation `{1, 2, 3}`, empty set `∅`
- **Operations**: union `A ∪ B`, intersection `A ∩ B`, difference `A \ B`, complement `Aᶜ`, symmetric difference `A Δ B`
- **Power Set**: `𝒫(S)` — set of all subsets; `|𝒫(S)| = 2ⁿ`
- **Cartesian Product**: `A × B = {(a,b) | a∈A, b∈B}`; basis for relations and tuples
- **Cardinality**: finite vs infinite; countable (ℕ, ℚ) vs uncountable (ℝ); Cantor's diagonal argument
- **ZFC Axioms**: foundation of modern set theory; avoids Russell's paradox

## Combinatorics

- **Permutations**: ordered arrangements; `P(n,k) = n!/(n-k)!`
- **Combinations**: unordered selections; `C(n,k) = n!/(k!(n-k)!)` — binomial coefficient
- **Stars and Bars**: distributing n identical items into k bins: `C(n+k-1, k-1)`
- **Pigeonhole Principle**: if n items placed in m boxes and n > m, at least one box contains ≥2 items
- **Inclusion-Exclusion**: `|A ∪ B| = |A| + |B| - |A ∩ B|`; generalizes to n sets
- **Recurrence Relations**: Fibonacci `F(n) = F(n-1) + F(n-2)`, solving via characteristic equations
- **Generating Functions**: encode sequences as power series; closed forms for recurrences
- **Catalan Numbers**: `C_n = (1/(n+1))·C(2n,n)`; count BSTs, valid parentheses, triangulations

## Graph Theory

- **Fundamentals**: vertices (V), edges (E); directed vs undirected; simple graphs, multigraphs, hypergraphs
- **Connectivity**: paths, cycles, connected components; strongly connected (directed); articulation points and bridges
- **Eulerian Paths**: traverse every edge exactly once; exists iff 0 or 2 vertices have odd degree; Euler's theorem
- **Hamiltonian Paths**: visit every vertex exactly once; NP-complete to determine; Dirac's theorem (δ ≥ n/2)
- **Graph Coloring**: chromatic number χ(G); greedy coloring; Four Color Theorem (planar graphs need ≤4 colors)
- **Planar Graphs**: can be drawn without edge crossings; Euler's formula V - E + F = 2; Kuratowski's theorem (K₅ and K₃,₃)
- **Matching**: bipartite matching (Hopcroft-Karp); stable marriage (Gale-Shapley); Hall's marriage theorem
- **Trees**: connected acyclic graph; n nodes, n-1 edges; spanning trees; minimum spanning tree (Kruskal, Prim)

## Number Theory

- **Divisibility**: `a|b` if b = ka; gcd(a,b), lcm(a,b); Euclidean algorithm for GCD
- **Extended Euclidean Algorithm**: finds x,y such that `ax + by = gcd(a,b)`; computes modular inverses
- **Modular Arithmetic**: congruence `a ≡ b (mod m)`; residues Z/mZ; addition, multiplication, exponentiation
- **Chinese Remainder Theorem**: system of congruences with coprime moduli has unique solution modulo product
- **Euler's Totient**: φ(n) = count of integers < n coprime to n; φ(p) = p-1 for prime p
- **Fermat's Little Theorem**: `aᵖ⁻¹ ≡ 1 (mod p)` for prime p not dividing a
- **Miller-Rabin Test**: probabilistic primality testing; witnesses for compositeness
- **RSA Foundations**: trapdoor one-way function based on hardness of factoring; `c = mᵉ mod n`, `m = cᵈ mod n`

## Probability Theory

- **Fundamentals**: sample space Ω, events, probability axioms; `P(A) ∈ [0,1]`, `P(Ω)=1`, `P(A∪B)=P(A)+P(B)-P(A∩B)`
- **Conditional Probability**: `P(A|B) = P(A∩B)/P(B)`; independence `P(A∩B) = P(A)P(B)`
- **Bayes Theorem**: `P(A|B) = P(B|A)·P(A)/P(B)`; prior → likelihood → posterior
- **Random Variables**: discrete (Bernoulli, Binomial, Poisson) vs continuous (Uniform, Normal, Exponential)
- **Expectation & Variance**: `E[X] = Σx·P(x)`, `Var(X) = E[(X-μ)²]`; linearity of expectation
- **Law of Large Numbers**: sample mean converges to expected value as n → ∞
- **Central Limit Theorem**: sum of i.i.d. random variables approaches Normal distribution
- **Markov Chains**: states, transition matrix, stationary distribution; PageRank as stationary distribution

## Boolean Algebra & Logic

- **Boolean Operators**: AND (∧), OR (∨), NOT (¬), XOR (⊕), NAND, NOR; truth tables
- **Identities**: De Morgan's laws `¬(A∧B) = ¬A ∨ ¬B`, distributive, associative, commutative, absorption
- **Karnaugh Maps**: graphical minimization of Boolean expressions; grouping adjacent 1s; don't-care conditions
- **Propositional Logic**: atomic propositions, connectives, well-formed formulas; logical equivalence; inference rules (modus ponens, modus tollens)
- **Predicate Logic**: quantifiers ∀ (universal), ∃ (existential); predicates and functions; Skolemization

## Learning Path

1. Set theory and combinatorics (counting is the foundation)
2. Graph theory and number theory
3. Probability and statistics
4. Boolean algebra and logic
5. Recurrence relations and generating functions

**References**: CLRS (Appendix), Concrete Mathematics (Knuth), Introduction to Probability (Bertsekas), Discrete Mathematics and Its Applications (Rosen)
