"""Chat with your documents: answer questions using only the user's files,
and say exactly which file and page each fact came from."""
from core import ai
from core.semantic import top_chunks

TOP_K = 6
MIN_SCORE = 0.45

ANSWER_PROMPT = """You answer questions using ONLY the numbered sources below,
which come from the user's own documents.
- After each fact, cite its source number in square brackets, like [1] or [2][3].
- If the sources do not contain the answer, say: "I couldn't find this in your documents."
- Be clear and concise. Use Markdown lists where helpful."""


def find_sources(files, question, k=TOP_K):
    """The chunks most related to the question."""
    return [c for c in top_chunks(files, question, limit=k) if c["score"] >= MIN_SCORE]


def format_source(c):
    page = f", page {c['page']}" if c["page"] else ""
    return f"{c['file'].name}{page}"


def stream_answer(question, sources, previous=()):
    """Yield the answer piece by piece (so the UI can show it as it's written).
    `previous` is a list of earlier (question, answer) pairs for follow-up questions."""
    context = "\n\n".join(
        f"[{i}] ({format_source(c)})\n{c['text']}" for i, c in enumerate(sources, start=1)
    )
    messages = [{"role": "system", "content": ANSWER_PROMPT}]
    for q, a in list(previous)[-2:]:
        messages += [{"role": "user", "content": q}, {"role": "assistant", "content": a}]
    messages.append({"role": "user", "content": f"Sources:\n{context}\n\nQuestion: {question}"})

    for part in ai.chat(messages, temperature=0.2, stream=True):
        if part.message.content:  # reasoning (if any) arrives separately and is skipped
            yield part.message.content
