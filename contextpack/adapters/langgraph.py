from contextpack.core.models import AggregatedAgentContext, ContextPack


class LangGraphAdapter:
    def inject(self, context: ContextPack | AggregatedAgentContext) -> dict:
        if isinstance(context, AggregatedAgentContext):
            return {"state": {"agent_context": context.model_dump()}}
        return {"state": {"context_pack": context.model_dump()}}
