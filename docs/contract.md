# Snap Cite development contract 0.1

This implementation is staging only. concept.md remains frozen and unchanged.
No API entity or touchstone is freeze-qualified; corpus, snapshot selection,
yellow policy, independent review and pilot are pending human gates.

## Scope and identity

The engine evaluates explicit `class_exists`, `member_exists`, and `enum_item_exists`
assertions. Green proves exact-case presence only, never constructibility, member
accessibility, call signatures, writability, runtime behavior or complete code validity.
A Deprecated tag on the resolved class/member/enum/item yields yellow. Missing
entities yield red with an exhaustive lookup trace. Unsupported operations are
unevaluated; any coverage gap prevents an overall green report. Operational errors
fail execution (exit 2), never become an API verdict. Red exits 1 without override;
yellow exits 1 pending a human-approved policy. Development runs always exit 1.

Inputs are strict JSON, UTF-8, duplicate keys prohibited, integers bounded to
2^53-1, no floats, no surrogate characters. Canonicalization recursively sorts
ASCII object keys, preserves array order and Unicode strings without normalization,
uses compact separators, emits UTF-8 without BOM or newline. Object keys must be
ASCII. SHA-256 is over those exact bytes. This is a bounded format, not RFC 8785.
Raw snapshot and source snippets instead hash their exact original bytes.

Hash graph: snapshot/schema/rubric -> touchstone -> manifest -> packet.
No object contains its own hash. Citation ID is manifest SHA-256. The CLI requires
an external expected touchstone hash for build/replay; a hash alone authenticates
integrity relative to that trust anchor, never upstream authorship or human approval.
Engine, schema and rubric versions must match the installed implementation.
Touchstone includes hashes of schema and rubric and the raw snapshot pin.

## Source binding and coverage

Each manifest binds repository URL, full Git commit, safe relative path, whole-file
SHA-256, and each assertion's half-open UTF-8 byte span plus snippet SHA-256.
Build reads the exact file via `git show COMMIT:path`; replay uses bundled source
bytes and verifies file/span hashes. Repository origin and commit authenticity
remain reviewer checks: a local Git object is not authenticated agent provenance.
Coverage is explicitly `explicit-assertions-only`, never whole-program scanning.
Required claim IDs must equal evaluated assertion IDs for complete declared coverage;
unknown or omitted claims remain visible. At least one assertion is required.

## Snapshot adapter and rubric

Snapshot loader validates unique class/enum/member/item names, inheritance references
and cycles, and required structural fields. Member queries walk the exact class chain
and record declaring class, traversal, raw record and JSON pointer. Absence records
all searched class/member names (or enum/item names) plus the pinned snapshot hash.
No aliases, lowercase matching, bypass allowlists, SQL, arbitrary expressions or
network lookups occur during build/replay. Unknown operations are never compiled.

## Offline packet and report

A hash-addressed directory contains manifest, touchstone, schema, rubric, snapshot,
source, packet, report.txt and optionally report.pdf. Replay independently verifies
all pins and recomputes the packet, including inline evidence. Reports derive only
from the verified packet and include the full packet JSON inline. PDF uses pinned
ReportLab 4.4.4, invariant mode and page wrapping; reproducibility is tested in this
environment, not promised across platforms. URL references use the manifest hash;
links are operational and availability is reported separately. No QR is required
for offline verification. A development fixture is a positive engineering example,
not a curated corpus or an invented agent failure. Negative tests mutate protocol
inputs; they do not constitute yellow/red entity fixtures.

## Qualification and publication

Only staging bundles may be produced by this release. There is deliberately no
freeze command or approved mode. Human snapshot and policy decisions, genuine
3/2/1 entity corpus, one-level touchstone self-suite, independent acceptance and
pilot remain release blockers. Hash-addressed published directories must never be
replaced; a new input creates a new citation. Staging index is a static directory
listing/document, not a web application. Upstream candidate bytes are inspected
locally but not redistributed until the redistribution basis is established.
