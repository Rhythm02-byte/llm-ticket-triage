"""Rule-based safety net: finds safety terms in a ticket, whatever the model says.

Any match sends the ticket to a person. A false match only costs staff time, while a
missed safety ticket goes to a queue, so the patterns lean towards matching.
"""
import re

# Each label maps to the German and English patterns that trigger it.
# Patterns that look looser or stricter than you'd expect are explained inline.
SAFETY_TERMS = {
    "crash or fall detection": [
        r"crash[\s-]*(?:detection|sensor|alert)",
        r"fall[\s-]*detection",
        r"sturzerkennung",
        r"sturzsensor",
        r"\bsturz\b",            # not "Absturz" or "stürzt ab": those mean the app crashed
        r"gestürzt",
        r"unfallerkennung",
    ],
    "emergency call": [
        r"emergency",            # emergency call, contact, services, SOS
        r"\bsos\b",
        r"\be-?call\b",
        r"notruf",               # Notruf, Notrufnummer, Notrufkontakt
        r"notfall",              # Notfall, Notfallkontakt
    ],
    "accident": [
        r"\baccidents?\b",       # not "accidentally"
        r"\bcollisions?\b",
        r"unfall",
        r"kollision",
    ],
    "tyres": [
        r"\btyres?\b",
        r"\btires?\b",
        r"\btpms\b",
        r"(?<!g)(?<!st)reifen",  # Reifen, Vorderreifen, Reifendruck; not "zugreifen" or "Streifen"
    ],
    "brakes": [
        r"\bbrak(?:e|es|ed|ing)\b",
        r"\babs\b",
        r"brems",                # Bremse, Bremsen, Hinterradbremse, Notbremsung
    ],
}

_COMPILED = {
    label: [re.compile(p, re.IGNORECASE) for p in patterns] for label, patterns in SAFETY_TERMS.items()
}


def find_safety_terms(text):
    """The labels of every safety term the ticket mentions, in a fixed order. Empty if none."""
    return [label for label, patterns in _COMPILED.items() if any(p.search(text) for p in patterns)]
