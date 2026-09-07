"""Document Q&A agent: plan -> retrieve -> reason -> validate.

Each step is a discrete method so the agent's behaviour (and its trace) is
easy to follow and to extend with more tools later."""

from agents.base import BaseAgent
from llm.base import BaseLLM
from utils.guardrails import NO_CONTEXT_MESSAGE, has_sufficient_context
from vectorstore.store import VectorStore

_PLAN_SYSTEM_PROMPT = (
    "You are a retrieval planning assistant. Rewrite the user's question into "
    "a short, keyword-rich search query optimized for semantic search over "
    "enterprise documents. Reply with ONLY the rewritten query, nothing else."
)

_ANSWER_SYSTEM_PROMPT = (
    "You are an enterprise document assistant. Answer the user's question "
    "using ONLY the context provided below. If the answer is not contained "
    "in the context, say you don't know based on the available documents - "
    "never make up information. Cite the source file name(s) you used in "
    "parentheses at the end of relevant sentences."
)

_VALIDATE_SYSTEM_PROMPT = (
    "You are a strict fact-checker. Given a CONTEXT and an ANSWER, reply with "
    "exactly one word: 'GROUNDED' if every claim in the ANSWER is supported by "
    "the CONTEXT, or 'UNGROUNDED' if the ANSWER contains claims not present in "
    "the CONTEXT."
)


class QAAgent(BaseAgent):
    key = "qa"
    label = "Document Q&A Agent"
    description = (
        "Plans a search query, retrieves the most relevant chunks, drafts a "
        "grounded answer, and validates the answer against the retrieved context."
    )

    def plan(self, llm: BaseLLM, query: str, chat_history: list[dict]) -> str:
        history_snippet = "\n".join(
            f"{m['role']}: {m['content']}" for m in chat_history[-4:]
        )
        user_prompt = f"Recent conversation:\n{history_snippet}\n\nQuestion: {query}"
        try:
            rewritten = llm.generate(_PLAN_SYSTEM_PROMPT, user_prompt)
            return rewritten.strip() or query
        except Exception:
            return query

    def retrieve(
        self, vectorstore: VectorStore, search_query: str, sources: list[str] | None
    ) -> list[dict]:
        return vectorstore.query(search_query, sources=sources)

    def reason(self, llm: BaseLLM, query: str, chunks: list[dict]) -> str:
        context = "\n\n".join(f"[Source: {c['source']}]\n{c['text']}" for c in chunks)
        user_prompt = f"Context:\n{context}\n\nQuestion: {query}"
        return llm.generate(_ANSWER_SYSTEM_PROMPT, user_prompt)

    def validate(self, llm: BaseLLM, answer: str, chunks: list[dict]) -> bool:
        if not chunks:
            return False
        context = "\n\n".join(c["text"] for c in chunks)
        user_prompt = f"CONTEXT:\n{context}\n\nANSWER:\n{answer}"
        try:
            verdict = llm.generate(_VALIDATE_SYSTEM_PROMPT, user_prompt)
            return "GROUNDED" in verdict.upper()
        except Exception:
            return True  # don't block the answer if the validator call fails

    def run(
        self,
        query: str,
        chat_history: list[dict],
        llm: BaseLLM,
        vectorstore: VectorStore,
        sources: list[str] | None = None,
    ) -> dict:
        trace = {}

        search_query = self.plan(llm, query, chat_history)
        trace["plan"] = search_query

        chunks = self.retrieve(vectorstore, search_query, sources)
        trace["retrieve"] = [c["source"] for c in chunks]

        if not has_sufficient_context(chunks):
            return {
                "answer": NO_CONTEXT_MESSAGE,
                "sources": [],
                "trace": trace,
            }

        answer = self.reason(llm, query, chunks)
        trace["reason"] = "answer drafted"

        is_grounded = self.validate(llm, answer, chunks)
        trace["grounded"] = is_grounded

        result_sources = sorted({c["source"] for c in chunks})
        return {
            "answer": answer,
            "sources": result_sources,
            "trace": trace,
        }