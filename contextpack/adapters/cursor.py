from contextpack.core.models import AggregatedAgentContext, ContextPack


class CursorAdapter:
    """Inject context as Cursor extra_instructions / rules attachment."""

    def inject(self, context: ContextPack | AggregatedAgentContext) -> dict:
        if isinstance(context, AggregatedAgentContext):
            block = context.extra_instructions
        else:
            block = "\n".join(context.summaries)
        return {
            "type": "cursor_context",
            "extra_instructions": block,
            "files": getattr(context, "files", []),
        }
