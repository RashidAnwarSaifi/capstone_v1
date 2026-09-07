"""Fact-checker agent: independently drafts an answer, then explicitly lists
which claims are supported by the retrieved documents and which are not.

Useful to run alongside the QA agent when the user wants an explicit,
itemized grounding check rather than the QA agent's single-word verdict."""

from agents.base import BaseAgent
from llm.base import BaseLLM
from utils.guardrails import NO_CONTEXT_MESSAGE, has_sufficient_context
from vectorstore.store import VectorStore

_ANSWER_SYSTEM_PROMPT = (
    "You are an enterprise document assistant. Answer the user's question "
    "using ONLY the context provided below. Never invent information."
)

_CHECK_SYSTEM_PROMPT = (
    "You are a fact-checking assistant. Given a CONTEXT and a DRAFT ANSWER, "
    "list each factual claim in the DRAFT ANSWER on its own line, and mark it "
    "'[Supported]' or '[Unsupported]' based on whether the CONTEXT backs it "
    "up. Be strict: a claim only counts as supported if it is explicitly "
    "stated or directly implied by the CONTEXT."
)


class FactCheckerAgent(BaseAgent):
    key = "fact_checker"
    label = "Fact-Checker Agent"
    description = (
        "Drafts an answer, then itemizes each claim as Supported or "
        "Unsupported against the retrieved document context."
    )

    def run(
        self,
        query: str,
        chat_history: list[dict],
        llm: BaseLLM,
        vectorstore: VectorStore,
        sources: list[str] | None = None,
    ) -> dict:
        trace = {}

        chunks = vectorstore.query(query, sources=sources)
        trace["retrieve"] = [c["source"] for c in chunks]

        if not has_sufficient_context(chunks):
            return {"answer": NO_CONTEXT_MESSAGE, "sources": [], "trace": trace}

        context = "\n\n".join(f"[Source: {c['source']}]\n{c['text']}" for c in chunks)

        draft = llm.generate(
            _ANSWER_SYSTEM_PROMPT, f"Context:\n{context}\n\nQuestion: {query}"
        )
        trace["draft"] = "draft answer produced"

        checked = llm.generate(
            _CHECK_SYSTEM_PROMPT,
            f"CONTEXT:\n{context}\n\nDRAFT ANSWER:\n{draft}",
        )
        trace["fact_check"] = "claims itemized"

        answer = f"**Draft answer:**\n{draft}\n\n**Claim-by-claim check:**\n{checked}"
        result_sources = sorted({c["source"] for c in chunks})
        return {"answer": answer, "sources": result_sources, "trace": trace}