FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/apps:/app/apps/shared/v1_0_0
ENV APPOINTMENT_AGENT_DB_URL=sqlite:////app/data/appointment_agent.db
ENV APPOINTMENT_AGENT_APP_HOST=0.0.0.0
ENV APPOINTMENT_AGENT_APP_PORT=8080
ENV APPOINTMENT_AGENT_LOG_LEVEL=info

COPY pyproject.toml README.md /app/
COPY apps /app/apps
COPY Docs /app/Docs
COPY scripts /app/scripts

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e '.[google]' && \
    chmod +x /app/scripts/docker_start.sh /app/scripts/docker_smoke_test.sh && \
    mkdir -p /app/data /app/test-results

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3)"

CMD ["/app/scripts/docker_start.sh"]
