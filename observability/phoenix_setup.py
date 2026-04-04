# Import open-telemetry dependencies
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode

from openinference.instrumentation import using_session
from openinference.instrumentation.openai import OpenAIInstrumentor
from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues
from openinference.semconv.resource import ResourceAttributes

from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from phoenix.evals import LLM
from phoenix.evals.metrics import CorrectnessEvaluator
from phoenix.client import Client
from phoenix.evals import bind_evaluator
from phoenix.evals import evaluate_dataframe
from phoenix.trace import suppress_tracing
from phoenix.evals.utils import to_annotation_dataframe

# ***** Trace Provider ******
# TracerProvider primarily creates Tracers, and Tracers create Spans. 
# The hierarchy is:

# TracerProvider → creates Tracers
# Tracer → creates Spans
# Span → contains the actual trace data (timing, attributes, events, status)
# But TracerProvider also manages:

# SpanProcessors — how spans are processed (e.g., batched or simple)
# Exporters — where spans are sent (e.g., Phoenix, Jaeger)
# Resource — metadata like project name attached to all spans
# So TracerProvider is the top-level orchestrator — it doesn't just create tracers, it also controls the entire pipeline of how span data flows from creation to export.

load_dotenv()

# ---------------- OTEL SETUP ---------------- #

def init_phoenix():
    print("Initializing Phoenix tracing...")
    """
    Initializes Phoenix tracing for the entire Expense Agent system.
    This should be called once at application startup.
    """

    # 1. Set up tracer provider (core tracing engine)
    trace_attributes = {
    ResourceAttributes.PROJECT_NAME: "Expense Agent Observability",
    }

    tracer_provider = trace_sdk.TracerProvider(
    resource=Resource(attributes=trace_attributes)
    )

    # 2. Phoenix OTLP exporter endpoint
    # phoenix_endpoint = os.getenv(
    #     "PHOENIX_ENDPOINT",
    #     "http://localhost:6006/v1/traces"
    # )

    # 3. Exporter sends traces to Phoenix backend
    otlp_exporter = OTLPSpanExporter(
       endpoint="localhost:4317",
       insecure=True
)


    tracer_provider.add_span_processor(BatchSpanProcessor(
    otlp_exporter,
    max_queue_size=2048,        # max spans buffered
    max_export_batch_size=512,  # spans per batch send
    schedule_delay_millis=5000, # flush interval (ms)
    export_timeout_millis=30000 # timeout for export
))

init_phoenix()
