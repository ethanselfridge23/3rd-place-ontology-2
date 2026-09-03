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
  entity (D1).
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
| `contains` | Touchpoint → Touchpoint | 0..* | Structural nesting (recursive). |
| `next` | Touchpoint → Touchpoint | 0..1 | Points to the following sibling — orders occurrences within the same parent (D9, closes CQ 5). |
| `recoversFrom` | Touchpoint → Touchpoint | 0..1 | Points back to the Touchpoint whose Unmet Expectation triggered this one. Only set on recovery Touchpoints (D9, closes CQ 6). |
| `involves` | Touchpoint → Actor | 0..* | Who actively participated. Each involvement optionally carries one `Emotion` — the Actor's felt state during that Touchpoint. |
| `has` | Touchpoint → Expectation | exactly 1 | The standard this occurrence is judged against, and whether it was met. |

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

## Competency Questions

| # | Question | Status |
|---|---|---|
| 1 | What are all the sub-touchpoints that make up "Order a Drink"? | Answerable — `contains` |
| 2 | Which touchpoints does the bartender actively participate in, vs. just the customer? | Answerable — `involves` |
| 3 | Which touchpoints in a given visit had an unmet Expectation? | Answerable — `Expectation.status` |
| 4 | What emotion did the customer feel at each touchpoint of a visit? | Answerable — `Emotion` on `involves` |
| 5 | Where in a visit did the customer's emotion first turn negative? | Answerable — `next` gives ordering to walk |
| 6 | When a Touchpoint's Expectation goes unmet, what recovery Touchpoint (if any) follows it? | Answerable — `recoversFrom` |
| 7 | Can a visit have an unmet Expectation but still end with a positive customer Emotion (service recovery)? | Answerable by walking `next` to the last Touchpoint and reading its Emotion — no separate visit-level rollup field. Open: is a rollup ever needed, or is "walk to the end" good enough? |
| 8 | Which Actor is most often absent from a Touchpoint's Actor set when Expectation is unmet? | Answerable in principle; needs a real population of instances (not just one illustrative visit) to be a meaningful query. |
| 9 | For a given Touchpoint label (e.g. "Drink is Made"), across many visits, what fraction of occurrences are Unmet? | Answerable — group occurrences by `label`, once multiple visits are populated. |
| 10 | Does every Touchpoint have exactly one Expectation, even new recovery ones? | Self-consistency check, not stakeholder-facing — run once instances are populated. |

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
