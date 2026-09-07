"""Hard wall-clock timeout for calls into SDKs (Hugging Face Hub, Groq,
Gemini) whose own retry/backoff can block far longer than a user should ever
wait - runs the call on a background thread with a deadline instead of
trusting the SDK's own timeout options, which don't always cover every retry
path (e.g. Gemini's gRPC transport reconnects past its documented timeout)."""

import threading


def call_with_timeout(fn, timeout_seconds: float):
    outcome = {}

    def _run():
        try:
            outcome["value"] = fn()
        except Exception as e:
            outcome["error"] = e

    worker = threading.Thread(target=_run, daemon=True)
    worker.start()
    worker.join(timeout_seconds)

    if worker.is_alive():
        raise TimeoutError(f"Timed out after {timeout_seconds}s waiting for a response.")
    if "error" in outcome:
        raise outcome["error"]
    return outcome["value"]