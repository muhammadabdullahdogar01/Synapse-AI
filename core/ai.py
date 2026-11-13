"""Shared settings for talking to the local AI model through Ollama."""
import re
from functools import lru_cache

import ollama

# The Instruct version answers directly. The default "qwen3:4b" is a Thinking
# model: it writes long hidden reasoning first, which is ~7x slower on a laptop CPU.
PREFERRED_MODELS = ["qwen3:4b-instruct", "qwen3:4b"]
MODEL = PREFERRED_MODELS[0]
CONTEXT_TOKENS = 8192  # how much text the model can see at once


def _installed():
    try:
        return [m.model for m in ollama.list().models]
    except Exception:
        return None


def active_model():
    """The best installed model from PREFERRED_MODELS."""
    names = _installed() or []
    for wanted in PREFERRED_MODELS:
        if any(n == wanted or n == f"{wanted}:latest" for n in names):
            return wanted
    return MODEL


@lru_cache(maxsize=8)
def _can_think(model):
    try:
        return "thinking" in (ollama.show(model).capabilities or [])
    except Exception:
        return False


def strip_thinking(text):
    """Remove any <think>...</think> reasoning a model printed into its answer."""
    if "</think>" in text:
        text = text.split("</think>", 1)[1]
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def chat(messages, schema=None, temperature=0, stream=False):
    """Send messages to the local model. With a schema, the reply is guaranteed JSON."""
    model = active_model()
    # For a thinking model, think=True makes Ollama keep the reasoning in a
    # separate field so it never appears in the answer; with a schema we can
    # turn thinking off completely.
    think = _can_think(model) and schema is None
    return ollama.chat(
        model=model,
        messages=messages,
        format=schema,
        think=think,
        stream=stream,
        options={"temperature": temperature, "num_ctx": CONTEXT_TOKENS},
    )


def status():
    """Which parts of the AI engine are ready."""
    names = _installed()
    if names is None:
        return {"online": False, "chat_model": False, "embed_model": False, "model": None}
    model = active_model()
    return {
        "online": True,
        "chat_model": any(n.startswith(model) for n in names),
        "embed_model": any(n.startswith("nomic-embed-text") for n in names),
        "model": model,
    }
