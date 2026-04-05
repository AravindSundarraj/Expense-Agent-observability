from opentelemetry import trace
from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues

from tools.expense_classifier_tool import classify_expense_llm
from models.llm_client import LLMClient
from models.prompts import EXPENSE_SYSTEM_PROMPT, EXPENSE_USER_PROMPT_TEMPLATE
from opentelemetry.trace import Status, StatusCode
import openinference.instrumentation as oi
from services.item_extraction import extract_expenses_llm
from services.summary import build_summary


# Get tracer
tracer = trace.get_tracer("expense_agent_tracer")

def clean_json_block(text):
    import re, json

    text = text.strip()

    # remove ```json ``` wrappers
    text = re.sub(r"```json|```", "", text).strip()

    return json.loads(text)

def extract_expenses(user_input: str):

    return extract_expenses_llm(user_input)

def run_expense_llm(user_input, classified_items, summary):

    llm = LLMClient()

    user_prompt = EXPENSE_USER_PROMPT_TEMPLATE.format(
        user_input=user_input,
        classified_items=classified_items,
        summary=summary
    )

    return llm.chat(
        system_prompt=EXPENSE_SYSTEM_PROMPT,
        user_prompt=user_prompt
    )

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
        #root_span.set_attribute("user.input", user_input)

        print("Processing user input..." , user_input)
                # 🧩 CHILD SPAN → Extraction
        with tracer.start_as_current_span("expense_extraction") as ex_span:
            ex_span.set_attribute(
                SpanAttributes.OPENINFERENCE_SPAN_KIND,
                OpenInferenceSpanKindValues.LLM.value
            )
            extracted_items = extract_expenses(user_input)

            
            
            ex_span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_PROMPT, extracted_items["prompt_tokens"])
            ex_span.set_attribute(SpanAttributes.INPUT_VALUE, user_input)
            ex_span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_COMPLETION, extracted_items["completion_tokens"])
            ex_span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_TOTAL, extracted_items["total_tokens"])
            ex_span.set_attribute(SpanAttributes.LLM_MODEL_NAME, "gpt-4o-mini")
            ex_span.set_attribute(SpanAttributes.OUTPUT_VALUE, extracted_items["json"])
            ex_span.set_status(Status(StatusCode.OK))
            ex_span.set_attribute("llm.model", "gpt-4o-mini")
            ex_span.set_attribute("llm.provider", "openai")

            
                # 🧩 CHILD SPAN → Classification (calls TOOL)
        with tracer.start_as_current_span("expense_classification") as expense_span:
            expense_span.set_attribute(
                    SpanAttributes.OPENINFERENCE_SPAN_KIND,
                    OpenInferenceSpanKindValues.CHAIN.value
                )
            expense_span.set_status(Status(StatusCode.OK))
            expense_span.set_attribute(SpanAttributes.INPUT_VALUE, extracted_items)

            classified = []

            for item in extracted_items["json"]:  # 🔧 TOOL CALL
                print("Classifying item:", item , "item-type:", type(item))
                category = classify_expense_llm(item)
                print("category---:", category)  # 🔧 TOOL CALL

                classified.append(category["content"])

            expense_span.set_attribute("classified.count", len(classified))
            expense_span.set_attribute(SpanAttributes.OUTPUT_VALUE, classified)
            print("Classified items:", classified)
        # 🧩 NEW: Aggregation Span
        '''
        # We introduce an aggregation span to isolate the final transformation stage, 
        # where classified expenses are grouped and summarized. This helps us separate 
        # computational logic from data transformation, 
        # making performance and debugging analysis more precise.
        # ''' 
        # with tracer.start_as_current_span("expense_aggregation") as span:

        #     span.set_attribute(
        #             SpanAttributes.OPENINFERENCE_SPAN_KIND,
        #             OpenInferenceSpanKindValues.CHAIN.value
        #         )
        #     total_by_category = {}

        #     for item in classified:
        #         cat = item["category"]
        #         total_by_category[cat] = total_by_category.get(cat, 0) + item["amount"]

        #     final_output = {
        #         "classified_items": classified,
        #         "summary": total_by_category
        #     }

        #     # Observability metadata
        #     span.set_attribute("categories.count", len(total_by_category))
        #     span.set_attribute("items.count", len(classified))
        with tracer.start_as_current_span(
        "expense_llm_generation") as llm_span:
    
            cleaned_classified_items = [
            clean_json_block(item) for item in classified
                ]
            llm_span.set_attribute(
            SpanAttributes.OPENINFERENCE_SPAN_KIND,
            OpenInferenceSpanKindValues.LLM.value)
    
            try:
                llm_output = run_expense_llm(user_input, cleaned_classified_items, build_summary(cleaned_classified_items))
                oi_token_count = oi.TokenCount(
                prompt=llm_output.usage.prompt_tokens,
                completion=llm_output.usage.completion_tokens,total=llm_output.usage.total_tokens)

                llm_span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_PROMPT, llm_output.usage.prompt_tokens)
                llm_span.set_attribute(SpanAttributes.INPUT_VALUE, user_input)
                llm_span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_COMPLETION, llm_output.usage.completion_tokens)
                llm_span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_TOTAL, llm_output.usage.total_tokens)
                llm_span.set_attribute(SpanAttributes.LLM_MODEL_NAME, "gpt-4o-mini")
                llm_span.set_attribute(SpanAttributes.OUTPUT_VALUE, llm_output.choices[0].message.content)
                llm_span.set_status(Status(StatusCode.OK))
                llm_span.set_attribute("llm.model", "gpt-4o-mini")
                llm_span.set_attribute("llm.provider", "openai")
            except Exception as e:
                llm_span.set_status(Status(StatusCode.ERROR, str(e)))
                raise e
        root_span.set_status(Status(StatusCode.OK))
        root_span.set_attribute(SpanAttributes.OUTPUT_VALUE, llm_output.choices[0].message.content)
            
    

        # For now, just return input
    return llm_output.choices[0].message.content

'''
The expense extractor is isolated in a separate span to clearly capture and measure 
the input parsing step independently from other agent logic, enabling visibility 
into how raw user input is transformed into structured expense data.
'''    
