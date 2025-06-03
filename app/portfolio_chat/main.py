import os
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

from pydantic import BaseModel
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

load_dotenv()

app = FastAPI()

header_scheme = APIKeyHeader(name="x-key")


def init_llm():
    index_name = "yuri-data"

    pc = Pinecone(api_key=os.getenv("PINECONE_KEY"))
    index = pc.Index(index_name)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = PineconeVectorStore(index=index, embedding=embeddings)

    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 3, "score_threshold": 0.5},
    )

    with open(
        "./prompts/system_prompt.txt", "r", encoding="utf-8"
    ) as llm_instructions_f:
        system_instructions = llm_instructions_f.read()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_instructions.strip(),
            ),
            ("human", "{input}"),
        ]
    )

    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.5,
        max_tokens=150,
        max_retries=2,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    combine_docs_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
    return create_retrieval_chain(retriever, combine_docs_chain)


class Question(BaseModel):
    query: str


def verify_token(x_key: str = Header(None)):
    if not x_key or x_key != os.environ.get("API_KEY"):
        raise HTTPException(status_code=401, detail="Token?")
    return True


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
    allow_origins=[
        "https://portfolio-v2-pearl-one.vercel.app",
        "https://www.yuribarsotti.tech",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["x-key"],
)


@app.post("/chat", dependencies=[Depends(verify_token)])
@limiter.limit("12/minute")
def chat(request: Request, q: Question):
    llm = init_llm()
    result = llm.invoke({"input": q.query})
    return {"response": result["answer"]}

