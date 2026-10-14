import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.verification_service import InfraiClient, SignupRequest, complete_signup


def main() -> None:
    recipient = os.environ.get("DEMO_EMAIL_TO")
    if not recipient:
        raise SystemExit("DEMO_EMAIL_TO is required")
    result = complete_signup(
        SignupRequest(recipient, "https://developer-tools.example/verify?token=demo"),
        InfraiClient(),
    )
    print(f"verification queued: message_id={result.message_id} events={result.event_count}")


if __name__ == "__main__":
    main()
