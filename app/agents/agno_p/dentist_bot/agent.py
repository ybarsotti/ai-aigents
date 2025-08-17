from agno.agent import Agent
from agno.models.google import Gemini
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.tools import tool
from agno.tools.user_control_flow import UserControlFlowTools
from agno.storage.sqlite import SqliteStorage
from agno.agent import Agent

agent_storage: str = "tmp/agents.db"
user_id = "ava"

model = Gemini(
    id="gemini-1.5-flash",
    vertexai=False,
)

memory = Memory(
    model=model,
    db=SqliteMemoryDb(table_name="patient_memories", db_file=agent_storage),
    delete_memories=True,
    clear_memories=True,
)
storage = SqliteStorage(table_name="agent_sessions", db_file=agent_storage)


@tool(requires_user_input=True, user_input_fields=["name", "cpf", "phone"])
def collect_user_info(agent: Agent, name: str, cpf: str, phone: str) -> str:
    """Collect user information for support ticket."""
    agent.session_state["user_name"] = name
    agent.session_state["user_cpf"] = cpf
    agent.session_state["user_phone"] = phone
    return f"Collected info - Name: {name}, Cpf: {cpf}, Phone: {phone}"


clinic_agent = Agent(
    model=model,
    session_state={
        "user_name": "",
        "user_cpf": "",
        "user_phone": "",
        "conversation_stage": "welcome",
    },
    tools=[UserControlFlowTools(), collect_user_info],
    storage=storage,
    memory=memory,
    instructions="""
    You are a helpful customer care agent for a clinica. Follow this workflow:
    1. Welcome the user warmly saying about the clinic and ask for their information.
    2. Collect their name, telephone and cpf if not already stored
    3. Ask about their issue or how you can help
    4. Provide assistance or create support tickets as needed
    
    Current user info: {user_name}, {user_cpf}, {user_phone}
    """,
    enable_user_memories=True,
    add_history_to_messages=True,
    num_history_runs=3,
    add_state_in_messages=True,
    read_chat_history=True,
    markdown=True,
)
