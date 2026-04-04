from opentelemetry import trace
from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues

from tools.expense_classifier_tool import classify_expense

# Get tracer
tracer = trace.get_tracer("expense_agent_tracer")


def run_expense_agent(user_input: str):
    """
    Entry point for Expense Agent
    """

    # 🔍 ROOT SPAN (TRACE)
    with tracer.start_as_current_span("expense_agent_chain-span") as root_span:

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

        print("Processing user input..." , user_input)
                # 🧩 CHILD SPAN → Extraction
        with tracer.start_as_current_span("expense_extraction") as span:
            span.set_attribute(
                SpanAttributes.OPENINFERENCE_SPAN_KIND,
                OpenInferenceSpanKindValues.CHAIN.value
            )
            extracted_items = extract_expenses(user_input)

            span.set_attribute("extracted.count", len(extracted_items))
                # 🧩 CHILD SPAN → Classification (calls TOOL)
        with tracer.start_as_current_span("expense_classification") as span:
            span.set_attribute(
                    SpanAttributes.OPENINFERENCE_SPAN_KIND,
                    OpenInferenceSpanKindValues.CHAIN.value
                )

            classified = []

            for item in extracted_items:
                category = classify_expense(item["item"])  # 🔧 TOOL CALL

                classified.append({
                    "item": item["item"],
                    "amount": item["amount"],
                    "category": category
                })

            span.set_attribute("classified.count", len(classified))
        # 🧩 NEW: Aggregation Span
        '''
        We introduce an aggregation span to isolate the final transformation stage, 
        where classified expenses are grouped and summarized. This helps us separate 
        computational logic from data transformation, 
        making performance and debugging analysis more precise.
        ''' 
        with tracer.start_as_current_span("expense_aggregation") as span:

            span.set_attribute(
                    SpanAttributes.OPENINFERENCE_SPAN_KIND,
                    OpenInferenceSpanKindValues.CHAIN.value
                )
            total_by_category = {}

            for item in classified:
                cat = item["category"]
                total_by_category[cat] = total_by_category.get(cat, 0) + item["amount"]

            final_output = {
                "classified_items": classified,
                "summary": total_by_category
            }

            # Observability metadata
            span.set_attribute("categories.count", len(total_by_category))
            span.set_attribute("items.count", len(classified))


        # For now, just return input
        return final_output

'''
The expense extractor is isolated in a separate span to clearly capture and measure 
the input parsing step independently from other agent logic, enabling visibility 
into how raw user input is transformed into structured expense data.
'''    
def extract_expenses(user_input: str):

    return [
        {"item": "Uber", "amount": 120},
        {"item": "Food", "amount": 50}
    ]