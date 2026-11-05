import importlib.util
from pathlib import Path

import pytest

from triage.safety import find_safety_terms

spec = importlib.util.spec_from_file_location("run_eval", Path(__file__).parents[1] / "eval" / "run_eval.py")
run_eval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_eval)


@pytest.mark.parametrize("text, label", [
    ("My emergency contact keeps getting removed from the app.", "emergency call"),
    ("The tyre pressure sensor failed, then the warning disappeared.", "tyres"),
    ("Tire pressure shows 0 psi on the rear wheel.", "tyres"),
    ("Crash detection didn't trigger after my fall.", "crash or fall detection"),
    ("The ABS warning light came on during the ride.", "brakes"),
    ("I was braking hard and the app logged a fault.", "brakes"),
    ("I had an accident and the app sent nothing.", "accident"),
    ("Die Sturzerkennung lässt sich nicht einschalten.", "crash or fall detection"),
    ("Der Notruf wurde ohne Grund ausgelöst.", "emergency call"),
    ("Mein Notfallkontakt ist verschwunden.", "emergency call"),
    ("Der Reifendruck am Vorderreifen wird falsch angezeigt.", "tyres"),
    ("Die Hinterradbremse quietscht laut.", "brakes"),
    ("Ich hatte gestern einen Unfall.", "accident"),
])
def test_safety_terms_are_found_in_german_and_english(text, label):
    assert label in find_safety_terms(text)


@pytest.mark.parametrize("text", [
    "The app crashes immediately every time I open it.",
    "Die App stürzt beim Start ab, nach jedem Absturz muss ich mich neu anmelden.",
    "Ich kann nicht mehr auf mein Konto zugreifen.",
    "Oben in der App ist ein grauer Streifen.",
    "I accidentally deleted a saved route.",
    "Please add a widget that shows the fuel level.",
])
def test_everyday_words_that_contain_a_safety_term_do_not_match(text):
    assert find_safety_terms(text) == []


def test_labelled_set_safety_tickets_are_all_caught_and_nothing_else_is_flagged():
    # The patterns were written after seeing these tickets, so this guards against
    # regressions. It is not an independent accuracy measure.
    for ticket in run_eval.load_tickets():
        flagged = bool(find_safety_terms(ticket["text"]))
        assert flagged == (ticket["category"] == "safety"), ticket["id"]
