FROM python:3.12-slim

WORKDIR /app

# git is needed only for scripts/setup_corpus.sh's optional clone at container
# start — the application itself never touches git at runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src
COPY data ./data
COPY scripts ./scripts

RUN pip install --no-cache-dir .

EXPOSE 8000

ENTRYPOINT ["scripts/docker-entrypoint.sh"]
CMD ["uvicorn", "vahiy_engine.main:app", "--host", "0.0.0.0", "--port", "8000"]
