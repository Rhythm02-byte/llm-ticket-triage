import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("run_eval", Path(__file__).parents[1] / "eval" / "run_eval.py")
run_eval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_eval)


def test_score_counts_each_field_and_failures():
    tickets = [
        {"category": "safety", "urgency": "high", "language": "en"},
        {"category": "feedback", "urgency": "low", "language": "de"},
        {"category": "account", "urgency": "high", "language": "en"},
    ]
    predictions = [
        {"category": "safety", "urgency": "high", "language": "en"},
        {"category": "feedback", "urgency": "medium", "language": "de"},
        None,
    ]

    scores = run_eval.score(tickets, predictions)

    assert scores["category"] == 2 / 3
    assert scores["urgency"] == 1 / 3
    assert scores["category_and_urgency"] == 1 / 3
    assert scores["failed"] == 1


def test_labelled_set_is_balanced_and_valid():
    tickets = run_eval.load_tickets()
    categories = {t["category"] for t in tickets}

    assert len(tickets) == 30
    assert categories == {"connectivity", "app_bug", "navigation", "account", "safety", "feedback"}
    assert {t["urgency"] for t in tickets} == {"high", "medium", "low"}
    assert len({t["id"] for t in tickets}) == 30


def test_route_metrics_separate_missed_and_false_escalations():
    tickets = [
        {"id": "a", "category": "safety", "urgency": "high", "language": "en"},
        {"id": "b", "category": "navigation", "urgency": "medium", "language": "en"},
        {"id": "c", "category": "feedback", "urgency": "low", "language": "en"},
    ]
    predictions = [
        {"category": "account", "urgency": "medium", "language": "en"},    # needed a person, went to a queue
        {"category": "navigation", "urgency": "high", "language": "en"},   # escalated without needing it
        {"category": "feedback", "urgency": "low", "language": "en"},
    ]

    metrics = run_eval.route_metrics(tickets, predictions)

    assert metrics["escalations_expected"] == 1
    assert metrics["escalations_caught"] == 0
    assert metrics["missed_escalations"] == ["a"]
    assert metrics["false_escalations"] == ["b"]
    assert metrics["route_accuracy"] == 1 / 3
