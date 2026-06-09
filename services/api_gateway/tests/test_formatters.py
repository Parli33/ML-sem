from datetime import datetime, timezone

from app.web.formatters import format_local_datetime, sort_predictions


def test_sort_predictions_places_general_risk_first() -> None:
    predictions = ["ah:0.2", "stroke:0.1", "general:0.3", "angina:0.4"]

    assert sort_predictions(predictions) == [
        "general:0.3",
        "ah:0.2",
        "angina:0.4",
        "stroke:0.1",
    ]


def test_format_local_datetime_converts_utc_to_configured_timezone() -> None:
    value = datetime(2026, 6, 9, 4, 18, tzinfo=timezone.utc)

    assert format_local_datetime(value, "Asia/Krasnoyarsk") == "09.06.2026 11:18"
