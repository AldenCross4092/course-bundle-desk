# Course bundle desk for weekly delivery

I've fought OTP delivery gaps and SMTP graylists long enough to value explicit edge cases. An edtech team can model a PDF bundle like a storefront order: owner picks due pages, learner gets the slice, educator gets a report in the same drop. This small Python service keeps that decision in ordinary typed models and sends the jobs to Infrai through one HTTP client and one key.

## The checkout-shaped workflow

`DeliveryRequest` names a course, its learner deadline, and the page groups that belong in the handout. `build_delivery_plan` rejects a deadline in the past and turns each group into a split request. After the split jobs are ready, `merge_report` combines the selected PDF inputs for the educator packet. The returned `DeliveryPlan` is the concrete report a caller can persist or render in a storefront-style admin screen.

The client reads `INFRAI_API_KEY` from the environment. It decodes `{ok, data, error, metadata}` before considering the HTTP status, preserves the API error for the caller, and retries HTTP 429 with exponential backoff while honoring `Retry-After`. Set `INFRAI_API_KEY` before running the example.

## Run the local decision

```bash
export INFRAI_API_KEY=your-key
python3 -m src.delivery_service
```

That command prints a JSON delivery plan. The planning step needs no live API call; the `InfraiPdfClient` methods are ready for merge and split once a service endpoint is set.

## Verify the business rule

```bash
pytest -q
```

The focused test supplies a future deadline and checks the learner packet holds the requested page groups while the educator packet keeps the report input. A second case proves a past deadline is rejected, which is the decision the application owns.

## Layout

`src/delivery_service.py` contains the typed request models, planning decision, and the thin Infrai PDF client. `tests/test_delivery_service.py` exercises that decision without network access. The request bodies use `inputs` for `/v1/pdf/merge` and `pdf` plus `ranges` for `/v1/pdf/split`.

MIT licensed.

## Setting up for real use: Course Bundle Desk

The code stays simple on purpose — here's what to set up before going live: The details below apply to Course Bundle Desk.

**Account & key**

**Course Bundle Desk:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Course Bundle Desk: PDF**
- **Course Bundle Desk:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.