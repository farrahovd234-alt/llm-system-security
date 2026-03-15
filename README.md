# Киберполигон: Smart Wiki Security Stand

## Описание проекта
**Smart Wiki** — это прототип корпоративной базы знаний с интегрированным ИИ-ассистентом. Система предназначена для автоматизации работы с технической документацией: написания статей, генерации диаграмм и интеллектуального поиска по внутренним регламентам.

**Главная идея проекта:**
Исследование уязвимостей, возникающих при использовании ИИ-агентов для генерации исполняемого контента. В системе реализован подход, при котором вывод LLM (Markdown, HTML, JS-код для диаграмм) напрямую рендерится в интерфейсе или используется для управления данными через инструменты MCP. Это позволяет наглядно демонстрировать атаки классов **Insecure Output Handling** и **Indirect Prompt Injection**.

## Архитектура системы

```mermaid
flowchart LR

%% ================= Attack Surface =================
subgraph attack["Attack Surface"]
    kali["Kali<br/>(Атакующий)"]
end


%% ================= Ubuntu Host =================
subgraph ubuntu["Ubuntu"]

direction LR


%% ---------- Interface ----------
subgraph interface["Interface Layer"]
    streamlit["Wiki UI<br/>(Streamlit)"]
end


%% ---------- API ----------
subgraph api["API Layer"]
    subgraph fastapi["FastAPI"]
        direction TB
        guard_in["GuardIn"]
        router["Router"]
        guard_out["GuardOut"]
    end
end


%% ---------- AI / LLM ----------
subgraph ai["AI / LLM Layer"]
    rag["RAG Chain<br/>(Wiki Search)"]
    agent["Agent LangGraph"]
    ollama["Ollama<br/>(сервер моделей)"]
    huggingface["Hugging Face<br/>(репозиторий моделей)"]
end


%% ---------- Tools ----------
subgraph tools["Tools Layer"]
    mcp["Tools<br/>(MCP Server)"]
end


%% ---------- Data ----------
subgraph data["Data Layer"]
    chroma["ChromaDB<br/>(Векторная база)"]
    postgres["PostgreSQL<br/>(БД контента и логов)"]
    fs["Файловая система<br/>(Статьи Wiki)"]
end


%% ---------- Observability ----------
subgraph observability["Observability"]
    prometheus["Prometheus + cAdvisor"]
    langfuse["Langfuse"]
end

end


%% ================= Attacks =================
kali -->|HTTP / curl| streamlit
kali -->|прямой запрос| guard_in


%% ================= Main Flow =================
streamlit -->|Запрос на оформление| guard_in
guard_in --> router

router -->|mode=rag| rag
router -->|mode=agent| agent
router -->|chat / generate| ollama


%% ================= RAG =================
rag --> chroma
rag --> ollama


%% ================= Agent =================
agent <-->|Think / Act / Observe| ollama
agent --> mcp


%% ================= Tools =================
mcp --> postgres
mcp --> fs


%% ================= Models =================
huggingface -.->|модели скачиваются| ollama


%% ================= Output (Secure Path) =================
ollama --> guard_out
guard_out -->|HTML / Markdown / JS| streamlit


%% ================= Observability =================
router --> langfuse
guard_out --> langfuse
ollama -.-> langfuse

streamlit -.-> prometheus
ollama -.-> prometheus
fastapi -.-> prometheus


%% ================= Styles =================
classDef attack fill:#ffd6d6,stroke:#c92a2a,stroke-width:2px,color:#000;
classDef interface fill:#dbeafe,stroke:#1d4ed8,stroke-width:2px,color:#000;
classDef api fill:#ede9fe,stroke:#6d28d9,stroke-width:2px,color:#000;
classDef ai fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#000;
classDef tools fill:#ffedd5,stroke:#ea580c,stroke-width:2px,color:#000;
classDef data fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#000;
classDef obs fill:#e5e7eb,stroke:#374151,stroke-width:2px,color:#000;

class kali attack
class streamlit interface
class guard_in,router,guard_out api
class rag,agent,ollama,huggingface ai
class mcp tools
class chroma,postgres,fs data
class prometheus,langfuse obs
