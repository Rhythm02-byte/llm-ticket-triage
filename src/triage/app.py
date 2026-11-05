"""HTTP API for ticket triage.

    PYTHONPATH=src uvicorn triage.app:app --port 8000
"""
import time

import httpx
from fastapi import Depends, FastAPI, HTTPException, Response, status

from triage.llm import OllamaClient, TriageError
from triage.safety import find_safety_terms
from triage.schema import TicketIn, TriageResponse

app = FastAPI(title="LLM Ticket Triage")


def get_client():
    return OllamaClient()


@app.get("/health")
def health(response: Response, client: OllamaClient = Depends(get_client)):
    if client.is_ready():
        return {"status": "ok", "model": client.model}
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "unavailable", "model": client.model}


@app.post("/triage", response_model=TriageResponse)
def triage(ticket: TicketIn, client: OllamaClient = Depends(get_client)):
    started = time.perf_counter()
    try:
        result = client.triage(ticket.text)
    except TriageError as error:
        raise HTTPException(status_code=502, detail=str(error))
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="model service is unreachable")
    latency_ms = int((time.perf_counter() - started) * 1000)
    return TriageResponse(
        **result.model_dump(),
        safety_terms=find_safety_terms(ticket.text),
        model=client.model,
        latency_ms=latency_ms,
    )
