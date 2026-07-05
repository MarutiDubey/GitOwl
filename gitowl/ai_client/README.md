# `gitowl.ai_client` — Provider-agnostic AI layer

Every provider implements one method:

```python
def review(self, diff: str, findings: list[Finding]) -> ReviewResult: ...
```

## Interface contract

- **Input:** a unified `diff` string and a list of Semgrep `Finding`s.
- **Output:** a `ReviewResult` (`summary`, `risk`, `findings`, `dismissed`).
- **Errors:** raise `AIProviderError` on network/auth/parse failures.

See [`base.py`](base.py) for the abstract class and [`models.py`](../models.py)
for the data shapes.

## Built-in providers

| `AI_PROVIDER` | Class | Notes |
|---|---|---|
| `openrouter` | `OpenRouterProvider` | Default. One key, many models. Needs `AI_API_KEY`. |
| `openai` | `OpenAIProvider` | Direct OpenAI API. Needs `AI_API_KEY`. |
| `ollama` | `OllamaProvider` | Local, free, no key. Run `ollama serve` first. |

`openrouter`, `openai`, and `ollama` all speak the OpenAI `/chat/completions`
protocol, so they share [`openai_compatible.py`](openai_compatible.py).

## Adding a provider

1. Subclass `AIProvider` (or `OpenAICompatibleProvider` if the API is OpenAI-shaped).
2. Set a unique `name`.
3. Register it in [`registry.py`](registry.py) (add to `_BUILTIN` loop or call
   `register_provider`).
4. Add tests under `tests/` with the HTTP layer mocked — never hit a live API in tests.
