"""Grounded answer generation.

Local mode quotes retrieved sentences. A live LLM is used only when a client
is configured. If that call fails, the extractive answer is returned and the
mode says the live call failed. Nothing is presented as a model answer unless
the provider returned it.
"""

from __future__ import annotations

from rag.schemas import FALLBACK_EN, GroundedAnswer, RetrievedChunk
from rag.textutil import content_tokens, sentences


def _citation(chunk: RetrievedChunk) -> dict:
    return {
        "record_id": chunk.record_id,
        "chunk_id": chunk.chunk_id,
        "title": chunk.title,
        "source": chunk.source,
        "source_url": chunk.source_url,
        "section": chunk.section,
        "category": chunk.category,
        "version": chunk.version,
        "score": round(chunk.score, 4),
    }


def _extractive(query: str, chunks: list[RetrievedChunk]) -> str:
    query_terms = set(content_tokens(query))
    picked: list[str] = []
    for chunk in chunks[:1]:
        options = sentences(chunk.content) or [chunk.content]
        scored = []
        for index, sentence in enumerate(options):
            terms = set(content_tokens(sentence))
            overlap = len(query_terms & terms)
            scored.append((overlap, index, sentence))
        matched = [item for item in scored if item[0] > 0] or scored[:1]
        matched.sort(key=lambda item: item[0], reverse=True)
        chosen = sorted(matched[:3], key=lambda item: item[1])
        for _, _, sentence in chosen:
            if sentence not in picked:
                picked.append(sentence)
    if not picked and chunks:
        picked = sentences(chunks[0].content)[:2] or [chunks[0].content]
    answer = " ".join(picked).strip()
    if len(answer) > 700:
        answer = answer[:700].rsplit(" ", 1)[0] + "..."
    return answer


def generate(
    query: str,
    chunks: list[RetrievedChunk],
    threshold: float,
    fallback_message: str = FALLBACK_EN,
    llm=None,
    system_prompt: str = "",
) -> GroundedAnswer:
    payload = [chunk.model_dump() for chunk in chunks]
    if not chunks or chunks[0].score < threshold:
        return GroundedAnswer(
            answer=fallback_message,
            confidence=round(chunks[0].score, 4) if chunks else 0.0,
            sources=[],
            retrieved_chunks=payload,
            fallback=True,
            fallback_reason="below_confidence_threshold" if chunks else "no_retrieval",
            generation_mode="fallback",
        )
    sources = [_citation(chunk) for chunk in chunks[:3]]
    if llm is not None:
        context = "\n\n".join(
            f"[{chunk.record_id}] {chunk.content}" for chunk in chunks[:3]
        )
        user = (
            "Answer only from the context. If the context is insufficient, say you do not know.\n\n"
            f"Context:\n{context}\n\nQuestion: {query}"
        )
        try:
            text = llm.complete(system_prompt, user)
            return GroundedAnswer(
                answer=text,
                confidence=round(chunks[0].score, 4),
                sources=sources,
                retrieved_chunks=payload,
                fallback=False,
                generation_mode="llm",
            )
        except Exception:
            answer = _extractive(query, chunks)
            return GroundedAnswer(
                answer=answer,
                confidence=round(chunks[0].score, 4),
                sources=[_citation(chunks[0])],
                retrieved_chunks=payload,
                fallback=False,
                fallback_reason="llm_call_failed_used_extractive",
                generation_mode="extractive_after_llm_error",
            )
    return GroundedAnswer(
        answer=_extractive(query, chunks),
        confidence=round(chunks[0].score, 4),
        sources=[_citation(chunks[0])],
        retrieved_chunks=payload,
        fallback=False,
        generation_mode="extractive",
    )
