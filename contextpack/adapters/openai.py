from contextpack.adapters.claude import ClaudeAdapter


class OpenAIAdapter(ClaudeAdapter):
    """OpenAI chat format — same structure as Claude adapter."""

    def inject(self, context):  # type: ignore[no-untyped-def]
        payload = super().inject(context)
        return {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": payload["system"]},
                *payload["messages"],
            ],
        }
