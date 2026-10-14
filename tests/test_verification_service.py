import json

from src.verification_service import InfraiClient, SignupRequest, complete_signup


def test_signup_sends_link_and_reads_events():
    calls = []

    def transport(method, url, body, headers):
        calls.append((method, url, json.loads(body) if body else None))
        if method == "POST":
            return 200, json.dumps({"ok": True, "data": {"message_id": "msg-42"}}).encode(), {}
        return 200, json.dumps({"ok": True, "data": {"events": [{"type": "queued"}]}}).encode(), {}

    result = complete_signup(
        SignupRequest("dev@example.com", "https://example.com/verify?t=abc"),
        InfraiClient(api_key="test-key", transport=transport),
    )
    assert result.message_id == "msg-42"
    assert result.event_count == 1
    assert calls[0][0] == "POST" and calls[0][1].endswith("/v1/email/send")
    assert calls[1][0] == "GET" and "message_id=msg-42" in calls[1][1]
