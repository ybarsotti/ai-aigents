FROM python:3.11-slim

WORKDIR /app

ARG GOOGLE_API_KEY
ARG API_KEY
ARG PINECONE_API

ENV PINECONE_API=${PINECONE_API}
ENV GOOGLE_API_KEY=${GOOGLE_API_KEY}
ENV API_KEY=${API_KEY}

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]

