FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh /uv-installer.sh

RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

COPY pyproject.toml . 

RUN uv sync
RUN npx @modelcontextprotocol/inspector --install

COPY . .

EXPOSE 8000
EXPOSE 6277
EXPOSE 6274

CMD ["uv", "run", "fastmcp", "run", "server.py", "--transport", "streamable-http", "--port", "8000"]

