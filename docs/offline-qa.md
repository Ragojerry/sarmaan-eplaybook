# Offline Question Answering — revised Phases 10 & 11

## 1. What changed, and why

The master prompt specified Phase 10 as RAG (chunking, **embeddings, pgvector**, retrieval) and Phase 11 as
offline AI (**local embedding, local vector search, local LLM**). By product-owner decision these two phases
are **replaced** by a simpler design: an offline, deterministic, *extractive* question-answering engine.

> A user asks a question and — even with no internet — gets an answer taken only from the training content
> already stored on the phone, with its source shown.

Dropped: the embedding model, the vector database, the on-device LLM runtime. Every open decision that
blocked the original design (which model, which runtime, how to ship hundreds of MB of weights) simply no
longer applies. The pgvector `rag_chunks` table (schema-only, never populated) was removed by migration
`a7c3e91d2b54`; its downgrade restores it.

## 2. How an answer is produced

```
question
  -> tokenize, drop stopwords, light stemming
  -> synonym expansion into "concepts"  (vomit ~ retch/puke, medicine ~ drug/azm/dose, ...)
  -> BM25 over content chunks
  -> re-rank: the chunk containing the single sentence covering most concepts wins
  -> coverage check (>= 50% of the question's concepts must be covered)
  -> extract the best sentence(s) VERBATIM
  -> answer + source(s) + confidence      (or the strict fallback)
```

Nothing is generated — every word of an answer is copied from approved content, so the engine cannot invent
health information. If the evidence is thin it says so:
*"I couldn't find a reliable answer to this question in your downloaded training materials."* and suggests
topics it does cover. "No evidence → no answer."

**Chunks** are heading groups: a heading plus everything under it, mirroring how the flipbook is organised
(61 migrated sections → 16 chunks). Table rows become self-describing sentences
(`Age (1–11 months): 3–4 months; Dose: 3 ml.`) so a row is meaningful on its own.

**Confidence** is the share of the question's concepts the best passage covers (e.g. 0.75), not a statistical
probability. It is shown to users as "Match 75%".

## 3. Problems found by reading real answers (and fixed)

The engine was run on real migrated content and the answers read critically before anything was built on top:

1. *"What if the child vomits after the medicine?"* first returned the referral danger-signs list; the real
   instruction ("re-dose if the child vomits within 5 minutes") ranked second. Plain BM25 favoured a short
   chunk that repeated common words. **Fix:** re-rank by the best single sentence's concept coverage.
2. *Dosing tables.* Rows had no column headers, and asking about a **4-month-old** also matched the
   "5–11 months → 4 ml" row because the plain number 4 appears as a dose. In a health app that ambiguity is
   dangerous. **Fix:** self-describing table sentences, plus *range-aware numbers* — in a sentence containing
   ranges, a number matches only if it falls **inside** one (parenthesised header ranges and decimals like
   `11.5 – 12.4` are ignored). 4 → `3–4 months`; 8 → `5–11 months`; "severe malnutrition" returns only the
   severe row.
3. A second sentence is appended only when it is *as relevant as the first*; supporting sources must be
   substantive (≥2 concepts) — this removed stray citations such as "House-marking codes" on a dose question.

## 4. Same answers online and offline: the parity contract

The engine exists twice: `backend/app/ai/qa_engine.py` and `mobile/lib/qa/qa_engine.dart`, ported
line-for-line (integer arithmetic for percentages and scaled scores so rounding can't diverge).
`backend/scripts/generate_qa_vectors.py` writes `qa_vectors.json` (stopwords, synonym groups, tokenizer/stemmer
cases, and 13 question→answer cases over fixed chunks) to **both** `backend/tests/` and `mobile/test/`.
Python tests and `mobile/test/qa_engine_test.dart` replay the same file. Hand-written expectations
(tokenize/stem/content-terms) are asserted against the engine *before* the vectors are written.
**Any change to the algorithm must be made in both languages, then the vectors regenerated.**

## 5. API

- `POST /ai/ask` `{question, language}` → `{answer, matched, confidence, offline, sources[], suggestions[]}`;
  every question is logged to `ai_question_log` (matched or not) — unmatched questions show content admins
  what learners ask that the materials don't cover (master prompt §42-43).
- `GET /ai/chunks?language=en` — the passages the phone downloads.
- `python3 -m scripts.build_content_index` rebuilds the index from published content (idempotent; only
  `PUBLISHED` modules with a `PUBLISHED` translation).

## 6. Mobile

- Drift schema **v1 → v2**: new `ContentChunks` table with an `onUpgrade` migration (existing installs would
  otherwise crash with "no such table"). `LocalAiQuestions` (previously unused) now logs every question;
  `RagMetadata` is retired but left in place to avoid a destructive migration.
- `ContentSyncService` also downloads `/ai/chunks` (failure is isolated — modules still sync).
- `QuestionAnswerService` is the single seam the UI uses. **Local-first**: if the device holds the passages
  it answers on-device with no network; only a device with nothing downloaded asks the server; with neither
  it says nothing is downloaded yet. Each question is logged and queued in `pending_sync` for Phase 12.
- The **Ask** screen (chat UI, suggestion chips, source list, "Answered offline" badge, strict-fallback
  card) is back in the router and the bottom nav. Every answer carries: *"Copied from the training
  materials. For doses, always follow your job aid and the DIGIT HCM app."*

## 7. Verified

- **88 backend tests pass** (23 existing + 65 new): engine units; the parity vectors; ten real questions
  against real migrated content (including the 3/4/8-month dose cases, asserting the *wrong* row is absent);
  strict fallback for unsupported questions; answers verbatim from the materials; result independent of chunk
  order; the HTTP API (auth required, cited answer, logging of matched/unmatched, chunk download, validation).
- Migration: applied from an empty database, `alembic check` reports no drift, downgrade → upgrade round-trips.
- All 32 hand-written Dart files **parse cleanly** with a real Dart grammar (tree-sitter). Ten of them had
  already passed `flutter analyze` on your machine, which acted as a control for false positives; the checker
  was also confirmed to flag a deliberately broken file.

**Not verified here (no Dart SDK in this sandbox):** that the Dart code *compiles and runs*, and that the Dart
engine reproduces the vectors. The parser proves syntax, not types or behaviour. `flutter test` on
`qa_engine_test.dart` is the real proof of online/offline parity — please run it.

## 8. Known limitations

- **English only.** No Hausa/Fulfulde/Kanuri content exists yet. The engine is Unicode-aware and filters by
  language, so adding translated content + running the index builder is all that's needed.
- **No page numbers** in citations — the flipbook's page numbers were not carried into the content schema.
  Citations are module + section heading.
- **Synonyms are hand-tuned for the AZM content.** Review `ai_question_log` unmatched questions and extend the
  groups (in both languages, then regenerate vectors). Stemming is deliberately light, not a full stemmer.
- Numeric reasoning is limited to ranges as above; the engine does not do arithmetic. Dosing remains governed
  by the DIGIT HCM app / dose pole, which is why the disclaimer is shown.
- BM25 runs in application code over rows loaded from the database (server and phone), not via SQLite FTS5 /
  Postgres FTS. Chosen for identical behaviour in both places, and because FTS5 virtual-table code generation
  couldn't be verified here. At the current 16 chunks this is instant; revisit if content grows to thousands.
- The index is rebuilt by a script — it should be triggered when content is published (Phase 12/13 work).
- Queued questions are not uploaded until Phase 12 (sync).

## 9. Upgrade path (unchanged by this design)

Level 1 (this) → Level 2: a small local LLM that *rephrases* the already-retrieved passages → Level 3: an
online "enhanced" answer when connected. All slot in behind `QuestionAnswerService` without touching the UI.

## Synonym tuning (Phase 13.5)

`SYNONYM_GROUPS` in `backend/app/ai/qa_engine.py` is mirrored in
`mobile/lib/qa/qa_engine.dart` (`kSynonymGroups`). Change both, then run
`cd backend && python -m scripts.generate_qa_vectors` and `pytest`.

The latest pass used a **synthetic** paraphrase set (`PARAPHRASES` in
`tests/test_qa.py`), because no real unanswered questions exist yet. Changes:
vomiting phrasing (threw up, spit), thin/underweight -> MUAC, abuse/protection ->
safeguarding, parent/guardian -> caregiver, pregnant -> ANC, newborn -> age.
The medicine group was split so "AZM" no longer expands to "dose" (it made
unrelated chunks outrank real dosing answers).

**Safety fix:** years are converted to months before matching ("2 year old" ->
"24 months"). Previously a 2-year-old matched the "1-2 months: 2 ml" row.

**Do the real tuning after rollout:** open Admin > Analytics > unanswered questions
(`GET /analytics/questions`), add the recurring wordings as synonyms or content, and
add them to `PARAPHRASES`. Known gaps: "who can take the tablets" and "what if the
child is very thin" return the nearest chunk, not always the ideal sentence.
