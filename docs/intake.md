# Offline genuine-fixture intake

This is intake tooling, not evidence collection or freeze approval. Actual admitted
corpus remains G=0/Y=0/R=0. It implements the collection protocol in the
[qualification report](/TEA/issues/TEA-9#document-qualification-report), revision
cdafcf80-29e7-4adb-a170-7885f385acd1, and preserves the
[decision packet](/TEA/issues/TEA-9#document-board-decision-packet) gates.

Copy `examples/intake-record-template.json` outside published staging. Null fields
are deliberately incomplete. Populate only from authorized original exports;
never fill missing settings from defaults, the current agent or guesses. The
schema is `schemas/intake-record.json`. Temperature accepts an explicitly recorded
finite JSON number, including fractional values. This separate intake format does
not change the citation canonicalization contract or rubric.

Preserve raw exports as bytes under an artifact root. Record SHA-256 over the whole
artifact and each half-open prompt/output byte span. Spans must be nonempty,
nonoverlapping and within the artifact. Schema-valid integral numeric offsets
(such as `7.0`) are normalized to integers for slicing; fractional offsets fail
per-record schema validation. Preserve prompt/output boundaries; include
request/response IDs, exporter, timestamp, source reference and access restrictions.
Settings evidence must reference the original explicitly recorded family, exact
version and temperature. Snapshot hash/pointer and inheritance chain record the
asserted API fact binding; source_span_ref identifies the derived snippet location.
Use `failure_class: "none"` when no failure is observed. No runtime validity or
hallucination frequency is inferred from snapshot presence.

```sh
python3 -m snapcite.intake --artifact-root /authorized/export/root \
  /private/intake/record-1.json /private/intake/record-2.json > /private/intake/report.json
python3 -m unittest discover -s tests -v
```

Install the repository's pinned requirements first. The command reads local JSON
and raw bytes only; it never imports, runs or fetches evidence. It prints JSON to
stdout. Exit 0 means every submitted record passed completeness/integrity checks;
exit 1 means at least one incomplete/invalid record; exit 2 means the command
could not read/parse its inputs. None is a development merge approval. Preserve
reports for rejected and pending records; no publication or private-history access
is authorized by this tool. Run only against the intended authorized artifact root.

The report separates three things:

- `complete`: schema metadata plus local artifact hash/span integrity. Missing
  metadata blocks admission, including green records. This cannot authenticate
  source ownership, model settings, timestamps, snapshot facts or curator identity.
- `admission`: recorded accepted curator and distinct independent reviewer claims
  are `recorded-admitted`; pending/rejected reviews remain visible. Authored tests
  are always excluded. Duplicate IDs and repeated entity/output observations are
  blocked to avoid inflated counts. Reviewer identities and source claims still
  require independent authentication outside this tool.
- `coverage`: counts only recorded admissions per exact entity and reports exact
  3 green / 2 yellow / 1 red separately. Counts never pool entities. This does not
  prove distinct green pathways, distinct yellow caution predicates or the most
  probable observed red hallucination. Those require curator evidence, observed
  frequencies, sampling denominator and limitations, plus independent replay.

`suite_qualified` is always false and `development_gate` is always blocked. Human
snapshot selection, redistribution basis, yellow-policy approval and final freeze
remain outstanding. Intake never writes canonical citations or changes the engine.

All records constructed by `tests/test_intake.py`, including copies temporarily
relabeled to exercise genuine-admission branches, are authored engineering data.
They are not original model outputs and cannot enter the genuine corpus. The
null template is not a fixture and must not be counted as one.

Observation identity uses the exact recorded `source_ref`, `request_id` and
`response_id`, plus the verified output SHA-256 (a content fingerprint of the
output bytes). Export path, whole-container hash and offsets do not distinguish
observations. Within a batch, only the first complete record for a given entity
and identical observation can count; subsequent copies are blocked. Conflicting
output hashes under a reused source/request/response identity block every complete
record in that identity group, across entities, pending curator reconciliation.
Do not rewrite source identifiers to bypass a conflict.

This check is batch-local: submit the whole candidate corpus together. Identical
content with different recorded source identities is not automatically deduplicated:
independent responses can match, and altered or aliased IDs cannot be authenticated
here. Curators and independent reviewers must adjudicate equivalent content,
source aliases, conflicting labels and source identity claims against original
exports before qualification. No such adjudication or provenance is invented by
the tool. Hash equality assumes SHA-256 collision resistance.
