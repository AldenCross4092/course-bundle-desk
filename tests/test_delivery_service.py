from datetime import date

import pytest

from src.delivery_service import DeliveryRequest, InfraiPdfClient, PageGroup, build_delivery_plan


def test_split_serializes_pages_as_ranges(monkeypatch: pytest.MonkeyPatch) -> None:
    client = InfraiPdfClient(api_key="test-key")
    sent: dict[str, object] = {}

    def capture(path: str, body: dict[str, object]) -> dict[str, object]:
        sent.update({"path": path, "body": body})
        return {"ok": True}

    monkeypatch.setattr(client, "_post", capture)

    client.split("lessons.pdf", (1, 2, 5))

    assert sent == {
        "path": "/v1/pdf/split",
        "body": {"pdf": "lessons.pdf", "ranges": [1, 2, 5]},
    }


def test_future_deadline_keeps_learner_groups_and_report_inputs() -> None:
    request = DeliveryRequest(
        course_id="math-101",
        learner_deadline=date(2026, 9, 10),
        source_pdf="lessons.pdf",
        groups=(PageGroup("week-1", (1, 2)), PageGroup("week-2", (3,))),
        report_pdf="grades.pdf",
    )
    plan = build_delivery_plan(request, today=date(2026, 9, 6))
    assert plan.learner_groups == ("week-1", "week-2")
    assert plan.educator_inputs == ("lessons.pdf", "grades.pdf")


def test_past_deadline_is_rejected() -> None:
    request = DeliveryRequest("math-101", date(2026, 9, 5), "lessons.pdf", (PageGroup("week-1", (1,)),), "grades.pdf")
    with pytest.raises(ValueError, match="today or later"):
        build_delivery_plan(request, today=date(2026, 9, 6))
