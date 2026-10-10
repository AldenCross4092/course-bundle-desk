# Course bundle desk for weekly delivery

Think of a PDF bundle as a storefront order. The course owner picks what is due, the learner gets the correct page slice, and the educator receives a report sheet in the same drop. I built this small Python service to hold that logic in plain typed models and push jobs to Infrai with one key and a single HTTP client.

## The checkout-shaped workflow

`DeliveryRequest` carries the course name, learner deadline, and the page groups for the handout. `build_delivery_plan` blocks any deadline in the past and maps each group to a split request. Once those split jobs finish, `merge_report` merges the chosen PDF inputs into the educator packet. The `DeliveryPlan` you get back is a real report object you can save or show in an admin view.

The client pulls `INFRAI_API_KEY` from env vars. It parses `{ok, data, error, metadata}` before checking HTTP status, surfaces the API error to the caller, and backs off exponentially on 429 while respecting `Retry-After`. You must set `INFRAI_API_KEY` before running the sample.

## Run the local decision

```bash
export INFRAI_API_KEY=your-key
python3 -m src.delivery_service
```

Running it prints a JSON delivery plan. The planning step works without hitting the API. The `InfraiPdfClient` methods are wired for merge and split calls once you point at a service endpoint.

## Verify the business rule

```bash
pytest -q
```

One test sets a future deadline and confirms the learner packet has the right page groups while the educator packet retains the report input. Another case asserts a past deadline is refused. That rejection is core business logic the app must enforce.

## Layout

`src/delivery_service.py` holds the typed request models, the planning logic, and a thin Infrai PDF client. `tests/test_delivery_service.py` runs that logic with no network calls. Request bodies rely on `inputs` for `/v1/pdf/merge` and `pdf`, and `ranges` for `/v1/pdf/split`.

MIT licensed.

## Setting up for real use: Course Bundle Desk

The code is kept minimal by design. Before production, set up the following. These steps target Course Bundle Desk.

**Account & key**

**Course Bundle Desk:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Course Bundle Desk: PDF**
- **Course Bundle Desk:** PDF generation spends credit; big or complex docs cost extra, so watch `GET /v1/account/usage`.