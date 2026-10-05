/// Orchestrates the hybrid AI flow: online → ApiClient.dio.post('/ai/ask');
/// offline → OfflineRag lookup + local quantized LLM (master prompt §31-32).
/// Must enforce the strict knowledge boundary (§33) — answers only from
/// approved content, with a logged "not found" fallback (§35) rather than a
/// hallucinated answer, matching (but properly implementing, not faking)
/// the prototype's `kb` fallback behaviour (docs/prototype-analysis.md §6).
///
/// Phase 2 scope: interface only.
library ai_assistant;
