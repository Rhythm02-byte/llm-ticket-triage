# Evaluation: mistral:7b

30 labelled tickets.

| Measure | Result |
|---|---|
| category accuracy | 87% |
| urgency accuracy | 77% |
| language accuracy | 93% |
| category_and_urgency accuracy | 70% |
| route accuracy | 73% |
| escalations caught | 9 of 10 |
| missed escalations | t23 |
| false escalations | 5 (t01, t02, t03, t05, t11) |
| invalid output after retry | 0 |
| median seconds per ticket | 2.5 |

## Urgency: label vs predicted

| Label | Predicted | Count |
|---|---|---|
| high | high | 9 |
| high | medium | 1 |
| low | low | 8 |
| low | medium | 1 |
| medium | high | 5 |
| medium | medium | 6 |

## Mismatches

- **t01** (en) urgency: medium → high. _My phone won't pair with the bike over Bluetooth anymore since yesterday. I tried restarting both._
- **t02** (de) urgency: medium → high. _Die App zeigt seit drei Tagen den falschen Tankstand an, die Daten werden nicht mehr synchronisiert._
- **t03** (en) urgency: medium → high. _The app says 'vehicle offline' even though the bike is parked right next to me with full signal._
- **t05** (en) urgency: medium → high. _Trip data from my last three rides never showed up in the app._
- **t08** (en) language: en → de. _The settings screen shows text in English even though my phone is set to German._
- **t11** (en) urgency: medium → high. _Turn-by-turn directions keep sending me onto a road that has been closed for weeks._
- **t19** (de) language: de → en. _Wo finde ich die Rechnungen für mein Abo?_
- **t23** (en) category: safety → connectivity, urgency: high → medium. _The app shows a warning that the tyre pressure sensor failed, then the warning disappears a minute later._
- **t25** (en) category: safety → account. _My emergency contact keeps getting removed from the app after every update._
- **t28** (en) category: feedback → app_bug, urgency: low → medium. _Please add a home screen widget that shows the fuel level._
- **t30** (en) category: feedback → navigation. _It would be nice to export trips as GPX files for other apps._
