# syntax=docker/dockerfile:1

FROM python:3.12-slim AS build
WORKDIR /workspace

RUN pip install --upgrade pip
COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --prefix=/install .

FROM python:3.12-slim AS runtime
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --home /app app

COPY --from=build /install /usr/local

USER app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fsS http://localhost:8080/actuator/health || exit 1

CMD ["python", "-m", "app"]
