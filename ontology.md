# Cocktail Bar Ordering Experience Ontology

## Purpose

Model the experience of ordering a drink at a cocktail bar so that any moment
in the visit — good or bad — can be described the same way: as a
**Touchpoint**, who was actively part of it, what standard it was held to,
whether that standard was met, and how the people in it felt.

Consumers: humans mapping/reviewing the experience (e.g. a bar manager, a
service designer). Not yet scoped for agent read/write or multi-source
provenance — see Decision Log, D8.

## Entities

- **Touchpoint** — a discrete, nameable moment in the experience. May
  decompose into child Touchpoints (recursive). Every Touchpoint you'll ever
  see in an instance tree *is* one occurrence in one visit — there is no
  separate class layer (see D7).
  - `label` (string) — the name of the moment, e.g. "Place Order". Shared
    across occurrences of "the same kind" of moment in different visits, so
    occurrences can be grouped/aggregated by label without a separate class
    entity.

- **Actor** — a participant that *actively participates* in a Touchpoint
  (not merely present — D3). Actor is flattened with Role: no separate Role
  entity (D1). This is *not* a permanent type on a person — an Actor only
  exists scoped to one Touchpoint's `involves` edge, so it doesn't fall into
  the classic trap of rigidly subclassing a role (e.g. "Bartender" as a fixed
  kind of person) as if it were a permanent type. The same real person could
  be a "Bartender" Actor in one Touchpoint and a "Cashier" Actor in another,
  with no shared identity between the two — that's the accepted cost in D1.
  - `label` (string) — e.g. "Bartender", "Customer".

- **Expectation** — the standard a Touchpoint is judged against. Exactly one
  per Touchpoint (D2).
  - `statement` (string) — e.g. "Acknowledged within ~30 seconds."
  - `status` (enum: `Met` | `Unmet`) — whether this occurrence's Expectation
    was satisfied (D6).

- **Emotion** — how a specific Actor felt during a specific Touchpoint.
  Inheres in the Actor, not the Touchpoint, and is scoped to the pairing of
  the two (D4) — the same Actor can feel differently at different
  Touchpoints, and two Actors at the same Touchpoint can feel differently.
  - `label` (string) — e.g. "frustrated", "relieved", "focused".

## Relations

| Relation | From → To | Cardinality | Meaning |
|---|---|---|---|
| `contains` | Touchpoint → Touchpoint | 0..* | Direct structural nesting (parent→child, one level). |
| `next` | Touchpoint → Touchpoint | 0..1 | Points to the following sibling. |
| `recoversFrom` | Touchpoint → Touchpoint | 0..1 | Points back to the Touchpoint whose Unmet Expectation triggered this one. |
| `involves` | Touchpoint → Actor | 0..* | Who actively participated. |
| `involves.Emotion` | (Touchpoint, Actor) → Emotion | 0..1 | The Actor's felt state during that specific Touchpoint — an attribute of the *involvement*, not of either endpoint alone. |
| `has` | Touchpoint → Expectation | exactly 1 | The standard this occurrence is judged against. |

### Relation constraints

Stated explicitly to avoid the "incomplete relation declaration" trap (an algebraic
property left implicit and assumed inconsistently later):

- **`contains` is not transitive as stored** — it holds only between a Touchpoint
  and its immediate children. "All sub-touchpoints of X" (CQ 1) is the
  *transitive closure* of `contains`, computed at query time — never stored
  redundantly (core principle 3: one fact, one place). Inverse-functional: a
  Touchpoint has at most one direct parent (the structure is a tree, not a DAG).
- **`next` is functional and injective**, and only defined between two
  Touchpoints that share the same parent via `contains` — it orders siblings,
  it does not create a global timeline across the whole tree. Not transitive as
  stored; "what comes after X, eventually" is again a computed closure.
- **`recoversFrom` is irreflexive and not symmetric.** Its target must be a
  Touchpoint whose `Expectation.status = Unmet` — a recovery Touchpoint always
  points at a failure. It *can* chain (a failed recovery attempt spawning a
  second recovery), so treat it as a directed acyclic path, not assume
  single-hop.
- **`has` is inverse-functional and existence-dependent**: an Expectation
  belongs to exactly one Touchpoint and has no identity or reuse apart from it
  (this is why Expectation stayed a separate construct rather than being
  flattened into two plain Touchpoint attributes — see Validation).

## Decision Log

Each entry: the call made, and its accepted cost.

- **D1 — Actor = Role, flattened.** No separate Role entity; an Actor's
  label doubles as its role in that Touchpoint. *Cost:* if the same person
  plays different roles across Touchpoints (e.g. "Bartender" vs "Cashier"),
  that's just two different Actor labels — there's no way to say "these are
  the same person."
- **D2 — Expectation is singular per Touchpoint.** One statement, not a set.
  *Cost:* can't represent "timing expectation" and "quality expectation"
  separately at one Touchpoint — a Touchpoint needing both must be split
  into two Touchpoints.
- **D3 — Actor means actively participates**, not merely present. *Cost:*
  a passive bystander (e.g. Customer watching "Drink is Made") is not
  recorded as an Actor there at all — presence alone leaves no trace.
- **D4 — Emotion is scoped to (Touchpoint × Actor)**, not to the Touchpoint
  alone. *Cost:* one more thing to read at each node than a single
  Touchpoint-level Emotion would be.
- **D5 — Failure is not a separate entity type.** An existing Touchpoint can
  simply have `Expectation.status = Unmet`; a *new* Touchpoint (e.g.
  "Customer Flags the Mistake") is used only when a genuinely new
  moment — with its own Actors and Expectation — occurs as a consequence.
  *Cost:* judgment call each time about whether a bad outcome is "the same
  Touchpoint, unmet" or "a new Touchpoint."
- **D6 — Expectation.status is a formal enum field** (`Met`/`Unmet`), not
  left implicit in prose. *Cost:* binary only — no partial-credit status
  (e.g. "technically met but slow"); that would need a third value or a
  scalar, deferred until a competency question actually needs it.
- **D7 — No separate class/instance layer.** A Touchpoint node in a tree
  *is* one occurrence; `label` is what lets you group occurrences of "the
  same kind of moment" across different visits (e.g. for CQ 9). *Cost:*
  nothing enforces that two Touchpoints with the same label actually have
  matching Expectation statements or Actor sets — that consistency is a
  discipline, not a constraint.
- **D8 — No provenance/statement layer, no agent-actionability layer.**
  Facts (status, Emotion) are stipulated directly, not sourced or
  attributed. *Cost:* if multiple observers could disagree about whether an
  Expectation was met, or an emotion, there's nowhere to record that
  disagreement — revisit if this ontology ever needs to merge conflicting
  accounts of the same visit, or be written to by an agent.
- **D9 — `next` and `recoversFrom` added** to close CQ 5 (ordering) and
  CQ 6 (recovery linkage). Both optional, both point Touchpoint→Touchpoint.
  *Cost:* `next` only orders siblings under the same parent — no global
  timeline across the whole tree without walking it.
- **D10 — A parent Touchpoint's `Expectation.status` is independently
  stipulated, not mechanically derived from its children's statuses.**
  "Order a Drink" can legitimately be judged Unmet even if every child
  eventually shows Met (a slow, joyless but technically correct visit), or
  judged salvaged even with real failures inside it (the service-recovery
  case in the Worked Example). *Cost:* nothing enforces consistency between
  a parent's status and its children's — that judgment call is left to
  whoever populates the instance, which is a deliberate choice (D5's
  judgment-call pattern extended upward), not an oversight.

## Competency Questions

Each "Tested" row was actually run against the Worked Example below, not just
judged answerable in principle (avoids the "untested CQ catalogue"
anti-pattern — see Validation).

| # | Question | Status |
|---|---|---|
| 1 | What are all the sub-touchpoints that make up "Order a Drink"? | **Tested** — transitive closure of `contains` over the Worked Example returns all 8 descendant Touchpoints. |
| 2 | Which touchpoints does the bartender actively participate in, vs. just the customer? | **Tested** — Bartender is in `involves` for Place Order, Drink is Made, Receive Drink, and all three recovery Touchpoints; absent from Approach Bar and Get Bartender's Attention. |
| 3 | Which touchpoints in a given visit had an unmet Expectation? | **Tested** — Order a Drink (root), Get Bartender's Attention, Drink is Made, Receive Drink. |
| 4 | What emotion did the customer feel at each touchpoint of a visit? | **Tested** — read directly off `involves.Emotion` for the Customer at each node in the Worked Example. |
| 5 | Where in a visit did the customer's emotion first turn negative? | **Tested** — walking `next` at the top level: Approach Bar (hopeful) → Get Bartender's Attention (hopeful → impatient) is the first negative turn. |
| 6 | When a Touchpoint's Expectation goes unmet, what recovery Touchpoint (if any) follows it? | **Tested** — all three recovery Touchpoints carry `recoversFrom → Receive Drink`. |
| 7 | Can a visit have an unmet Expectation but still end with a positive customer Emotion (service recovery)? | **Tested**, with a correction: "the last Touchpoint" is not a single `next` chain — you have to follow `next` to the last sibling *and then descend into its children* via `contains`, repeating until a node has neither, since the recovery branch is nested under "Receive Drink," not chained after it at the top level. That combined traversal lands on "Receive Corrected Drink" — Customer: relieved — despite two Unmet Expectations earlier in the same visit. |
| 8 | Which Actor is most often absent from a Touchpoint's Actor set when Expectation is unmet? | Not yet testable — one visit isn't enough data for a meaningful frequency answer; needs a real population. |
| 9 | For a given Touchpoint label (e.g. "Drink is Made"), across many visits, what fraction of occurrences are Unmet? | Not yet testable — same reason as #8. |
| 10 | Does every Touchpoint have exactly one Expectation, even new recovery ones? | **Tested** — all 9 nodes in the Worked Example (root + 8 descendants) carry exactly one Expectation. |

## Worked Example

One visit, walked start to finish. `→` is `next`. Indentation is `contains`.
Each entry: Actors (with Emotion), Expectation (with status).

```
Order a Drink  [label: "Order a Drink"]
  Expectation: "Customer leaves with the drink they wanted, feeling
                attended to." — Unmet (see below)

  → Approach Bar
      Actors: Customer (hopeful), Host (welcoming)
      Expectation: "Finds an open spot within a reasonable wait." — Met

  → Get Bartender's Attention
      Actors: Customer (hopeful → growing impatient)
        (Bartender is NOT an Actor here — never actively engages)
      Expectation: "Acknowledged within ~30 seconds." — Unmet

  → Place Order
      Actors: Customer (relieved), Bartender (attentive)
      Expectation: "Order understood and confirmed back correctly." — Met

  → Drink is Made
      Actors: Bartender (focused)
      Expectation: "Matches order, correct, reasonable time." — Unmet
        (wrong drink made; unnoticed by anyone yet — no Emotion recorded,
         no Actor was present to react)

  → Receive Drink
      Actors: Customer (disappointed), Bartender (unaware)
      Expectation: "Correct drink, clear handoff." — Unmet

      → Customer Flags the Mistake   [recoversFrom: "Receive Drink"]
          Actors: Customer (anxious, hopeful), Bartender (apologetic)
          Expectation: "Concern is heard and taken seriously." — Met

      → Drink Remade   [recoversFrom: "Receive Drink"]
          Actors: Bartender (eager to make it right)
          Expectation: "Corrected quickly and matches order." — Met

      → Receive Corrected Drink   [recoversFrom: "Receive Drink"]
          Actors: Customer (relieved), Bartender (relieved)
          Expectation: "Resolution feels genuine, not grudging." — Met
```

Reading CQ 7 off this tree: the visit had two Unmet Expectations along the
way, but the last Touchpoint's Customer Emotion is "relieved" — a concrete
instance of the service-recovery pattern the model was built to represent.

## Validation

A pass against the anti-pattern catalogue and Gruber's design criteria,
run against the model as it stands (not asserted, checked):

**Taxonomic/logical checks — clean.** No circularity, no class standing in
for both a type and one of its instances, no rigid class subsuming an
anti-rigid role (Actor was checked specifically for this, see its
definition), no orphaned constructs (Emotion connects via `involves`; all
four entities and five relations trace back to the core loop), every
relation's domain/range and algebraic properties are now stated (Relation
constraints section — this was the one real gap the sweep found, now fixed).

**One deliberate design call surfaced by the sweep, not changed:**
Expectation could be flattened into two plain attributes on Touchpoint
(`expectationStatement`, `expectationStatus`) instead of staying a separate
construct — it has no identity, history, or relations of its own beyond its
one Touchpoint. Kept as a separate construct anyway, because `has` is
already declared existence-dependent and inverse-functional (Relation
constraints), so nothing is lost by the extra construct, and it keeps the
door open if a future CQ ever needs to reason about Expectations
independently of their Touchpoint (e.g. "list every distinct Expectation
statement in use"). Purpose decided this one, not correctness — both are
valid models (core principle 5).

**Structural/scale anti-patterns — not yet applicable.** Kitchen Sink, Golden
Hammer, God Object, and Center-of-Excellence risks mostly bite as an
ontology grows past one team/one use — worth re-running this checklist if
the model gets consumers beyond this document.

**Process anti-patterns:**
- *Untested CQ catalogue* — was present (CQs 1–7 and 10 were marked
  "Answerable" without being run); fixed by actually executing each against
  the Worked Example (see Competency Questions table).
- *Silent redundancy between a parent's status and its children's* — a real
  risk once `Expectation.status` exists at every level of a tree (root and
  leaves both have it). Resolved by D10: the parent's status is declared
  independently stipulated, not derived, so it isn't a silently-duplicated
  fact — it's a distinct fact by design, and that's now recorded rather than
  implicit.
- *Orthogonal axes collapsed into one enum* — checked `Expectation.status`
  specifically for this, since it's the newest formal field: it only
  encodes one axis (was the standard met), not conflated with severity,
  confidence, or who judged it. Clean for now; would need revisiting if a
  future CQ wants "how badly unmet."

**Gruber's five criteria — quick score:** Clarity and coherence are carried
by the Decision Log (every non-obvious call has a stated rationale and
cost); extendibility is demonstrated in practice by D9 (added `next` and
`recoversFrom` without touching the four original entities); minimal
encoding bias holds — nothing here assumes a particular database or file
format; minimal ontological commitment holds — D8 explicitly declined
provenance and agent-actionability layers neither current CQ needs.
