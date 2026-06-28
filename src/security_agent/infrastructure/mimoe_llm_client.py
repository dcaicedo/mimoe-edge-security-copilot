import os
from typing import List, Optional

import requests


_DEFAULT_BASE_URL   = "http://localhost:11434"
_DEFAULT_CHAT_MODEL = "llama3.2"
_DEFAULT_TIMEOUT    = 120


class MimoeLLMClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> None:
        resolved_base = (base_url or os.getenv("MIMOE_BASE_URL", _DEFAULT_BASE_URL)).rstrip("/")
        api_root      = resolved_base if resolved_base.endswith("/v1") else f"{resolved_base}/v1"
        self._url     = f"{api_root}/chat/completions"
        self._model   = model   or os.getenv("MIMOE_CHAT_MODEL", _DEFAULT_CHAT_MODEL)
        self._api_key = api_key if api_key is not None else os.getenv("MIMOE_API_KEY", "")
        self._timeout = timeout

    def generate(self, messages: List[dict]) -> str:
        headers: dict = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        try:
            response = requests.post(
                self._url,
                json={"model": self._model, "messages": messages},
                headers=headers,
                timeout=self._timeout,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"LLM request timed out after {self._timeout}s — is mimOE running at {self._url}?"
            )
        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(f"Could not connect to mimOE at {self._url}: {exc}")
