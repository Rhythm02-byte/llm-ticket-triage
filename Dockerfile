FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/

ENV PYTHONPATH=/app/src
# Ollama runs outside this container. On Docker Desktop, the host is reachable at host.docker.internal.
ENV OLLAMA_URL=http://host.docker.internal:11434
ENV OLLAMA_MODEL=llama3.1:8b

EXPOSE 8000
CMD ["uvicorn", "triage.app:app", "--host", "0.0.0.0", "--port", "8000"]
