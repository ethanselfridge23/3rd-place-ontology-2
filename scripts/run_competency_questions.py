#!/usr/bin/env python3
"""Run the competency questions from ontology.md as executable tests.

Loads ttl/ontology.ttl (TBox) and ttl/instances_visit1.ttl (the Worked
Example ABox) into a plain rdflib graph -- no OWL reasoner -- and answers
CQs 1-7 and 10 the same way they were verified by hand in ontology.md's
Validation section, so the doc's claims and this script can be checked
against each other.

Queries traverse the base asserted relations (exp:hasParticipation /
exp:byActor, not the entailed exp:involves shortcut) because a plain
rdflib graph doesn't run the owl:propertyChainAxiom declared on
exp:involves in ontology.ttl. See scripts/materialize_involves.py for a
version that does materialize it, using owlrl.

CQs 8 and 9 need a population of many visits, not one -- this repo only
ships one Worked Example, so they're left as documented gaps.
"""

from pathlib import Path

from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDFS

HERE = Path(__file__).resolve().parent
TTL_DIR = HERE.parent / "ttl"

EXP = Namespace("http://example.org/experience-ontology#")
RDFS_LABEL = RDFS.label


def load_graph() -> Graph:
    g = Graph()
    g.parse(TTL_DIR / "ontology.ttl", format="turtle")
    g.parse(TTL_DIR / "instances_visit1.ttl", format="turtle")
    return g


def find_by_label(g: Graph, text: str):
    return next(g.subjects(RDFS_LABEL, Literal(text)))


def cq1(g: Graph):
    print("\nCQ1: What are all the sub-touchpoints of 'Order a Drink'?")
    q = """
    PREFIX exp: <http://example.org/experience-ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?label WHERE {
      ?root rdfs:label "Order a Drink" .
      ?root exp:contains+ ?descendant .
      ?descendant rdfs:label ?label .
    } ORDER BY ?label
    """
    rows = [str(r.label) for r in g.query(q)]
    for r in rows:
        print(f"  - {r}")
    assert len(rows) == 8, f"expected 8 descendants, got {len(rows)}"
    print("  PASS (8 descendants)")


def cq2(g: Graph):
    print("\nCQ2: Which touchpoints does the bartender actively participate in, "
          "vs. just the customer?")
    q = """
    PREFIX exp: <http://example.org/experience-ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?tpLabel ?actorLabel WHERE {
      ?p exp:byActor ?actor ; exp:inTouchpoint ?tp .
      ?tp rdfs:label ?tpLabel .
      ?actor rdfs:label ?actorLabel .
      FILTER(?actorLabel IN ("Bartender", "Customer"))
    } ORDER BY ?tpLabel ?actorLabel
    """
    by_tp = {}
    for r in g.query(q):
        by_tp.setdefault(str(r.tpLabel), set()).add(str(r.actorLabel))
    for tp, actors in sorted(by_tp.items()):
        print(f"  - {tp}: {sorted(actors)}")
    bartender_absent = [tp for tp, actors in by_tp.items() if "Bartender" not in actors]
    print(f"  Bartender absent from: {sorted(bartender_absent)}")
    assert set(bartender_absent) == {"Approach Bar", "Get Bartender's Attention"}
    print("  PASS")


def cq3(g: Graph):
    print("\nCQ3: Which touchpoints had an unmet Expectation?")
    q = """
    PREFIX exp: <http://example.org/experience-ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?label WHERE {
      ?tp exp:hasExpectation ?e .
      ?e exp:status exp:Unmet .
      ?tp rdfs:label ?label .
    } ORDER BY ?label
    """
    rows = sorted(str(r.label) for r in g.query(q))
    for r in rows:
        print(f"  - {r}")
    assert rows == sorted([
        "Order a Drink", "Get Bartender's Attention", "Drink is Made", "Receive Drink",
    ])
    print("  PASS")


def cq4(g: Graph):
    print("\nCQ4: What emotion did the customer feel at each touchpoint?")
    q = """
    PREFIX exp: <http://example.org/experience-ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?tpLabel ?emotionLabel WHERE {
      ?p exp:byActor ?actor ; exp:inTouchpoint ?tp ; exp:withEmotion ?em .
      ?actor rdfs:label "Customer" .
      ?tp rdfs:label ?tpLabel .
      ?em rdfs:label ?emotionLabel .
    } ORDER BY ?tpLabel
    """
    rows = [(str(r.tpLabel), str(r.emotionLabel)) for r in g.query(q)]
    for tp, em in rows:
        print(f"  - {tp}: {em}")
    assert len(rows) == 6, f"expected 6 customer-emotion pairs, got {len(rows)}"
    print("  PASS")


# Emotion valence is a query-time judgment call, not part of the ontology --
# see ontology.md D6/D9 discussion; nothing in ttl/ontology.ttl classifies
# emotions as positive/negative, deliberately (no CQ needed it as a formal
# field until this one, and it's a heuristic label, not a fact about the
# Emotion individual itself).
NEGATIVE_EMOTIONS = {"impatient", "disappointed", "unaware", "anxious", "apologetic"}


def _next_of(g: Graph, node):
    return g.value(node, EXP["next"])


def _children_of(g: Graph, node):
    return list(g.objects(node, EXP["contains"]))


def cq5(g: Graph):
    print("\nCQ5: Where did the customer's emotion first turn negative?")
    root = find_by_label(g, "Order a Drink")
    ordered = []
    # find head of the top-level chain (the child with no incoming `next`)
    children = _children_of(g, root)
    targets = {_next_of(g, c) for c in children}
    node = next(c for c in children if c not in targets)
    while node is not None:
        ordered.append(node)
        node = _next_of(g, node)

    q = """
    PREFIX exp: <http://example.org/experience-ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?emotionLabel WHERE {
      ?p exp:byActor ?actor ; exp:inTouchpoint ?tp ; exp:withEmotion ?em .
      ?actor rdfs:label "Customer" .
      ?em rdfs:label ?emotionLabel .
    }
    """
    first_negative = None
    for tp in ordered:
        row = g.query(q, initBindings={"tp": tp})
        for r in row:
            em = str(r.emotionLabel)
            tp_label = str(next(g.objects(tp, RDFS_LABEL)))
            flag = " <-- first negative" if em in NEGATIVE_EMOTIONS and first_negative is None else ""
            print(f"  - {tp_label}: {em}{flag}")
            if em in NEGATIVE_EMOTIONS and first_negative is None:
                first_negative = tp_label
    assert first_negative == "Get Bartender's Attention"
    print(f"  PASS (first negative turn: {first_negative})")


def cq6(g: Graph):
    print("\nCQ6: When an Expectation goes unmet, what recovery Touchpoint follows?")
    q = """
    PREFIX exp: <http://example.org/experience-ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?recoveryLabel ?failedLabel WHERE {
      ?recovery exp:recoversFrom ?failed .
      ?recovery rdfs:label ?recoveryLabel .
      ?failed rdfs:label ?failedLabel .
    } ORDER BY ?recoveryLabel
    """
    rows = [(str(r.recoveryLabel), str(r.failedLabel)) for r in g.query(q)]
    for recovery, failed in rows:
        print(f"  - {recovery} recovers from {failed}")
    assert len(rows) == 3 and all(f == "Receive Drink" for _, f in rows)
    print("  PASS")


def _last_in_chain(g: Graph, node):
    while True:
        nxt = _next_of(g, node)
        if nxt is None:
            return node
        node = nxt


def _chain_head(g: Graph, siblings):
    siblings = list(siblings)
    targets = {_next_of(g, s) for s in siblings}
    heads = [s for s in siblings if s not in targets]
    return heads[0] if heads else siblings[0]


def _last_touchpoint_in_subtree(g: Graph, node):
    tail = _last_in_chain(g, node)
    children = _children_of(g, tail)
    if not children:
        return tail
    head = _chain_head(g, children)
    return _last_touchpoint_in_subtree(g, head)


def cq7(g: Graph):
    print("\nCQ7: Can a visit have an unmet Expectation but still end with a "
          "positive customer Emotion (service recovery)?")
    root = find_by_label(g, "Order a Drink")

    any_unmet = (root, EXP["hasExpectation"], None) in g and any(
        g.value(e, EXP["status"]) == EXP["Unmet"]
        for _, _, e in g.triples((None, EXP["hasExpectation"], None))
    )

    last_tp = _last_touchpoint_in_subtree(g, root)
    last_label = str(next(g.objects(last_tp, RDFS_LABEL)))
    q = """
    PREFIX exp: <http://example.org/experience-ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?emotionLabel WHERE {
      ?p exp:byActor ?actor ; exp:inTouchpoint ?tp ; exp:withEmotion ?em .
      ?actor rdfs:label "Customer" .
      ?em rdfs:label ?emotionLabel .
    }
    """
    row = list(g.query(q, initBindings={"tp": last_tp}))
    last_emotion = str(row[0].emotionLabel) if row else None

    print(f"  Some Expectation in this visit is Unmet: {any_unmet}")
    print(f"  Last Touchpoint reached (next+contains traversal): {last_label}")
    print(f"  Customer's Emotion there: {last_emotion}")
    assert last_label == "Receive Corrected Drink"
    assert last_emotion == "relieved"
    print("  PASS (unmet earlier, positive by the end -- service recovery holds)")


def cq10(g: Graph):
    print("\nCQ10: Does every Touchpoint have exactly one Expectation?")
    q = """
    PREFIX exp: <http://example.org/experience-ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?tp (COUNT(?e) AS ?n) WHERE {
      ?tp a exp:Touchpoint .
      OPTIONAL { ?tp exp:hasExpectation ?e }
    } GROUP BY ?tp
    """
    violations = [(r.tp, int(r.n)) for r in g.query(q) if int(r.n) != 1]
    if violations:
        for tp, n in violations:
            print(f"  - VIOLATION: {tp} has {n} Expectations")
    else:
        print("  All Touchpoints have exactly one Expectation.")
    assert not violations
    print("  PASS")


def main():
    g = load_graph()
    print(f"Loaded {len(g)} triples.")
    cq1(g)
    cq2(g)
    cq3(g)
    cq4(g)
    cq5(g)
    cq6(g)
    cq7(g)
    cq10(g)
    print("\nAll tested competency questions pass against the Worked Example.")


if __name__ == "__main__":
    main()
