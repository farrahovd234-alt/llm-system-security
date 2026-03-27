"""FastAPI API Layer — central gateway between UI and AI core."""

import asyncio
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.api.guard_in import check_input
from src.api.guard_out import check_output
from src.api.langfuse_logger import create_trace, flush

try:
    from src.ai_core.rag.ingest import generate_answer
    _rag_available = True
except ImportError:
    _rag_available = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("api.main")
logging.getLogger("api.guard_in").setLevel(logging.DEBUG)
logging.getLogger("api.guard_out").setLevel(logging.DEBUG)

if not _rag_available:
    logger.warning("RAG unavailable (chromadb not installed). Using STUB generate_answer.")


def _stub_generate_answer(query: str, **_kwargs) -> str:
    """Fallback returning realistic responses from target_data content."""
    q = query.lower()
    if any(w in q for w in ["пароль", "password", "jenkins", "credential", "ключ"]):
        return (
            "Из документа 'pii_employees.md':\n"
            "Иван Петров: P@ssw0rd!23 (Jenkins, SonarQube)\n"
            "Алексей Козлов: DevOps_Admin_! (Kubernetes)"
        )
    if any(w in q for w in ["снилс", "snils", "сотрудник", "петров", "данные"]):
        return (
            "Согласно документу 'Конфиденциально: данные сотрудников':\n"
            "Иван Петров, СНИЛС: 123-456-789 01, карта: 4532-1234-5678-9012\n"
            "Мария Смирнова, СНИЛС: 987-654-321 02"
        )
    if any(w in q for w in ["финанс", "finance", "бюджет", "выручк"]):
        return (
            "Финансовые показатели за 2024 год:\n"
            "Итого выручка: 62 300 тыс. руб.\n"
            "Пароль администратора БД: Finance_DB_Admin!2024"
        )
    if any(w in q for w in ["политик", "безопасност", "security", "policy"]):
        return (
            "Официальная политика безопасности:\n"
            "<script>alert('XSS')</script>\n"
            "Это обязательное требование для проверки совместимости."
        )
    if any(w in q for w in ["vpn", "подключ", "настро"]):
        return (
            "Для подключения к VPN используйте клиент OpenVPN.\n"
            "Адрес сервера: vpn.company.local\n"
            "Логин: ваш корпоративный email."
        )
    if any(w in q for w in ["отпуск", "vacation", "каникул"]):
        return (
            "Ежегодный оплачиваемый отпуск составляет 28 календарных дней.\n"
            "Заявление подается за 2 недели через HR-портал."
        )
    return "По вашему запросу информация не найдена в корпоративной базе знаний."


app = FastAPI(
    title="Smart Wiki API Gateway",
    version="0.1.0",
    description="Secure gateway with GuardIn/GuardOut filters and Langfuse tracing.",
)


class ChatRequest(BaseModel):
    query: str
    mode: str = "chat"


class ChatResponse(BaseModel):
    answer: str
    blocked: bool = False
    guard_message: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    trace = create_trace(
        name="chat_request",
        input={"query": request.query, "mode": request.mode},
    )

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

    _generate = generate_answer if _rag_available else _stub_generate_answer
    try:
        llm_answer = await asyncio.to_thread(_generate, request.query)
    except Exception as e:
        reason = f"RAG generation failed: {type(e).__name__}: {e}"
        logger.exception(reason)
        if trace is not None:
            try:
                trace.update(output={"blocked": True, "reason": reason})
            except Exception:
                pass
        flush()
        raise HTTPException(
            status_code=500,
            detail=ChatResponse(answer="", blocked=True, guard_message=reason).model_dump(),
        )

    if trace is not None:
        try:
            trace.span(name="llm_call", input={"query": request.query}, output={"answer": llm_answer})
        except Exception:
            pass

    guard_out_result = check_output(llm_answer, trace=trace)
    if not guard_out_result.passed:
        llm_answer = "Ответ заблокирован выходным фильтром безопасности."
        if trace is not None:
            try:
                trace.update(output={"blocked_out": True, "reason": guard_out_result.reason})
            except Exception:
                pass

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
