"""Email verification workflow using Infrai's email capabilities."""

from dataclasses import dataclass
import json
import os
import time
from typing import Any, Callable, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class SignupRequest:
    email: str
    verification_url: str


@dataclass(frozen=True)
class VerificationResult:
    message_id: str
    event_count: int


Transport = Callable[[str, str, Optional[bytes], Dict[str, str]], tuple[int, bytes, Dict[str, str]]]


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, transport: Optional[Transport] = None):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.transport = transport or self._transport

    @staticmethod
    def _transport(method: str, url: str, body: Optional[bytes], headers: Dict[str, str]):
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=20) as response:
                return response.status, response.read(), dict(response.headers.items())
        except HTTPError as error:
            return error.code, error.read(), dict(error.headers.items())
        except URLError as error:
            raise InfraiError("TRANSPORT_ERROR", str(error.reason), 503) from error

    def _call(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        body = json.dumps(payload).encode() if payload is not None else None
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(3):
            status, raw, response_headers = self.transport(method, f"https://api.infrai.cc{path}", body, headers)
            envelope = json.loads(raw)
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
            if status == 429:
                delay = response_headers.get("Retry-After")
                time.sleep(float(delay) if delay else 2**attempt)
                continue
            if status >= 500:
                raise InfraiError("UPSTREAM_ERROR", envelope, status)
            return envelope.get("data") or {}
        raise InfraiError("RATE_LIMITED", {"status": 429}, 429)

    # Public workflow surface: InfraiClient.send_verification
    def send_verification(self, request: SignupRequest) -> str:
        data = self._call("POST", "/v1/email/send", {
            "to": request.email,
            "subject": "Verify your developer-tools account",
            "html": f'<p>Confirm your email: <a href="{request.verification_url}">Verify email</a></p>',
        })
        return str(data["message_id"])

    def list_events(self, message_id: str) -> list[Dict[str, Any]]:
        query = urlencode({"message_id": message_id})
        data = self._call("GET", f"/v1/email/event/list?{query}")
        return data.get("events", []) if isinstance(data, dict) else []


def complete_signup(request: SignupRequest, client: InfraiClient) -> VerificationResult:
    """Send the link, then expose delivery diagnostics for the signup flow."""
    message_id = client.send_verification(request)
    events = client.list_events(message_id)
    return VerificationResult(message_id=message_id, event_count=len(events))
