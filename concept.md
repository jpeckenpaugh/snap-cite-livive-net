**Project:** snap-cite
**Document version:** v0.1.0
**Status:** FROZEN
**Freeze date:** 2026-10-21
**Scope statement:** A grounding report generator for Roblox/Luau code under agentic authorship, scoped to a single frozen API snapshot.

---

## 1. Thesis

snap-cite produces a report that a reviewer, a designer, or an agent can cite. The report states, for a pinned Roblox API snapshot, which code patterns are valid, which warrant caution, and which are stopped — each backed by a reproducible citation. It refuses to be a museum, an oracle, or a query language. Its value is the discipline of its own boundary.

## 2. The invariant

**A published version never mutates.**

Everything else in this document derives from that sentence. The API snapshot freezes on day 01. The touchstone freezes on day 01. The concept freezes on day 01. Later versions are new versions, never edits.

## 3. Scope

| In | Out |
|---|---|
| Day-01 Roblox API snapshot | Any other API version |
| Report pipeline (engine → report → PDF) | Web UI, graph explorer, museum |
| JSON manifest citations | SQL as a public interface |
| Touchstone as versioned provenance contract | Multi-version touchstone compilation |
| 3 green / 2 yellow / 1 red fixture suite | Luau grammar and type-system validation |
| Failure corpus mined from real agent outputs | Synthetic failure generation |
| Self-validation on the touchstone | Recursive meta-validation |

Scope-out items are deferred, not scheduled. They are listed so that a future snapshot can diff against this one and compute lineage as a diff, not as a wish.

## 4. Pipeline

```
API snapshot (frozen)
      │
      ▼
 Touchstone (frozen rubric)  ──► manifest (citation)
      │                              │
      ▼                              ▼
  evidence packet  ◄────────  QR / URL (manifest hash)
      │
      ▼
   report ──► PDF ──► PR / brief / architecture doc
```

Every arrow is a named guarantee. The snapshot-to-touchstone arrow guarantees reproducibility. The manifest-to-touchstone arrow guarantees the citation resolves against a frozen standard, not against current data. The report-to-PDF arrow guarantees the artifact is self-contained to the extent stated in §5.

## 5. Citation contract

A **touchstone** is the versioned provenance contract: it carries the API snapshot version, the manifest schema version, and the rubric that defines what a valid citation is. It is frozen on day 01.

A **manifest** is a citation: a versioned JSON descriptor that references a touchstone and encodes the query the citation represents. Manifests are compiled by the backend, never executed as text. A manifest's canonical hash is its identity.

A **citation** is a manifest plus its touchstone. Citations link to their touchstone. A touchstone is the only object that claims provenance for a given set of positions at a given point in time, and it claims it only under its own verifiable rubric.

The PDF carries evidence inline as the floor and links as the ceiling. A link that resolves to the touchstone resolves to the same standard the PDF was generated against.

## 6. Verdict taxonomy

Every fixture, and every report line, carries one of three verdicts:

- **Green** — valid pathway. Three per entity. Cruise.
- **Yellow** — edge case, deprecated-but-working, version-fragile, or under-advisement. Two per entity. Caution; requires a stated policy at the review layer.
- **Red** — the single most probable hallucination for that entity. One per entity. Stopped, no override.

Yellow is bounded at two for the same reason red is bounded at one: if the curator cannot choose, the curator has found concerns, not fixtures. Concerns belong in doc prose.

Yellow's ambiguity at the automation layer is a policy decision, not a schema decision. That policy must be written before yellow is trusted in CI. It is not written here.

## 7. Self-validation clause

The touchstone carries its own fixture suite — 3 green, 2 yellow, 1 red — and the suite is green before the touchstone freezes. The touchstone practices the discipline it asks of the code it reports on.

Self-validation is one level deep. The touchstone is validated by the same machinery it defines. That machinery is validated by CI exit codes. There is no meta-validator. If self-validation requires an LLM to adjudicate, the vanity machine has been rebuilt and the clause has failed.

Freeze is a ceremony, human-gated, one event: green suite → tagged commit → published touchstone version → freeze. There is no freeze tooling. Tooling for a single event is the vanity machine again.

## 8. Failure corpus

Red and yellow fixtures are **mined from real agent outputs**, not invented. Each carries provenance: model family, model version, temperature, and failure class. The corpus is data. It is the museum's future exhibit hall and the report's current evidence, and it earns both roles by being real.

The method for building it: do not ask a model to produce bad code. Ask for code, observe where the probability mass leans wrong, and record the lean.

## 9. The 3 / 2 / 1 on this document

**Green — this document must support these uses:**

- **G1 — Scope determination.** A reader can state what is in and what is out from §3 alone, without inferring from tone.
- **G2 — Citation tracing.** Given a PDF citation, a reader can name the full chain (§4) and mark which links are contractual versus operational.
- **G3 — Failure attribution.** Given a red or yellow fixture, a reader can identify provenance and violated assertion as two separate facts.

**Yellow — this document permits these with caution:**

- **Y1 — Boundary pressure.** A reader may argue that an item in §3 is misclassified. The document permits this by naming the table as the scope rather than the rationale; a misclassification is a change request against a frozen document, which is a new version, not an edit.
- **Y2 — Metaphor drift.** The reader may carry the traffic-light or water-sphere framing into discussion. The document permits this as long as the framing does not enter the schema; §6 is the only place verdict colors have operational meaning.

**Red — this document must cause this to fail loudly:**

- **R1 — Version generalization.** A reader treats the document's claims about the day-01 snapshot as authoritative for any other API version. The document fails this by scoping every factual claim to the snapshot and marking everything else as method. Test: every API claim in the document carries a scope marker; expected unscoped count is zero.

The two failure modes R1 and Y1 address — generalizing past the snapshot, and one-and-ing toward the museum — are the two the author committed in the conversation that produced this document. They are named here so the document holds the line the tool is supposed to hold.

## 10. Non-goals

The museum. The graph explorer. The web UI. Lineage across versions. Luau grammar validation. Multi-version touchstone compilation. The water-sphere metaphor as a feature. The bodhi tree.

These are not scheduled. No temporal language attaches to them. They are absent by scope, and their absence is the scope.

## 11. Deliberately absent

No glossary of metaphors. No future-work section. No open-questions section. No roadmap. A question written down here would make this document a proposal again.

---

*This tool makes claims only about the snapshot it carries, and proves its own discipline by carrying a 3/2/1 suite on its own provenance contract before that contract is frozen.*
