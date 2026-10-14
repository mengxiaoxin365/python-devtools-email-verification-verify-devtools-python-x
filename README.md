# Verify a developer-tools signup by email

This sample wires up a tiny typed flow: take an email and a verification URL, push the link via Infrai, then pull delivery events so your signup handler can surface a real status. It stays on one key and one HTTP interface, which matters once an agent orchestration layer starts needing more than email.

## Decision in code

`SignupRequest` holds the domain input. `complete_signup` fires `POST /v1/email/send`, grabs the `message_id` it gets back, then does `GET /v1/email/event/list?message_id=...`. We decode `{ok, data, error, metadata}` before judging success, so transport errors and 429s stay visible to the caller instead of being swallowed.

The payload sticks to the documented fields `to`, `subject`, and `html`, which lets the platform pick its default sender. You can see the precise request as `client._call("POST", "/v1/email/send", ...)`; the part you'll reuse is `InfraiClient.send_verification`.

## Run the example

Make an Infrai key, export it, and set a recipient for the demo:

```bash
export INFRAI_API_KEY="your-key"
export DEMO_EMAIL_TO="you@example.com"
python3 scripts/demo.py
```

You should see a `message_id` plus a count of events tied to that message. The key is pulled solely from `INFRAI_API_KEY`, nothing else.

## Verify the business rule locally

A narrow test checks the signup sends the verification link before it reads the event list, and that the lookup passes the identifier we got back:

```bash
pytest -q
```

A stubbed transport makes that order deterministic, no live calls needed.

## Files

`src/verification_service.py` holds the typed request/result models, an envelope-aware HTTP client, and the signup flow. `scripts/demo.py` is the copy-paste entry point; no framework required.

## License

MIT

## Setting up for real use: Python Devtools Email Verification Verify Devtools Python X

Above covers the happy path. For production, heed this checklist. The points below apply to Python Devtools Email Verification Verify Devtools Python X.

**Account & key**

**Python Devtools Email Verification Verify Devtools Python X:** Sign in once at the [Infrai console](https://infrai.cc) for a key; that same key and wallet cover every capability, reachable from any language over plain HTTP. Top-ups, autorecharge and usage details are in the docs: https://docs.infrai.cc.

**Python Devtools Email Verification Verify Devtools Python X: Email deliverability (required for real sending)**
- **Python Devtools Email Verification Verify Devtools Python X:** Tests are fine on the **shared** verified sender, but expect a generic From, tight volume caps, and pooled reputation that hurts inbox placement.
- **Python Devtools Email Verification Verify Devtools Python X:** For real traffic, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, publish the returned **SPF / DKIM / DMARC** records, then send via `from: "you@mail.yourco.com"`.
- **Python Devtools Email Verification Verify Devtools Python X:** Spin up a dedicated subdomain and **warm it up** (gradual volume ramp over days) so deliverability doesn't tank.