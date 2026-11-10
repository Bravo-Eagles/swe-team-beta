FROM python:3.13-slim-trixie

WORKDIR /opt
COPY . .

COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

RUN uv sync --no-cache

CMD ["uv", "run", "streamlit", "run", "main.py"]
