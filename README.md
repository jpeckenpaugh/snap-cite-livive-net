# Snap Cite

Offline grounding reports for explicit Roblox API presence claims. The frozen
[concept](concept.md) is preserved. This implementation is **development staging,
not freeze qualified**. No curated entity suite, day-01 snapshot or yellow CI
policy has been approved.

See [contract](docs/contract.md), [snapshot inspection](docs/snapshot-candidate.md),
and the static [staging artifacts](staging/README.md). No web application is included.

## Reproduce

Python 3.13 was tested. Install `python -m pip install -r requirements.txt` in an
isolated environment. From the repository root:

```sh
python -m unittest discover -s tests -v
PYTHONPATH=. python scripts/make-example.py
python -m snapcite build --manifest build/manifest.json \
  --touchstone build/touchstone.json --snapshot examples/development-snapshot.json \
  --repo . --out build/citations --trust TOUCHSTONE_HASH_PRINTED_ABOVE --pdf
python -m snapcite replay build/citations/MANIFEST_HASH --trust TOUCHSTONE_HASH_PRINTED_ABOVE
```

Build/replay exit 1 for development evidence, including positive presence results;
exit 2 means execution failure with no verdict. Never interpret exit 1 as a passing
merge gate. Replay is offline and checks bundled snapshot/source/schema/rubric,
manifest/touchstone identity and regenerated evidence/report. The expected touchstone
hash must come from a trusted reviewer channel. Self-consistent attacker-controlled
hashes do not authenticate provenance.

The authored miniature and protocol branch tests are engineering data. They are
not mined agent failures, not a six-fixture suite, and not official API evidence.
The upstream candidate is inspected locally and deliberately not redistributed
pending provenance/redistribution review. Reports do not prove syntax, typing,
access permissions, writability, constructibility or runtime behavior.

## Offline fixture intake

Use the [intake guide](docs/intake.md) and
[blank record template](examples/intake-record-template.json) for authorized
original exports. `python3 -m snapcite.intake --artifact-root ROOT RECORD.json`
checks completeness and local byte integrity separately from recorded admission
and per-entity 3/2/1 coverage. It never authenticates provenance or opens the
blocked development gate.
