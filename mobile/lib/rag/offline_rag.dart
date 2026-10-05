/// On-device retrieval half of the offline AI pipeline: embeds the user's
/// question with the same embedding model used server-side (master prompt
/// §29), searches the bundled offline vector index (§28) shipped inside each
/// content release, and returns the top matching content chunks with their
/// module/section citation (§36) for the local LLM runtime to answer from.
///
/// AI/RAG is confirmed in MVP scope (docs/architecture.md §6).
/// Phase 2 scope: interface only — real implementation depends on the
/// embedding model / vector engine choice, still open (master prompt §29).
library offline_rag;
