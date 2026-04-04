from opentelemetry import trace
from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues

tracer = trace.get_tracer("expense_agent_tracer")


def classify_expense(item: str):
    """
    Simple rule-based classifier (mock tool)
    """

    # 🔧 TOOL SPAN
    with tracer.start_as_current_span("expense_classifier_tool") as span:

        span.set_attribute(
                SpanAttributes.OPENINFERENCE_SPAN_KIND,
                OpenInferenceSpanKindValues.TOOL.value
            )
        span.set_attribute(SpanAttributes.INPUT_VALUE, item)

        # Simple logic (can replace with ML/LLM later)
        if item.lower() in ["uber", "taxi"]:
            category = "Travel"
        elif item.lower() in ["food", "coffee", "groceries"]:
            category = "Food"
        else:
            category = "Other"

        span.set_attribute(SpanAttributes.OUTPUT_VALUE, category)

        return category