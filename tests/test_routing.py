import json
from pathlib import Path

from triage.routing import route


def test_safety_always_escalates():
    assert route("safety", "low") == "escalate"


def test_high_urgency_escalates_in_any_category():
    assert route("account", "high") == "escalate"


def test_feedback_goes_to_backlog_and_the_rest_to_support():
    assert route("feedback", "low") == "product_backlog"
    assert route("navigation", "medium") == "support_queue"


def test_n8n_workflow_uses_the_same_rules():
    # The JavaScript in the workflow must keep the same conditions as route() above
    workflow = json.loads((Path(__file__).parents[1] / "n8n" / "workflows" / "ticket-triage.json").read_text())
    code = next(n for n in workflow["nodes"] if n["name"] == "Choose route")["parameters"]["jsCode"]
    assert "t.category === 'safety' || t.urgency === 'high'" in code
    assert "route = 'escalate'" in code
    assert "t.category === 'feedback'" in code and "route = 'product_backlog'" in code
