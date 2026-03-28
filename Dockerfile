FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APPOINTMENT_AGENT_DB_URL=sqlite:////app/data/appointment_agent.db

COPY pyproject.toml README.md /app/
COPY apps /app/apps
COPY tests /app/tests
COPY scripts /app/scripts
COPY docs /app/docs

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .[dev]

CMD ["uvicorn", "appointment_agent_shared.main:app", "--host", "0.0.0.0", "--port", "8080"]
