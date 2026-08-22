# Style brief for `audit-paper-v2`

Derived from three exemplars, read this pass: **Harder**, *An Answer to the
Bose–Nelson Sorting Problem for 11 and 12 Channels* (arXiv:2012.04400v3, 54 pp,
~24,600 w) — the direct model; **Codish, Cruz-Filipe, Frank & Schneider-Kamp**,
*Twenty-Five Comparators is Optimal…* (arXiv:1405.5754v3, 18 pp, ~9,800 w;
JCSS 2016 as *Sorting nine inputs requires twenty-five comparisons*) — the model
for a computational-proof trust argument; **Ehlers & Müller**, *Faster Sorting
Networks for 17, 19 and 20 Inputs* (arXiv:1410.2736, 6 pp, 1,949 w) — the
short-note calibration.

---

## Target

**5,000–7,000 words ≈ 10–14 pages** at the exemplars' density (Codish et al.
run ~545 words/page single-column). Down from the v0.1 draft's 13,100.

This sits deliberately between Codish (9,800 w) and Ehlers–Müller (1,949 w).
It is **not** Harder-length: Harder is 54 pages because 12 of them are a new
theory of partial sorting networks and 11 are a formal-verification apparatus we
do not have. What we take from Harder is proportion, not size.

*Where v2.0 actually landed:* **8,140 words** (7,685 excluding the reference list
and the internal draft banner), ≈ 15 pages — over target. The overrun is
structural, not stylistic: five claim tiers do not compress below about eight
thousand words without dropping one. The only cut that reaches 10–14 pages is a
split into an audit note (§§1–5) and a computation paper (§§6–8), which is what
the external prior-art review recommends. Flagged for the architect rather than
resolved here.

**The proportions that matter, measured:**

| | Harder | Codish et al. | us (target) |
|---|---|---|---|
| introduction | 2 pp (4 %) | 3 pp (17 %) | ~1.5 pp (13 %) |
| the actual headline result | **2 pp of 54 (4 %)** | 1.5 pp (8 %) | ~1 p |
| trust / verification story | **11 pp (23 %)** | 1.5 pp (10 %) | ~2 pp (15 %) |
| conclusion | 1 p, 368 w | **1 paragraph** | ≤ 1 p |

Harder spends a quarter of his paper on *why you should believe the number* and
4 % on *the number*. Copy that ratio. Our equivalent of his trusted base is
§9 Reproducibility + §10 Limitations.

---

## Section skeleton

Follow Harder's shape — *theory → method → trust → results → conclusion* — with
Ehlers–Müller's rule that the status table lands by page 2.

```
Abstract              ~230 w, unnumbered, no heading
1  Introduction       the bounds table by p. 2; contributions as a numbered
                      ladder; one paragraph on the artifact; a roadmap
                      paragraph naming every section by number  [Harder does
                      exactly this and it costs 5 lines]
2  Preliminaries      only the vocabulary later sections actually use
3  The audit          the chain, the counterexample, prevalence, the strongest
                      defence, the misstatement/gap distinction
4  The record         literature negative, provenance, what is unaffected
5  Partial repair     the identity, the two proved classes, the rich end,
                      coverage, closed routes
6  [second result]    stated at the same level of rigour, or cut
7  [credential]       the computation, as a narrative proof
8  Status             the honest open problem, priced
9  Reproducibility    the trusted base, in Harder's register
10 Limitations        numbered, blunt
   References         numbered, alphabetical, DOIs, artifacts among them
```

Sub-subsections are permitted to depth 2 (`5.3`) and no further. Harder never
goes past `8.2`; Codish et al. never past `4.4`.

---

## Theorem-statement conventions

**From Harder, adopt all four:**

1. **One continuous counter across Definitions, Lemmas, Theorems, Corollaries.**
   Harder runs Definition 1 … Corollary 62 in a single sequence. It removes the
   "which Lemma 3?" problem and makes back-references unambiguous.
2. **Every statement carries a parenthetical name**: `Lemma 9 (Pigeon Hole
   Bound)`, `Theorem 26 (The Huffman Bound)`. When a result is imported, the
   citation goes *inside the name*: `Lemma 17 (Van Voorhis [26])`.
3. **Be sparing with the word Theorem.** Harder has 3 in 62 statements. Ours
   should have at most 5. Everything else is a Lemma, a Proposition or a
   Corollary. A Theorem is a statement the paper would be pointless without.
4. **No "Theorem 1 = main result" up front.** Harder's headline is Theorem 61
   on page 42 of 54. The contribution ladder in §1 does the up-front work; the
   statements arrive when they are earned.

**From Harder's Theorem 61, adopt the computational-proof register.** Its
"proof" is a narrative of the run — stages, wall times, peak memory, certificate
size, the checker's literal return value — closed by *one* logical sentence
("From the machine checked formal correctness proof … we get that s(11) ≥ 35").
Any claim of ours that rests on a computation is written the same way: numbers,
then one sentence of logic. Never the reverse.

**Naming discipline for renumbered results.** Every statement that exists under
another name in the artifact carries it: `Theorem 12 (escape-free case; Theorem
6′ of [artifact])`. Two documents in this project already collide on
"Theorem C"; the paper must not inherit that.

**Conditionality is part of the statement, not a later caveat.** If a result
holds modulo an unproved proposition, a code audit, or a specific patched
binary, that appears in the statement or in the sentence immediately following
it — never only in §10.

---

## The trust argument

Harder's §8.2 *Trusted Base* is a three-column table (Component | Trusted Base |
Notes), 9 rows, 4 Yes / 5 No, each justified. Three moves to copy exactly:

- **Disclaim bug-freeness rather than claiming correctness.** *"Note that we do
  not require, or even expect, the trusted base to be free of all bugs."*
- **Scope to the single run.** *"here our goal is to verify a specific single
  result of a computation. Therefore only bugs that are triggered during that
  verification are relevant."*
- **Put your own mathematics outside the trusted base where the certificate
  permits it.** Harder places his own §5 correctness proof outside: eleven pages
  of his theory could be wrong without the headline number moving.

From Codish et al., copy one rhetorical move and one standard:

- **Name the shared dependency of two "independent" checks and concede it
  first.** They write: *"While it is reassuring to have two alternative proofs,
  they both share the computation of R¹⁴₉ … there is always the potential for
  errors in computer programs."* Our exact analogue: `verify_huffman2.py` and
  `verify_kraft_dispute.py` share nothing, but the two wave verifiers import the
  first one's primitives. Say so in the same breath as "independent".
- **Invoke the de Bruijn criterion by name** (every computer-assisted proof
  should be checkable by an independent small program) and claim conformance to
  it, rather than claiming correctness directly.

---

## The artifact, and how it is cited

**Harder has no "Availability" section.** Artifacts are ordinary numbered
bibliography entries — Zenodo DOI first, GitHub URL second — cited from four
inline sentences in the body. Codish et al. give one bare homepage URL in
running text, which by 2026 standards is a defect; Wang (2025) gives a bare
GitHub URL, same defect.

**Our rule:** artifacts are bibliography entries with DOIs, cited inline at each
point of use, plus **one** three-sentence paragraph at the end of §1 naming the
repository and the deposit. That is a small, deliberate departure from Harder
(who has no such paragraph), justified because our artifact is the *primary*
evidence for the audit rather than a convenience for re-running a search.

**Harder's in/out rule, adopted verbatim as ours:** *anything a reader must
audit to believe the result stays in the paper; anything they would only re-run
goes to the deposit.* He keeps the full inference system and the Isabelle
problem statement in the paper; he exports the Rust, the proofs, the certificate
format and the 2.9 GB certificate.

**Numerical claims.** Every one is keyed to a verifier. In the text, name the
**script** only — `verify_kraft_wave2.py`. The check-ID tables live in the
artifact (`verifiers/CHECKS.md`). The v0.1 draft's inline `V1:E4` / `V2:D-1`
citations are exactly the kind of apparatus the exemplars keep out of the paper.

---

## Register

- Declarative. State the finding, then the evidence. No throat-clearing.
- Harder's person convention: **"we" for mathematics, "I" for judgement calls
  and for computations personally run** (*"Currently, I do not consider this
  approach to be practical"*). We have no single author; use "we" throughout and
  mark judgements as judgements instead.
- Quote the primary source minimally and exactly, with page numbers.
- Numbers get units and a source. Never a bare ratio: "14.6× (search stage,
  191 GB → 13.08 GB)".
- Credit precedent before claiming novelty. Harder: *"This approach … was
  already used by Cruz-Filipe and Schneider-Kamp [8]."*
- Conclusions are short. Codish et al.'s is one paragraph.

---

## What NEVER goes in the paper

1. **Check-ID tables and per-check citations.** Script names in text; IDs in the
   artifact.
2. **Verbatim tool output.** Harder quotes exactly one string, the checker's
   return value. We may quote one.
3. **The project's internal apparatus** — gates, tiers, waves, campaigns,
   contracts, ledgers, agent roles. A result is not more credible for having a
   process behind it. One sentence on methodology, at most.
4. **Anything the artifact cannot regenerate.** If no shipped tool recomputes a
   number, either the tool gets written or the number does not appear.
5. **Retracted claims, in any softened form.** "Pass-throughs are the sole
   obstruction" is retracted; it does not reappear as "largely" or "typically".
6. **Any statement that a superseded result is the current one.** If a wider
   class has been proved, the narrower theorem is not the paper's result.
7. **Speculative roadmaps and effort estimates for work not done.** Harder's
   Future Work is 8 lines.
8. **Marketing.** No "novel", "powerful", "significant", "state-of-the-art".
   No claim that a negative result is exciting.
9. **A target of 44 anywhere.** The number appears only as the object under
   audit — never as a bound, feature, goal or stopping condition.
10. **Unscoped superlatives about our own verification.** "Machine-checked" is
    reserved for what a machine checked; a code-reading audit is called an
    audit, and a human second reader is called a second reader.

---

## Concrete borrowings, listed so they can be checked off

| from | what | where it lands |
|---|---|---|
| Ehlers–Müller | the status table by page 2 | §1.1 |
| Harder §1 | 5-line roadmap naming every section | end of §1 |
| Harder | continuous statement numbering + parenthetical names | throughout |
| Harder Thm 61 | computation-as-narrative-proof | §7 |
| Harder §8.2 | trusted-base table, Yes/No, with disclaimers | §9 |
| Harder | artifacts as DOI'd bibliography entries | §1, References |
| Codish §6 | concede the shared dependency; de Bruijn criterion | §9 |
| Codish §7 | one-paragraph conclusion | §8 close |
| Harder Lemma 17 | full proof of an imported classical result, with attribution in the name | §4 (the pre-emption) |
