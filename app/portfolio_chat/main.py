import os
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse
from slowapi.middleware import SlowAPIMiddleware
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

DATA_DIR = "./data"

app = FastAPI()
header_scheme = APIKeyHeader(name="x-key")


def init_llm():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vector_store = Chroma(
        collection_name="yuri_data_1",
        embedding_function=embeddings,
        persist_directory="./chroma_data",
    )

    retriever = vector_store.as_retriever(search_kwargs={"k": 4})

    with open(
        "./prompts/system_prompt.txt", "r", encoding="utf-8"
    ) as llm_instructions_f:
        system_instructions = llm_instructions_f.read()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_instructions,
            ),
            ("human", "{input}"),
        ]
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.5,
        max_tokens=300,
        max_retries=2,
    )

    combine_docs_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
    return create_retrieval_chain(retriever, combine_docs_chain)


class Question(BaseModel):
    query: str


def check_api_key(key: str):
    """
    This key is kinda exposed, but no problem.
    """
    if key != os.environ.get("API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key",
        )


limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    lambda request, exc: JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
    ),
)

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://portfolio-v2-pearl-one.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["x-key"],
)


@app.post("/chat")
@limiter.limit("30/minute")
def chat(request: Request, q: Question, key: str = Depends(header_scheme)):
    check_api_key(key)
    llm = init_llm()
    result = llm.invoke({"input": q.query})
    return {"response": result["answer"]}
