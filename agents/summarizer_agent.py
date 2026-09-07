"""Summarizer agent: retrieves the chunks most relevant to the user's topic
and produces a concise summary, instead of a direct point-answer."""

from agents.base import BaseAgent
from llm.base import BaseLLM
from utils.guardrails import NO_CONTEXT_MESSAGE, has_sufficient_context
from vectorstore.store import VectorStore

_SUMMARY_SYSTEM_PROMPT = (
    "You are a document summarization assistant. Summarize the CONTEXT below "
    "as it relates to the user's request, in clear bullet points. Use ONLY "
    "the provided context - do not add outside information. Cite source "
    "file names in parentheses next to the points they support."
)


class SummarizerAgent(BaseAgent):
    key = "summarizer"
    label = "Summarizer Agent"
    description = (
        "Retrieves the content most relevant to your request and condenses it "
        "into a bullet-point summary grounded in the source documents."
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

        chunks = vectorstore.query(query, top_k=8, sources=sources)
        trace["retrieve"] = [c["source"] for c in chunks]

        if not has_sufficient_context(chunks):
            return {"answer": NO_CONTEXT_MESSAGE, "sources": [], "trace": trace}

        context = "\n\n".join(f"[Source: {c['source']}]\n{c['text']}" for c in chunks)
        user_prompt = f"Context:\n{context}\n\nSummarize the above with respect to: {query}"
        answer = llm.generate(_SUMMARY_SYSTEM_PROMPT, user_prompt)
        trace["summarize"] = "summary drafted"

        result_sources = sorted({c["source"] for c in chunks})
        return {"answer": answer, "sources": result_sources, "trace": trace}