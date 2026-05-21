from contextpack.core.models import AggregatedAgentContext, ContextPack


class ClaudeAdapter:
    def inject(self, context: ContextPack | AggregatedAgentContext) -> dict:
        if isinstance(context, AggregatedAgentContext):
            text = context.to_agent_prompt_block()
        else:
            text = "\n".join(context.summaries)
        return {
            "system": "You are a domain-aware engineering agent with full project context.",
            "messages": [{"role": "user", "content": text}],
        }
