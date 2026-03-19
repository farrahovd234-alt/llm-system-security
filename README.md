# AI Security Cyber Range: Wiki Assistant

## 📌 О проекте

Данный проект представляет собой **испытательный полигон**, имитирующий работу корпоративной системы **Wiki** с интегрированным ИИ-ассистентом. 

Проект разработан для демонстрации и тестирования методов защиты больших языковых моделей (LLM) в закрытом контуре. Он позволяет исследовать векторы атак на ИИ и наглядно показывать работу защитных механизмов в реальном времени.

### Какую задачу решает система?
Интеграция ИИ в корпоративную среду несет в себе специфические риски безопасности. Данная система решает задачу **безопасного взаимодействия пользователя с LLM и корпоративными данными**, обеспечивая:
* **Защиту от манипуляций (Prompt Injection):** Нейтрализация попыток подмены системных инструкций вредоносными запросами.
* **Предотвращение утечек (Data Exfiltration):** Контроль за тем, чтобы конфиденциальная информация из базы знаний не покинула защищенный периметр.
* **Безопасное управление инструментами (Agent Security):** Ограничение прав ИИ-агента при работе с файловой системой и базами данных через строгие протоколы доступа.

---

## 🏗 Архитектура системы

В основе системы лежит принцип **эшелонированной защиты**. Архитектура четко разделяет роли пользователей, потоки данных и контур мониторинга, исключая возможность прямого доступа к модели в обход фильтров.

```mermaid
flowchart LR

%% ================= ВНЕШНИЙ КОНТУР =================
subgraph surface["Surface Layer (Поверхность доступа)"]
    direction TB
    kali["Kali Linux<br/>(Атакующий)"]:::attacker
    user["User<br/>(Сотрудник)"]:::user
    admin["Admin<br/>(Аудитор ИБ)"]:::admin
end

%% ================= ВНУТРЕННЯЯ ИНФРАСТРУКТУРА =================
subgraph ubuntu["Ubuntu Host (Серверная часть)"]
direction LR

    %% ---------- Пользовательский интерфейс ----------
    subgraph interface_layer["Interface Layer"]
        streamlit["Wiki UI<br/>(Streamlit)"]:::ui
    end

    %% ---------- Панель управления ----------
    subgraph admin_panel["Admin Panel (Secure Zone)"]
        direction TB
        grafana["Grafana<br/>(Метрики)"]:::monitor
        langfuse["Langfuse<br/>(Трассировка ИИ)"]:::monitor
    end

    %% ---------- Ядро логики и защиты ----------
    subgraph api["API Layer (FastAPI)"]
        direction TB
        guard_in["GuardIn<br/>(Входной фильтр)"]:::api
        router["Router<br/>(Диспетчер)"]:::api
        guard_out["GuardOut<br/>(Выходной фильтр)"]:::api
    end

    %% ---------- Искусственный интеллект ----------
    subgraph ai["AI / LLM Layer"]
        direction TB
        rag["RAG Chain"]:::ai
        agent["Agent<br/>(LangGraph)"]:::ai
        ollama["Ollama<br/>(LLM Engine)"]:::ai
    end

    %% ---------- Хранилища и инструменты ----------
    subgraph data_layer["Data & Tools Layer"]
        direction TB
        mcp["MCP Server"]:::tools
        db[(Wiki Docs / DB / Vector)]:::data
    end

    %% ---------- Сбор телеметрии ----------
    subgraph obs["Monitoring Engine"]
        prometheus["Prometheus + cAdvisor"]:::monitor
    end
end

%% ================= МАРШРУТЫ ДАННЫХ =================
kali -->|Direct API Attack| guard_in
user -->|Web Access| streamlit
streamlit -->|User Request| guard_in

guard_in --> router
router --> rag
router --> agent
router --> ollama

rag --> db
agent --> mcp
mcp --> db
agent <-->|Think / Act| ollama

ollama --> guard_out
guard_out -->|Clean Content| streamlit

%% ================= МАРШРУТЫ МОНИТОРИНГА =================
streamlit -.->|Метрики UI| prometheus
api -.->|Метрики API| prometheus
ollama -.->|Метрики GPU| prometheus

prometheus --> grafana

router -.->|Логи логики| langfuse
guard_out -.->|Логи фильтрации| langfuse

admin -.->|Анализ безопасности| grafana
admin -.->|Анализ безопасности| langfuse

%% ================= СТИЛИ =================
classDef attacker fill:#ffd6d6,stroke:#c92a2a,stroke-width:2px,color:#000;
classDef user fill:#dbeafe,stroke:#1d4ed8,stroke-width:1px,color:#000;
classDef admin fill:#f3f0ff,stroke:#845ef7,stroke-width:2px,color:#000;
classDef ui fill:#e0f7fa,stroke:#006064,stroke-width:2px,color:#000;
classDef api fill:#ede9fe,stroke:#6d28d9,stroke-width:2px,color:#000;
classDef ai fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#000;
classDef data fill:#fff3bf,stroke:#f08c00,stroke-width:2px,color:#000;
classDef tools fill:#ffedd5,stroke:#ea580c,stroke-width:2px,color:#000;
classDef monitor fill:#e5e7eb,stroke:#374151,stroke-width:2px,color:#000;
