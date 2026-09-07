"""Browser IndexedDB persistence, via a small hand-written Streamlit
component (storage/idb_frontend/index.html) implementing the Streamlit
Components postMessage protocol directly - no third-party JS-bridge
library, no build step.

Startup reads are batched into a single `idb_get_multi()` component call
rather than issuing one component instance per key. Testing showed that
multiple simultaneous instances of the same custom component in one script
run could each independently complete their IndexedDB work (confirmed via
frontend console tracing) but never have their resolved value observed on
the Python side - a bidirectional-component limitation in this Streamlit
version, not an IndexedDB problem. A single batched call sidesteps it
entirely, since the app never needs more than one `idb_store` instance
active in the same rerun (get_multi at hydration in ui/state.py; set/delete
afterwards, on pages that don't hydrate).

Because the browser round trip is asynchronous, a call may return LOADING
before Streamlit reruns the script with the resolved value.

Passing an explicit `key=` (required to keep a widget's identity stable
across reruns) makes Streamlit ignore the call's other arguments when
computing that identity - so two `idb_set()` calls to the same key share one
widget slot no matter what value each one writes. That means the frontend's
bare confirmation can't be matched back to a specific write by identity
alone: once any write to a key has ever been confirmed, that same stale
"confirmed" value keeps coming back on every later call, including calls
carrying a newer, not-yet-written value. `idb_set` works around this by
tagging each write with a short content token and only treating it as
confirmed when the echoed token matches the value just sent.
"""

import hashlib
import json
from pathlib import Path

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).resolve().parent / "idb_frontend"
_idb_component = components.declare_component("idb_store", path=str(_FRONTEND_DIR))

LOADING = object()  # sentinel distinct from any real stored value (incl. None)
_SENTINEL = "__IDB_LOADING__"


def _call(action: str, call_key: str, **kwargs):
    result = _idb_component(action=action, default=_SENTINEL, key=call_key, **kwargs)
    if result == _SENTINEL:
        return LOADING
    if isinstance(result, dict) and "__error__" in result:
        raise RuntimeError(f"IndexedDB error: {result['__error__']}")
    return result


def idb_get_multi(keys: list[str]):
    """Fetch several keys in a single component round trip. Returns a dict
    (key -> value or None), or LOADING if not resolved yet."""
    return _call("get_multi", "idb_get_multi_" + "_".join(keys), storage_keys=keys)


def idb_set(key: str, value) -> bool:
    """Persist 'value' (any JSON-serializable object) under 'key'. Returns
    True once the browser confirms *this* write landed, False if it's still
    in flight (or a stale confirmation from a previous write to this key came
    back instead) - callers that need the write to be durable before moving
    on (e.g. before re-enabling the UI) should keep calling this with the
    same value until it returns True."""
    token = _content_token(value)
    result = _call("set", f"idb_set_{key}", storage_key=key, value=value, confirm_token=token)
    return isinstance(result, dict) and result.get("confirm_token") == token


def _content_token(value) -> str:
    serialized = json.dumps(value, sort_keys=True, default=str)
    return hashlib.sha1(serialized.encode("utf-8")).hexdigest()[:12]


def idb_delete(key: str) -> bool:
    """Delete 'key'. Returns True once the browser confirms, False if still
    in flight. Unlike `idb_set`, a stale confirmation from an earlier delete
    of this key is still a valid confirmation here - deleting is idempotent,
    so there's no "newer content" it could be masking - hence no content
    token needed."""
    return _call("delete", f"idb_delete_{key}", storage_key=key) is True