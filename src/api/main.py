"""FastAPI API Layer — central gateway between UI and AI core.
 
Endpoints:
    POST /api/v1/chat — accept user query, run through GuardIn → LLM → GuardOut.
"""
 
import asyncio
import logging
 
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
 
from src.api.guard_in import check_input
from src.api.guard_out import check_output
from src.api.langfuse_logger import create_trace, flush
from src.ai_core.rag.ingest import generate_answer
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("api.main")
 
app = FastAPI(
    title="Smart Wiki API Gateway",
    version="0.1.0",
    description="Secure gateway with GuardIn/GuardOut filters and Langfuse tracing.",
)
 
 
# ---------------------------------------------------------------------------
# Pydantic contracts
# ---------------------------------------------------------------------------
 
class ChatRequest(BaseModel):
    query: str
    mode: str = "chat"
 
 
class ChatResponse(BaseModel):
    answer: str
    blocked: bool = False
    guard_message: str | None = None
 
 
# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
 
@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint.
 
    Flow: GuardIn → RAG/LLM → GuardOut → Response.
    """
    trace = create_trace(
        name="chat_request",
        input={"query": request.query, "mode": request.mode},
    )
 
    # 1. Input guard
    guard_in_result = check_input(request.query, trace=trace)
    if not guard_in_result.passed:
        if trace is not None:
            try:
                trace.update(output={"blocked": True, "reason": guard_in_result.reason})
            except Exception:
                pass
        flush()
        raise HTTPException(
            status_code=403,
            detail=ChatResponse(
                answer="",
                blocked=True,
                guard_message=guard_in_result.reason,
            ).model_dump(),
        )
 
    # 2. LLM / RAG call
    # NOTE: generate_answer() is synchronous; run it in a thread to avoid blocking event loop.
    try:
        llm_answer = await asyncio.to_thread(generate_answer, request.query)
    except Exception as e:
        reason = f"RAG generation failed: {type(e).__name__}: {e}"
        logger.exception(reason)
        if trace is not None:
            try:
                trace.update(output={"blocked": True, "reason": reason})
            except Exception:
                pass
        flush()
        raise HTTPException(status_code=500, detail=ChatResponse(answer="", blocked=True, guard_message=reason).model_dump())
 
    if trace is not None:
        try:
            trace.span(name="llm_call", input={"query": request.query}, output={"answer": llm_answer})
        except Exception:
            pass
 
    # 3. Output guard
    guard_out_result = check_output(llm_answer, trace=trace)
    if not guard_out_result.passed:
        llm_answer = "Ответ заблокирован выходным фильтром безопасности."
        if trace is not None:
            try:
                trace.update(output={"blocked_out": True, "reason": guard_out_result.reason})
            except Exception:
                pass
 
    # 4. Response
    response = ChatResponse(
        answer=llm_answer,
        blocked=not guard_out_result.passed,
        guard_message=guard_out_result.reason,
    )
 
    if trace is not None:
        try:
            trace.update(output=response.model_dump())
        except Exception:
            pass
    flush()
 
    return response