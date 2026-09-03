#!/usr/bin/env python3
"""Bonus / optional: materialize exp:involves via OWL2-RL reasoning.

ttl/ontology.ttl declares:

    exp:involves owl:propertyChainAxiom ( exp:hasParticipation exp:byActor ) .

meaning "Touchpoint involves Actor" is entailed wherever "Touchpoint
hasParticipation some Participation byActor that Actor" holds -- it's
never asserted directly in the instance data (one fact, one place: the
Participation records are the single source of truth for who was involved).

scripts/run_competency_questions.py deliberately queries hasParticipation/
byActor directly instead of relying on this, because a plain rdflib graph
doesn't run OWL entailment. This script shows the other side: run the
OWL2-RL closure (via owlrl) and confirm exp:involves triples appear.

Requires: pip install owlrl
"""

from pathlib import Path

from owlrl import DeductiveClosure, OWLRL_Semantics
from rdflib import Graph, Namespace
from rdflib.namespace import RDFS

HERE = Path(__file__).resolve().parent
TTL_DIR = HERE.parent / "ttl"

EXP = Namespace("http://example.org/experience-ontology#")


def main():
    g = Graph()
    g.parse(TTL_DIR / "ontology.ttl", format="turtle")
    g.parse(TTL_DIR / "instances_visit1.ttl", format="turtle")

    before = len(list(g.triples((None, EXP.involves, None))))
    print(f"exp:involves triples before reasoning: {before}")
    assert before == 0, "expected none asserted directly -- see module docstring"

    DeductiveClosure(OWLRL_Semantics).expand(g)

    after = list(g.triples((None, EXP.involves, None)))
    print(f"exp:involves triples after OWL2-RL closure: {len(after)}")
    for tp, _, actor in sorted(after, key=lambda t: (str(t[0]), str(t[2]))):
        tp_label = next(g.objects(tp, RDFS.label), tp)
        actor_label = next(g.objects(actor, RDFS.label), actor)
        print(f"  - {tp_label} involves {actor_label}")

    assert len(after) > 0, "property-chain reasoning did not fire"
    print("\nPASS -- exp:involves is correctly entailed from exp:hasParticipation/exp:byActor.")


if __name__ == "__main__":
    main()
