"""Run the labelled tickets through a model and report how often each field matches the label.

    PYTHONPATH=src python eval/run_eval.py --model llama3.1:8b
    PYTHONPATH=src python eval/run_eval.py --model llama3.1:8b --from-results   # re-score saved replies
"""
import argparse
import json
import time
from collections import Counter
from pathlib import Path

from triage.llm import OllamaClient, TriageError
from triage.routing import route
from triage.safety import find_safety_terms

EVAL_DIR = Path(__file__).resolve().parent
RESULTS_DIR = EVAL_DIR / "results"
FIELDS = ("category", "urgency", "language")


def load_tickets(path=EVAL_DIR / "tickets.jsonl"):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def score(tickets, predictions):
    """Accuracy per field, and the share where category and urgency are both right."""
    n = len(tickets)
    result = {f: sum(p is not None and p[f] == t[f] for t, p in zip(tickets, predictions)) / n for f in FIELDS}
    result["category_and_urgency"] = sum(
        p is not None and p["category"] == t["category"] and p["urgency"] == t["urgency"]
        for t, p in zip(tickets, predictions)
    ) / n
    result["failed"] = sum(p is None for p in predictions)
    return result


def route_metrics(tickets, predictions, safety_net=False):
    """What the routing does with the model's answers, compared with routing the labels.

    A missed escalation is the costly error: a ticket that needed a person went to a queue.
    A false escalation costs staff time but is safe.
    With safety_net, the keyword safety net also runs on each ticket's text, as it does in the API.
    An invalid model reply still counts as unrouted: the API returns 502 and nothing is routed.
    """
    expected = [route(t["category"], t["urgency"]) for t in tickets]
    actual = [None if p is None else route(p["category"], p["urgency"],
                                           find_safety_terms(t["text"]) if safety_net else ())
              for t, p in zip(tickets, predictions)]
    should = [i for i, e in enumerate(expected) if e == "escalate"]
    return {
        "route_accuracy": sum(e == a for e, a in zip(expected, actual)) / len(tickets),
        "escalations_expected": len(should),
        "escalations_caught": sum(actual[i] == "escalate" for i in should),
        "missed_escalations": [tickets[i]["id"] for i in should if actual[i] != "escalate"],
        "false_escalations": [t["id"] for t, e, a in zip(tickets, expected, actual)
                              if e != "escalate" and a == "escalate"],
    }


def run_model(model, tickets):
    client = OllamaClient(model=model)
    predictions, latencies = [], []
    for ticket in tickets:
        started = time.perf_counter()
        try:
            predictions.append(client.triage(ticket["text"]).model_dump(mode="json"))
        except TriageError:
            predictions.append(None)
        latencies.append(round(time.perf_counter() - started, 2))
    return predictions, latencies


def write_report(model, tickets, predictions, latencies):
    slug = model.replace(":", "-")
    RESULTS_DIR.mkdir(exist_ok=True)
    with open(RESULTS_DIR / f"{slug}.jsonl", "w") as f:
        for t, p, s in zip(tickets, predictions, latencies):
            f.write(json.dumps({**t, "predicted": p, "seconds": s}, ensure_ascii=False) + "\n")

    scores, routes = score(tickets, predictions), route_metrics(tickets, predictions)
    net = route_metrics(tickets, predictions, safety_net=True)
    confusion = Counter((t["urgency"], p["urgency"]) for t, p in zip(tickets, predictions) if p)
    misses = [(t, p) for t, p in zip(tickets, predictions) if p is None or any(p[f] != t[f] for f in FIELDS)]

    lines = [f"# Evaluation: {model}", "", f"{len(tickets)} labelled tickets.", "",
             "| Measure | Result |", "|---|---|"]
    lines += [f"| {k} accuracy | {scores[k]:.0%} |" for k in (*FIELDS, "category_and_urgency")]
    lines += [f"| route accuracy | {routes['route_accuracy']:.0%} |",
              f"| escalations caught | {routes['escalations_caught']} of {routes['escalations_expected']} |",
              f"| missed escalations | {', '.join(routes['missed_escalations']) or 'none'} |",
              f"| false escalations | {len(routes['false_escalations'])} ({', '.join(routes['false_escalations']) or 'none'}) |",
              f"| invalid output after retry | {scores['failed']} |",
              f"| median seconds per ticket | {sorted(latencies)[len(latencies) // 2]:.1f} |",
              "", "## With the keyword safety net", "",
              "The same model replies, routed with the safety net in `src/triage/safety.py` switched on.", "",
              "| Measure | Result |", "|---|---|",
              f"| route accuracy | {net['route_accuracy']:.0%} |",
              f"| escalations caught | {net['escalations_caught']} of {net['escalations_expected']} |",
              f"| missed escalations | {', '.join(net['missed_escalations']) or 'none'} |",
              f"| false escalations | {len(net['false_escalations'])} ({', '.join(net['false_escalations']) or 'none'}) |",
              "", "## Urgency: label vs predicted", "", "| Label | Predicted | Count |", "|---|---|---|"]
    lines += [f"| {a} | {b} | {c} |" for (a, b), c in sorted(confusion.items())]
    lines += ["", "## Mismatches", ""]
    for t, p in misses:
        got = "invalid output" if p is None else ", ".join(f"{f}: {t[f]} → {p[f]}" for f in FIELDS if p[f] != t[f])
        lines.append(f"- **{t['id']}** ({t['language']}) {got}. _{t['text']}_")
    (RESULTS_DIR / f"{slug}.md").write_text("\n".join(lines) + "\n")
    return {**scores, **routes, "with_safety_net": net}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="llama3.1:8b")
    parser.add_argument("--from-results", action="store_true", help="re-score the saved replies instead of calling the model")
    args = parser.parse_args()

    tickets = load_tickets()
    if args.from_results:
        saved = [json.loads(line) for line in (RESULTS_DIR / f"{args.model.replace(':', '-')}.jsonl").read_text().splitlines()]
        predictions, latencies = [s["predicted"] for s in saved], [s["seconds"] for s in saved]
    else:
        predictions, latencies = run_model(args.model, tickets)

    summary = write_report(args.model, tickets, predictions, latencies)
    print(json.dumps({k: round(v, 3) if isinstance(v, float) else v for k, v in summary.items()}))


if __name__ == "__main__":
    main()
