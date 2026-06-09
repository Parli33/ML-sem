from app.web.formatters import sort_predictions


def test_sort_predictions_places_general_risk_first() -> None:
    predictions = ["ah:0.2", "stroke:0.1", "general:0.3", "angina:0.4"]

    assert sort_predictions(predictions) == [
        "general:0.3",
        "ah:0.2",
        "angina:0.4",
        "stroke:0.1",
    ]
