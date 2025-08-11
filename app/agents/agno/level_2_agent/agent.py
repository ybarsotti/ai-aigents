from agno.agent import Agent
from agno.knowledge.url import UrlKnowledge
from agno.embedder.google import GeminiEmbedder
from agno.models.google import Gemini
from agno.storage.sqlite import SqliteStorage
from agno.vectordb.lancedb import LanceDb, SearchType

model = Gemini(
    id="gemini-1.5-flash",
    vertexai=False,
)

knowledge = UrlKnowledge(
    urls=["https://docs.agno.com/introduction.md"],
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="agno_docs",
        search_type=SearchType.hybrid,
        embedder=GeminiEmbedder(id="gemini-embedding-001", dimensions=1536),
    ),
)

storage = SqliteStorage(table_name="agent_sessions", db_file="tmp/agent.db")

agent = Agent(
    name="Agno Assist",
    model=model,
    instructions=[
        "Search your knowledge before answering the question.",
        "Only include the output in your response. No other text.",
    ],
    knowledge=knowledge,
    storage=storage,
    add_datetime_to_instructions=True,
    # Add the chat history to the messages
    add_history_to_messages=True,
    # Number of history runs
    num_history_runs=3,
    markdown=True,
)

if __name__ == "__main__":
    # Load the knowledge base, comment out after first run
    # Set recreate to True to recreate the knowledge base if needed
    # agent.knowledge.load(recreate=False)
    agent.print_response("What is Agno?", stream=True)
