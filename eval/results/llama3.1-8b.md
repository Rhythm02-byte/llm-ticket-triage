# Evaluation: llama3.1:8b

30 labelled tickets.

| Measure | Result |
|---|---|
| category accuracy | 93% |
| urgency accuracy | 80% |
| language accuracy | 97% |
| category_and_urgency accuracy | 80% |
| route accuracy | 87% |
| escalations caught | 9 of 10 |
| missed escalations | t25 |
| false escalations | 3 (t02, t03, t11) |
| invalid output after retry | 0 |
| median seconds per ticket | 2.5 |

## With the keyword safety net

The same model replies, routed with the safety net in `src/triage/safety.py` switched on.

| Measure | Result |
|---|---|
| route accuracy | 90% |
| escalations caught | 10 of 10 |
| missed escalations | none |
| false escalations | 3 (t02, t03, t11) |

## Urgency: label vs predicted

| Label | Predicted | Count |
|---|---|---|
| high | high | 8 |
| high | medium | 2 |
| low | low | 9 |
| medium | high | 3 |
| medium | low | 1 |
| medium | medium | 7 |

## Mismatches

- **t02** (de) urgency: medium → high. _Die App zeigt seit drei Tagen den falschen Tankstand an, die Daten werden nicht mehr synchronisiert._
- **t03** (en) urgency: medium → high. _The app says 'vehicle offline' even though the bike is parked right next to me with full signal._
- **t08** (en) category: app_bug → account, urgency: medium → low, language: en → de. _The settings screen shows text in English even though my phone is set to German._
- **t11** (en) urgency: medium → high. _Turn-by-turn directions keep sending me onto a road that has been closed for weeks._
- **t23** (en) urgency: high → medium. _The app shows a warning that the tyre pressure sensor failed, then the warning disappears a minute later._
- **t25** (en) category: safety → account, urgency: high → medium. _My emergency contact keeps getting removed from the app after every update._
