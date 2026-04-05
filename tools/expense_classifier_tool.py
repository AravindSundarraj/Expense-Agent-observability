from models.llm_client import LLMClient
from services.item_extraction import extract_expenses_llm , safe_parse_json
from opentelemetry import trace
from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues
from opentelemetry.trace import Status, StatusCode
# Get tracer
tracer = trace.get_tracer("expense_classifier_tracer")

def classify_expense_llm(item: str):
    print("Classifying item in tool:", item)

    with tracer.start_as_current_span("expense_classifier_tool") as span_tool:
            span_tool.set_attribute(
                    SpanAttributes.OPENINFERENCE_SPAN_KIND,
                    OpenInferenceSpanKindValues.TOOL.value
                )

    prompt = f"""
            Classify the expense item into multiple attributes.

        Return JSON:
{{
  "category": "",
  "subcategory": "",
  "is_mandatory": true/false,
  "can_be_avoided": true/false,
  "is_healthy": true/false,
  "expense_type": "",
  "frequency": "",
  "savings_impact": "",
  "optimization_suggestion": ""
}}

Item: {item}
"""
    
    with tracer.start_as_current_span("expense_classifier_tool") as span_tool_LLM:
        span_tool_LLM.set_attribute(
                    SpanAttributes.OPENINFERENCE_SPAN_KIND,
                    OpenInferenceSpanKindValues.LLM.value
                )
        llm = LLMClient()
        response = llm.chat(
        system_prompt="You are a financial advisor AI.",
        user_prompt=prompt
    )
        classifier_dictionary = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
        "content": response.choices[0].message.content,
        "json": safe_parse_json(response.choices[0].message.content)

        }
        span_tool_LLM.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_PROMPT, classifier_dictionary["prompt_tokens"])
        span_tool_LLM.set_attribute(SpanAttributes.INPUT_VALUE, prompt)
        span_tool_LLM.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_COMPLETION, classifier_dictionary["completion_tokens"])
        span_tool_LLM.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_TOTAL, classifier_dictionary["total_tokens"])
        span_tool_LLM.set_attribute(SpanAttributes.LLM_MODEL_NAME, "gpt-4o-mini")
        span_tool_LLM.set_attribute(SpanAttributes.OUTPUT_VALUE, classifier_dictionary["json"])
        span_tool_LLM.set_status(Status(trace.StatusCode.OK))
        span_tool_LLM.set_attribute("llm.model", "gpt-4o-mini")
        span_tool_LLM.set_attribute("llm.provider", "openai")


        return classifier_dictionary