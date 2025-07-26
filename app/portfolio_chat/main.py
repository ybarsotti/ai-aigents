import os
import asyncio

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from langchain.agents.output_parsers import JSONAgentOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.render import render_text_description_and_args
from langchain.agents.format_scratchpad import format_log_to_str
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from langchain.agents import AgentExecutor
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse
from telegram import Bot

load_dotenv()

app = FastAPI()

header_scheme = APIKeyHeader(name="x-key")
agent: AgentExecutor
telegram_bot = Bot(token=os.getenv("TELEGRAM_API_KEY"))


class Message(BaseModel):
    """Sends message to Yuri."""

    name: str = Field(description="Name of the person sending the message")
    message: str = Field(description="Message to be sent", example="Hello, world!")


@tool("send_message-tool", args_schema=Message)
async def send_message(name: str, message: str) -> str:
    """Sends message."""
    final_msg = f"📬 Message from {name} via agent\n\n{message}"
    asyncio.create_task(
        telegram_bot.send_message(chat_id=os.getenv("TELEGRAM_CHAT_ID"), text=final_msg)
    )
    return "Message sent successfully!"


def init_agent() -> AgentExecutor:
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

    @tool
    def contextual_search(input: str) -> str:
        """Search for relevant documents about Yuri and return a summary."""
        documents = retriever.invoke(input)
        if not documents:
            return "No relevant documents found."
        combined_text = "\n\n".join(doc.page_content for doc in documents)
        return combined_text

    all_tools = [send_message, contextual_search]

    hooman_prompt = """{input}
    {agent_scratchpad}
    (reminder to always respond in a JSON blob)
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_instructions.strip(),
            ),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", hooman_prompt),
        ]
    )
    prompt = prompt.partial(
        tools=render_text_description_and_args(list(all_tools)),
        tool_names=", ".join([t.name for t in all_tools]),
    )

    llm = ChatOpenAI(
        model="gpt-4.1-nano",
        temperature=0.3,
        max_tokens=150,
        max_retries=2,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    chain = (
        RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_log_to_str(x["intermediate_steps"]),
        )
        | prompt
        | llm
        | JSONAgentOutputParser()
    )

    agent_executor = AgentExecutor(
        agent=chain,
        tools=all_tools,
        handle_parsing_errors=True,
        verbose=True,
        # memory=memory,
    )

    return agent_executor


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


@app.on_event("startup")
async def startup_event():
    global agent
    agent = init_agent()


@app.post("/chat", dependencies=[Depends(verify_token)])
@limiter.limit("12/minute")
async def chat(request: Request, q: Question):
    result = await agent.ainvoke({"input": q.query})
    return {"response": result["output"]}
