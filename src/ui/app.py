import os
from typing import Any

import requests
import streamlit as st


DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_CHAT_PATH = "/api/v1/chat"
REQUEST_TIMEOUT_SECONDS = 30


def build_api_chat_url() -> str:
    """Build full FastAPI chat endpoint URL from environment."""
    api_url = os.getenv("API_URL", DEFAULT_API_URL).rstrip("/")
    chat_path = os.getenv("API_CHAT_PATH", DEFAULT_CHAT_PATH)
    if not chat_path.startswith("/"):
        chat_path = f"/{chat_path}"
    return f"{api_url}{chat_path}"


def call_chat_api(user_query: str) -> dict[str, Any]:
    """Send user message to FastAPI and return parsed JSON response."""
    endpoint = build_api_chat_url()
    payload = {"query": user_query, "mode": "chat"}
    response = requests.post(endpoint, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


st.set_page_config(page_title="Smart Wiki UI", page_icon="🛡️", layout="centered")
st.title("🛡️ Smart Wiki Assistant")
st.caption("UI отправляет запросы только в FastAPI API Layer")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.subheader("Настройки API")
    st.code(build_api_chat_url(), language="text")
    st.caption("URL собирается из API_URL и API_CHAT_PATH")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Введите запрос в защищенный Wiki-чат")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Отправляю запрос в FastAPI..."):
            try:
                result = call_chat_api(prompt)
                answer = result.get("answer", "Пустой ответ от API.")
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except requests.HTTPError as err:
                status_code = err.response.status_code if err.response is not None else "unknown"
                message = f"Ошибка API ({status_code}). Запрос был отклонен или обработан с ошибкой."
                st.error(message)
                st.session_state.messages.append({"role": "assistant", "content": message})
            except requests.RequestException:
                message = (
                    "Не удалось подключиться к API. Проверь API_URL, API_CHAT_PATH и доступность FastAPI."
                )
                st.error(message)
                st.session_state.messages.append({"role": "assistant", "content": message})
