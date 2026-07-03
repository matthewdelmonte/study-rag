"""Answer generation: retrieved context + question -> cited answer, via Ollama.

>>> PAIR-PROGRAMMING SPOT <<<
The prompt template is the lever that controls grounding and citation quality.
We'll tune it together in Phase 2.
"""

from __future__ import annotations

import ollama

from .retriever import Retrieved

DEFAULT_MODEL = "qwen2.5:14b-instruct"

SYSTEM = (
    "You answer strictly from the provided context. If the context does not contain "
    "the answer, say so. Cite the note titles you used."
)


def build_prompt(question: str, hits: list[Retrieved]) -> str:
    """Assemble the context block + question.

    TODO (pair): experiment with how context is framed — numbered sources,
    titles inline, etc. — and measure grounding.
    """
    context = "\n\n".join(f"[{h.title}]\n{h.text}" for h in hits)
    return f"Context:\n{context}\n\nQuestion: {question}"


def answer(question: str, hits: list[Retrieved], model: str = DEFAULT_MODEL) -> str:
    resp = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": build_prompt(question, hits)},
        ],
    )
    return resp["message"]["content"]
