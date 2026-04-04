from opentelemetry import trace
from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues

# Get tracer
tracer = trace.get_tracer("expense_agent_tracer")


def run_expense_agent(user_input: str):
    """
    Entry point for Expense Agent
    """

    # 🔍 ROOT SPAN (TRACE)
    with tracer.start_as_current_span("expense_agent_chain-span",openinference_span_kind="chain") as root_span:

        # Add metadata (very important for observability)
        # root_span.set_attribute(SpanAttributes.SESSION_ID, session_id)
        # root_span.set_attribute(SpanAttributes.USER_ID, "user-456")

        root_span.set_attribute(
                SpanAttributes.OPENINFERENCE_SPAN_KIND,
                OpenInferenceSpanKindValues.CHAIN.value
            )

        root_span.set_attribute(SpanAttributes.INPUT_VALUE, user_input)
        root_span.add_event("Agent started reasoning")
        root_span.set_attribute("user.input", user_input)

        print("Processing user input...")

        # For now, just return input
        return {"message": "Processing started"}