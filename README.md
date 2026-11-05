# LLM Ticket Triage: local model + n8n

A self-hosted AI service that triages support tickets for a connected-vehicle app, in German and English. It runs a local model through Ollama, so no ticket leaves the machine. It returns validated JSON: category, urgency, language, and a one-line English summary. A rule-based safety net escalates any ticket that mentions crash detection, emergency calls, accidents, tyres or brakes, whatever the model says. An n8n workflow receives each ticket, calls the service, and routes it to `escalate`, `support_queue` or `product_backlog`.

```
POST /webhook/ticket  ──►  n8n (container)  ──►  triage API (container)  ──►  Ollama (local model)
                             │                      validates the JSON reply,
                             │                      runs the keyword safety net
                             ▼
                      Choose route ──► Reply: { category, urgency, language, summary, route }
                      Handle failure ──► Reply: 400 invalid ticket / 502 service unavailable
```

## Results

30 labelled tickets (12 German, 18 English, 5 per category), run at temperature 0 with a fixed seed.

| Measure | Llama 3.1 8B | Mistral 7B |
|---|---|---|
| Category accuracy | 93% | 87% |
| Urgency accuracy | 80% | 77% |
| Language accuracy | 97% | 93% |
| Category and urgency both right | 80% | 70% |
| Route accuracy | 87% | 73% |
| Escalations caught, model only | 9 of 10 | 9 of 10 |
| **Escalations caught, with safety net** | **10 of 10** | **10 of 10** |
| Route accuracy, with safety net | 90% | 77% |
| Escalations that weren't needed | 3 | 5 |
| Invalid output after one retry | 0 | 0 |
| Median time per ticket | 2.5 s | 2.6 s |

Full reports with every mismatch: [`eval/results/llama3.1-8b.md`](eval/results/llama3.1-8b.md) and [`eval/results/mistral-7b.md`](eval/results/mistral-7b.md).

### What the errors show

- **Each model missed one safety ticket.** Llama filed "my emergency contact keeps getting removed" as an account issue with medium urgency. Mistral filed a failing tyre-pressure warning as a connectivity issue. In both cases the ticket would go to a queue instead of a person. This is the most important result: the model alone is not safe enough to route safety tickets. The keyword safety net now catches both, and it flags none of the 20 tickets that aren't about safety, so it adds no unneeded escalations on this set.
- **Most other errors are on the safe side.** The commonest mistake is rating a medium ticket as high, for example a sync problem or a wrong route. That escalates tickets that didn't need it, which costs staff time but doesn't put anyone at risk.
- **One language error comes from the ticket's content.** Llama marked an English ticket as German because it says "my phone is set to German".

### What I'd add before real use

1. **A person reviewing every safety ticket**, and a sample of the rest, to measure accuracy on real tickets, and to find safety terms the keyword list misses.
2. **A larger, independently labelled test set.** These 30 tickets were written and labelled by me, which limits how far the numbers generalise. The safety net's 10 of 10 is the weakest number here: I wrote the keywords after seeing which tickets the models missed.

## How it works

- **`src/triage/schema.py`**: the allowed categories, urgency levels and languages, as Pydantic models.
- **`src/triage/llm.py`**: sends the ticket to Ollama with a system prompt and the JSON schema. Ollama constrains the reply to the schema, and the service validates it again. An invalid reply is retried once, then the request fails with 502. A category the schema doesn't allow is rejected, not passed on.
- **`src/triage/app.py`**: the FastAPI service. `POST /triage` returns the triage, the model name and the time taken. `GET /health` returns 503 unless Ollama answers and the model is installed.
- **`src/triage/safety.py`**: the keyword safety net. German and English patterns for crash and fall detection, emergency calls, accidents, tyres and brakes. The API returns the matches as `safety_terms` and leaves the model's category and urgency as they were, so a reviewer can see both what the model said and why the ticket was escalated. The patterns skip everyday words that contain a safety term, such as "Die App stürzt ab" (the app crashes), "zugreifen" (to access) and "accidentally".
- **`src/triage/routing.py`**: the routing rules. Safety, high urgency or any `safety_terms` match goes to `escalate`, feedback to `product_backlog`, everything else to `support_queue`. A test checks that the n8n workflow uses the same rules.
- **`n8n/workflows/ticket-triage.json`**: the workflow. Webhook → HTTP call to the service → route → reply. If the call fails, an error branch replies with 400 for an invalid ticket or 502 if the service is down.
- **`eval/`**: the labelled tickets and the evaluation script.

## Run it

You need Docker and Ollama.

```bash
ollama pull llama3.1:8b
docker compose up -d --build

# Load and publish the workflow, then restart n8n so it registers the webhook
docker compose exec n8n n8n import:workflow --input=/workflows/ticket-triage.json
docker compose exec n8n n8n publish:workflow --id=TicketTriage0001
docker compose restart n8n

curl -X POST localhost:5678/webhook/ticket -H 'content-type: application/json' \
  -d '{"text": "Die Sturzerkennung ist in der App plötzlich deaktiviert und lässt sich nicht wieder einschalten."}'
```

Reply:

```json
{"category": "safety", "urgency": "high", "language": "de",
 "summary": "Crash detection is disabled in the app and can't be reactivated.",
 "safety_terms": ["crash or fall detection"],
 "model": "llama3.1:8b", "latency_ms": 8182, "route": "escalate"}
```

The first request is slower because Ollama loads the model.

Without Docker:

```bash
conda create -n triage python=3.11 -y && conda activate triage
pip install -r requirements.txt
PYTHONPATH=src uvicorn triage.app:app --port 8000
```

Tests and evaluation:

```bash
pytest                                                    # no model or Docker needed
PYTHONPATH=src python eval/run_eval.py --model llama3.1:8b
PYTHONPATH=src python eval/run_eval.py --model llama3.1:8b --from-results   # re-score saved replies
```

Each report shows the routing twice: with the model alone and with the safety net.

If you imported the workflow before the safety net was added, run the `import:workflow` and `publish:workflow` commands again and restart n8n.

Settings: `OLLAMA_URL` (default `http://127.0.0.1:11434`) and `OLLAMA_MODEL` (default `llama3.1:8b`).

## Limits

- **Small, self-labelled test set.** 30 synthetic tickets, written and labelled by me. The system prompt was written before the evaluation and not changed after it, so the prompt isn't tuned to these tickets.
- **The safety net is a keyword list.** It misses misspellings and terms it doesn't know, for example "the bike won't stop". It also escalates when a safety term is mentioned in passing ("brakes are fine, but the map is wrong"), which is the safe direction. It only runs when the model returns a valid reply: if the model fails, the request fails with 502 and nothing is routed.
- **One run per model.** Temperature 0 and a fixed seed make the runs repeatable, but other phrasings of the same ticket could be classified differently.
- **Ollama ran on macOS.** The API and n8n run in Linux containers. On a Linux server Ollama runs natively, and only `OLLAMA_URL` changes.
- **No authentication.** The API and the webhook are open. This setup is for local use only.
- **n8n's editor needs an owner account.** The first visit to http://localhost:5678 asks you to create one. The workflow runs without it.
- **No real data.** The tickets are invented, and so is the app they describe.

## Project structure

```
src/triage/        schema, model client, API, safety net, routing rules
n8n/workflows/     the n8n workflow
eval/              labelled tickets, evaluation script, results
tests/             pytest suite (37 tests)
Dockerfile         the API image
docker-compose.yml the API and n8n
```
