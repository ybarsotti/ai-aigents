FROM python:3.11-slim

WORKDIR /app

ARG GOOGLE_API_KEY
ARG API_KEY

ENV GOOGLE_API_KEY=${GOOGLE_API_KEY}
ENV API_KEY=${API_KEY}

RUN apt-get update && \
    apt-get install -y sqlite3 libsqlite3-dev gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]

