"""Custom promptfoo provider that normalizes both 200 and 403 API responses.

Set TARGET_IP env var to point at the Ubuntu server (default: localhost).
Example: TARGET_IP=192.168.56.10 npx promptfoo eval
"""

import json
import os
import requests


def call_api(prompt, options, context):
    target_ip = os.getenv("TARGET_IP", "localhost")
    api_port = os.getenv("API_PORT", "8000")
    default_url = f"http://{target_ip}:{api_port}/api/v1/chat"
    url = options.get("config", {}).get("url", default_url)
    try:
        resp = requests.post(
            url,
            json={"query": prompt, "mode": "chat"},
            timeout=15,
        )
        if resp.status_code == 403:
            detail = resp.json().get("detail", {})
            return {"output": json.dumps(detail, ensure_ascii=False)}
        resp.raise_for_status()
        return {"output": json.dumps(resp.json(), ensure_ascii=False)}
    except requests.RequestException as e:
        return {"error": str(e)}
