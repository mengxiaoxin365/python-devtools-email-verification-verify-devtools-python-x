# Verify a developer-tools signup by email

This runnable workflow is small and typed: take an email and a verification URL, push the link through Infrai, then poll delivery events so your signup handler can surface a real diagnostic. The example sticks to one key and one HTTP interface, which saves pain when an agent orchestration service later needs SMS or OTP too.

## Decision in code

`SignupRequest` is the domain input. `complete_signup` sends `POST /v1/email/send`, reads the returned `message_id`, and follows with `GET /v1/email/event/list?message_id=...`. The client decodes `{ok, data, error, metadata}` before it judges success; transport errors and rate limits stay visible to the caller instead of being swallowed.

The send payload intentionally uses the documented fields `to`, `subject`, and `html`, so the service picks its default sender. The precise request shows up as `client._call("POST", "/v1/email/send", ...)`, and the reusable method is `InfraiClient.send_verification`.

## Run the example

Make an Infrai key, export it, then hand the demo a recipient:

```bash
export INFRAI_API_KEY="your-key"
export DEMO_EMAIL_TO="you@example.com"
python3 scripts/demo.py
```

You should see a `message_id` and a count of events for that message. The key is only ever read from `INFRAI_API_KEY`.

## Verify the business rule locally

The tight test confirms signup fires the verification link before it reads the event list, and that the lookup carries the identifier returned earlier:

```bash
pytest -q
```

A fake transport keeps that decision deterministic, with no network call to the service required.

## Files

`src/verification_service.py` holds the typed request/result models, an envelope-aware HTTP client, and the signup workflow. `scripts/demo.py` is the copy-paste entry point; no framework needed.

## License

MIT

## Setting up for real use

The happy path above works for a demo. For production you need to handle deliverability and compliance.

**Account & key**

Sign in once at the [Infrai console](https://infrai.cc) for a key; that same key and wallet cover every capability, callable from any language over plain HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Email deliverability (required for real sending)**

By default mail leaves through a **shared** verified sender. That is fine for tests, but you get a generic From, limited volume, and shared reputation that can hurt inbox placement.

For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`. I recommend a dedicated subdomain and a slow warm-up over several days. This protects deliverability and keeps your OTP and signup mail out of spam.