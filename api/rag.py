"""RAG composer — retrieve → assemble → generate → cite → grounding check.

Grounding contract: when `answer` is not the empty-retrieval sentinel,
`len(citations) > 0` is required. Every cited `chunk_id` corresponds to
a chunk in the top-`k` retrieved from Weaviate.

Generator called with `do_sample=False` for reproducibility.

Integration deltas (backend/api-endpoints):
- The generator call runs under a per-call timeout (RAG_GENERATION_TIMEOUT_S,
  default 120s). On timeout the composer returns the SENTINEL with zero
  citations — the grounding refusal is preserved, never bypassed.
- Structured `api.rag` logs (retrieval size, generation latency, sentinel
  reason) are emitted for the Infra lead to read in `docker compose logs api`.
"""
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Tuple

logger = logging.getLogger("api.rag")

# Per-call wall-clock budget for one flan-t5-base generation. Default is
# deliberately generous: it is a hang-guard, not a latency cap. A normal
# 256-token CPU generation on a slow CI runner must finish well inside it,
# otherwise the demo call flips to the refusal sentinel and CI goes red.
GENERATION_TIMEOUT_S = float(os.environ.get("RAG_GENERATION_TIMEOUT_S", "120"))
# Single worker: generation is serialized so a slow call cannot fan out
# threads. NOTE: ThreadPoolExecutor cannot hard-kill the underlying thread —
# on timeout the model keeps running in the background until it finishes,
# but control returns to the caller and the request resolves as a refusal.
_GENERATION_POOL = ThreadPoolExecutor(max_workers=1, thread_name_prefix="rag-gen")

PROMPT_TEMPLATE = """\
You are answering a recipe question. Use ONLY the numbered sources below.
Cite each claim with the source number in square brackets, e.g. [1].
If the sources do not contain the answer, say: I cannot answer this from the available sources.

Sources:
{sources}

Question: {question}
Answer:"""

SENTINEL = "I cannot answer this from the available sources"
CITATION_PATTERN = re.compile(r"\[(\d+)\]")


def assemble_prompt(question: str, chunks: list[dict]) -> Tuple[str, dict[int, dict]]:
    """Number the retrieved chunks 1..k and substitute into the prompt template.

    Returns (prompt_str, {citation_index: chunk_dict}). Index starts at 1.
    """
    numbered: dict[int, dict] = {}
    lines = []
    for i, chunk in enumerate(chunks, start=1):
        numbered[i] = chunk
        lines.append(f"[{i}] {chunk['text']}")
    sources = "\n".join(lines)
    return PROMPT_TEMPLATE.format(sources=sources, question=question), numbered


def extract_citations(answer: str, numbered: dict[int, dict]) -> list[dict]:
    """Pull [N]-style markers from `answer` and resolve to retrieved chunks.

    Returns one {"chunk_id", "score"} dict per unique resolvable index.
    """
    cited: list[dict] = []
    seen: set[int] = set()
    for match in CITATION_PATTERN.finditer(answer):
        idx = int(match.group(1))
        if idx in numbered and idx not in seen:
            seen.add(idx)
            chunk = numbered[idx]
            cited.append({"chunk_id": chunk["chunk_id"], "score": chunk["score"]})
    return cited


def _run_generation(generator, prompt: str) -> str:
    """Invoke the generator under the per-call timeout budget.

    Returns the generated text, or raises FutureTimeoutError if the call
    exceeds GENERATION_TIMEOUT_S.
    """
    future = _GENERATION_POOL.submit(
        lambda: generator(prompt, max_new_tokens=256, do_sample=False)[0]["generated_text"]
    )
    return future.result(timeout=GENERATION_TIMEOUT_S)


def compose_rag(question: str, embedder, weaviate_client, generator, k: int = 4) -> dict:
    """Run the four-stage RAG pipeline.

    Encodes the question via the externally-loaded sentence-transformers
    embedder and queries Weaviate with `with_near_vector`. The Weaviate
    class is `vectorizer=none`, so `with_near_text` would fail at
    runtime with `KeyError: 'data'`.

    Returns {"answer": str, "citations": list[dict], "confidence": float}.
    """
    vector = embedder.encode(question).tolist()
    raw_query = (
        weaviate_client.query.get("Chunk", ["chunk_id", "text"])
        .with_near_vector({"vector": vector})
        .with_limit(k)
        .with_additional(["distance"])
        .do()
    )
    retrieved = [
        {
            "chunk_id": c["chunk_id"],
            "text": c["text"],
            "score": 1.0 - c["_additional"]["distance"],
        }
        for c in raw_query["data"]["Get"]["Chunk"]
    ]
    logger.info("rag.retrieve question_len=%d k=%d hits=%d", len(question), k, len(retrieved))
    if not retrieved:
        logger.info("rag.sentinel reason=empty_retrieval")
        return {"answer": SENTINEL, "citations": [], "confidence": 0.0}

    prompt, numbered = assemble_prompt(question, retrieved)
    started = time.monotonic()
    try:
        raw = _run_generation(generator, prompt)
    except FutureTimeoutError:
        logger.warning("rag.sentinel reason=generation_timeout budget_s=%.1f", GENERATION_TIMEOUT_S)
        return {"answer": SENTINEL, "citations": [], "confidence": 0.0}
    logger.info("rag.generate latency_ms=%d", int((time.monotonic() - started) * 1000))

    citations = extract_citations(raw, numbered)
    if not citations:
        logger.info("rag.sentinel reason=no_resolvable_citations")
        return {"answer": SENTINEL, "citations": [], "confidence": 0.0}

    confidence = sum(c["score"] for c in citations) / len(citations)
    confidence = max(0.0, min(1.0, confidence))
    logger.info("rag.answer citations=%d confidence=%.3f", len(citations), confidence)
    return {"answer": raw, "citations": citations, "confidence": confidence}