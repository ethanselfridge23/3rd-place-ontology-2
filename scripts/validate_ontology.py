#!/usr/bin/env python3
"""Structural checks that back up ontology.md's "Relation constraints" and
"Validation" sections with actual code, instead of leaving them as prose
claims. Exits non-zero and lists every violation if any check fails.

These are checks OWL's cardinality restrictions in ttl/ontology.ttl either
can't express at all (e.g. recoversFrom's target-must-be-Unmet rule, which
would need a role/status interaction axiom) or that a plain rdflib graph
can't verify without an OWL reasoner (the FunctionalProperty /
InverseFunctionalProperty declarations are just asserted here, not checked
by rdflib -- this script checks the data actually honors them).
"""

from collections import Counter
from pathlib import Path

from rdflib import RDF, Graph, Namespace
from rdflib.namespace import RDFS

HERE = Path(__file__).resolve().parent
TTL_DIR = HERE.parent / "ttl"

EXP = Namespace("http://example.org/experience-ontology#")


def load_graph() -> Graph:
    g = Graph()
    g.parse(TTL_DIR / "ontology.ttl", format="turtle")
    g.parse(TTL_DIR / "instances_visit1.ttl", format="turtle")
    return g


def lbl(g, node):
    return str(next(g.objects(node, RDFS.label), node))


def check_exactly_one_expectation(g: Graph):
    """Every Touchpoint has exactly one exp:hasExpectation (D2 / the OWL
    qualified-cardinality restriction on exp:Touchpoint)."""
    violations = []
    touchpoints = set(g.subjects(RDF.type, EXP.Touchpoint))
    for tp in touchpoints:
        n = len(list(g.objects(tp, EXP.hasExpectation)))
        if n != 1:
            violations.append(f"{lbl(g, tp)} has {n} Expectations, expected 1")
    return violations


def check_recovers_from_targets_unmet(g: Graph):
    """recoversFrom's target must have Expectation.status = Unmet (documented
    as a data-quality rule in ontology.ttl's comment on exp:recoversFrom,
    since it isn't expressible as a plain OWL restriction here)."""
    violations = []
    for recovery, failed in g.subject_objects(EXP.recoversFrom):
        expectation = g.value(failed, EXP.hasExpectation)
        status = g.value(expectation, EXP.status) if expectation else None
        if status != EXP.Unmet:
            violations.append(
                f"{lbl(g, recovery)} recoversFrom {lbl(g, failed)}, "
                f"but that Touchpoint's status is {lbl(g, status) if status else 'unset'}, not Unmet"
            )
    return violations


def check_contains_is_a_tree(g: Graph):
    """Each Touchpoint has at most one direct parent (contains's inverse,
    exp:isDirectChildOf, is declared owl:FunctionalProperty)."""
    violations = []
    parent_count = Counter()
    for parent, child in g.subject_objects(EXP.contains):
        parent_count[child] += 1
    for child, n in parent_count.items():
        if n > 1:
            violations.append(f"{lbl(g, child)} has {n} parents via exp:contains, expected at most 1")
    return violations


def check_next_forms_simple_chains(g: Graph):
    """exp:next is declared both FunctionalProperty (at most one next) and
    InverseFunctionalProperty (at most one predecessor) -- so a sibling
    group must form a simple chain, never a fork or a merge."""
    violations = []
    outgoing = Counter()
    incoming = Counter()
    for a, b in g.subject_objects(EXP.next):
        outgoing[a] += 1
        incoming[b] += 1
    for node, n in outgoing.items():
        if n > 1:
            violations.append(f"{lbl(g, node)} has {n} outgoing exp:next edges, expected at most 1")
    for node, n in incoming.items():
        if n > 1:
            violations.append(f"{lbl(g, node)} has {n} incoming exp:next edges, expected at most 1")
    return violations


def check_participation_round_trip(g: Graph):
    """exp:hasParticipation and exp:inTouchpoint are declared inverses in
    the TBox, but a plain graph doesn't infer the missing direction -- the
    instance data asserts both explicitly, so check they actually agree."""
    violations = []
    for tp, participation in g.subject_objects(EXP.hasParticipation):
        back = g.value(participation, EXP.inTouchpoint)
        if back != tp:
            violations.append(
                f"{participation} is hasParticipation of {lbl(g, tp)} "
                f"but its inTouchpoint points to {lbl(g, back) if back else 'nothing'}"
            )
    return violations


def check_recovers_from_is_irreflexive(g: Graph):
    """A Touchpoint can't recover from itself."""
    violations = []
    for a, b in g.subject_objects(EXP.recoversFrom):
        if a == b:
            violations.append(f"{lbl(g, a)} recoversFrom itself")
    return violations


CHECKS = [
    check_exactly_one_expectation,
    check_recovers_from_targets_unmet,
    check_contains_is_a_tree,
    check_next_forms_simple_chains,
    check_participation_round_trip,
    check_recovers_from_is_irreflexive,
]


def main():
    g = load_graph()
    print(f"Loaded {len(g)} triples. Running {len(CHECKS)} structural checks.\n")
    total_violations = 0
    for check in CHECKS:
        violations = check(g)
        status = "PASS" if not violations else "FAIL"
        summary = " ".join(check.__doc__.split())
        print(f"[{status}] {check.__name__}: {summary}")
        for v in violations:
            print(f"    - {v}")
        total_violations += len(violations)
    print()
    if total_violations:
        print(f"{total_violations} violation(s) found.")
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
