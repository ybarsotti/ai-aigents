from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.yfinance import YFinanceTools

model = Gemini(
    id="gemini-1.5-flash",
    vertexai=False,
)

agent = Agent(
    model=model,
    tools=[YFinanceTools(stock_price=True)],
    instructions="Use tables to display data. Don't include any other text.",
    markdown=True,
    debug_mode=True,
)

agent.print_response("What is the stock price of Apple?", stream=True)
