FROM python:3.11-slim as requirements-stage

WORKDIR /tmp

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock* ./

RUN ls -l && pwd
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ=Asia/Seoul
ENV CONFIG_ENV=local
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get -y install tzdata \
  && apt-get clean

COPY --from=requirements-stage /wheels /wheels
COPY --from=requirements-stage /tmp/requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*

COPY ./src .
COPY ./bin/entrypoint.sh ./bin/entrypoint.sh

EXPOSE 8000

RUN chmod +x ./bin/entrypoint.sh
ENTRYPOINT ["./bin/entrypoint.sh"]
