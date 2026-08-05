"""Provider-agnostic single-turn chat.

Lets the engine send an LLM call to EITHER Claude (Anthropic) or Kimi (Moonshot,
which exposes an OpenAI-compatible API) by flipping one env var — so token usage
can be moved between providers without touching any call site, and rolled back
instantly if the new one underperforms.

    AI_PROVIDER=claude   (default) -> Anthropic Messages API   · key ANTHROPIC_API_KEY
    AI_PROVIDER=kimi               -> Moonshot OpenAI-compat API · key MOONSHOT_API_KEY
                                      base https://api.moonshot.ai/v1 · model kimi-k3

The two APIs differ in shape (Anthropic: `messages.create(system=..., content blocks)`;
OpenAI/Moonshot: `chat.completions.create(messages=[{role:system},{role:user}])`), and
this module hides that difference behind one `chat()` call that returns plain text.
"""
import os

CLAUDE = "claude"
KIMI = "kimi"


def provider() -> str:
    """Active provider name (lowercased). Defaults to 'claude'."""
    return (os.getenv("AI_PROVIDER") or CLAUDE).strip().lower()


def api_key_present() -> bool:
    """True if the API key for the ACTIVE provider is set."""
    return bool(os.getenv("MOONSHOT_API_KEY") if provider() == KIMI
                else os.getenv("ANTHROPIC_API_KEY"))


def active_model(claude_default: str) -> str:
    """Model id for the active provider — the Kimi model when on Kimi, else the
    caller's Claude default (so each call site keeps its own Claude model choice)."""
    if provider() == KIMI:
        return os.getenv("MOONSHOT_MODEL") or "kimi-k3"
    return claude_default


def chat(system: str, user: str, model: str = None, max_tokens: int = 1024,
         timeout: int = 45) -> str:
    """One system+user turn against the active provider. Returns the reply text.
    Raises on a missing key or API error (callers already guard/catch)."""
    if provider() == KIMI:
        # Moonshot speaks the OpenAI Chat Completions dialect — lazy import so the
        # openai package is only needed when actually running on Kimi.
        from openai import OpenAI
        client = OpenAI(
            api_key=os.environ["MOONSHOT_API_KEY"],
            base_url=os.getenv("MOONSHOT_BASE_URL") or "https://api.moonshot.ai/v1",
            timeout=timeout,
        )
        resp = client.chat.completions.create(
            model=model or os.getenv("MOONSHOT_MODEL") or "kimi-k3",
            max_tokens=max_tokens,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
        )
        return resp.choices[0].message.content or ""

    # Default: Claude via the Anthropic Messages API.
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=timeout)
    resp = client.messages.create(
        model=model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user}])
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
