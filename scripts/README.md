# Running this

```
pip install -r requirements.txt
python run_competency_questions.py   # CQs 1-7, 10 as executable tests against ttl/instances_visit1.ttl
python validate_ontology.py          # structural checks backing ontology.md's Relation constraints / Validation
```

Optional, needs `pip install owlrl` on top of the above:

```
python materialize_involves.py       # shows exp:involves entailed via OWL2-RL, from the property chain
                                      # declared in ttl/ontology.ttl (hasParticipation o byActor)
```

All three were run against `ttl/ontology.ttl` + `ttl/instances_visit1.ttl` while writing them; every
assertion in `run_competency_questions.py` and `validate_ontology.py` matches the corresponding claim
in `../ontology.md`. If you edit the TTL, re-run both scripts — a red assertion means the prose and the
data have drifted apart.
