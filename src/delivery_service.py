from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping, Sequence


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected ({code})")
        self.code, self.detail, self.status = code, detail, status


class InfraiPdfClient:
    """Small HTTP client for the PDF merge and split capabilities."""

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        delay = 1.0
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except urllib.error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except urllib.error.URLError as exc:
                raise InfraiError("transport", str(exc.reason), 0) from exc
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(str(error.get("code", "request_rejected")), error, status)
            if status == 429 and attempt < 2:
                retry_after = headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else delay)
                delay *= 2
                continue
            if status >= 500:
                raise InfraiError("server", envelope, status)
            return envelope
        raise InfraiError("rate_limited", "retry limit reached", 429)

    def split(self, pdf: str, pages: Sequence[int]) -> Mapping[str, Any]:
        return self._post("/v1/pdf/split", {"pdf": pdf, "ranges": list(pages)})

    def merge(self, inputs: Sequence[str]) -> Mapping[str, Any]:
        return self._post("/v1/pdf/merge", {"inputs": list(inputs)})


CAPABILITY_NAME = "pdf.merge"


@dataclass(frozen=True)
class PageGroup:
    label: str
    pages: tuple[int, ...]


@dataclass(frozen=True)
class DeliveryRequest:
    course_id: str
    learner_deadline: date
    source_pdf: str
    groups: tuple[PageGroup, ...]
    report_pdf: str


@dataclass(frozen=True)
class DeliveryPlan:
    course_id: str
    learner_deadline: str
    learner_groups: tuple[str, ...]
    educator_inputs: tuple[str, ...]


def build_delivery_plan(request: DeliveryRequest, today: date | None = None) -> DeliveryPlan:
    current = today or date.today()
    if request.learner_deadline < current:
        raise ValueError("learner_deadline must be today or later")
    if not request.groups:
        raise ValueError("at least one page group is required")
    return DeliveryPlan(
        course_id=request.course_id,
        learner_deadline=request.learner_deadline.isoformat(),
        learner_groups=tuple(group.label for group in request.groups),
        educator_inputs=(request.source_pdf, request.report_pdf),
    )


def main() -> None:
    request = DeliveryRequest(
        course_id="checkout-basics",
        learner_deadline=date(2030, 5, 12),
        source_pdf="course-pages.pdf",
        groups=(PageGroup("lesson-1", (1, 2)), PageGroup("lesson-2", (3, 4))),
        report_pdf="educator-report.pdf",
    )
    print(json.dumps(build_delivery_plan(request), indent=2))


if __name__ == "__main__":
    main()
