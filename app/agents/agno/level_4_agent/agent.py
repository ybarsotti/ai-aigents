from agno.agent import Agent
from agno.models.google import Gemini
from agno.team.team import Team
from agno.tools.serper import SerperTools
from agno.tools.reasoning import ReasoningTools
from agno.tools.yfinance import YFinanceTools


model = Gemini(
    id="gemini-1.5-flash",
    vertexai=False,
)

web_agent = Agent(
    name="Web Search Agent",
    role="Handle web search requests, general research and web scrapping.",
    model=model,
    # Changing to serper since duck duck go is not working properly.
    tools=[SerperTools()],
    instructions="Always include sources",
    add_datetime_to_instructions=True,
    monitoring=True
)

finance_agent = Agent(
    name="Finance Agent",
    role="Handle financial data requests and market analysis",
    model=model,
    tools=[YFinanceTools(stock_price=True, stock_fundamentals=True,analyst_recommendations=True, company_info=True)],
    instructions=[
        "Use tables to display stock prices, fundamentals (P/E, Market Cap), and recommendations.",
        "Clearly state the company name and ticker symbol.",
        "Focus on delivering actionable financial insights.",
    ],
    add_datetime_to_instructions=True,
    monitoring=True
)

reasoning_finance_team = Team(
    name="Reasoning Finance Team",
    mode="coordinate",
    model=model,
    members=[web_agent, finance_agent],
    tools=[ReasoningTools(add_instructions=True)],
    instructions=[
        "Collaborate to provide comprehensive financial and investment insights",
        "Consider both fundamental analysis and market sentiment",
        "Use tables and charts to display data clearly and professionally",
        "Present findings in a structured, easy-to-follow format",
        "Only output the final consolidated analysis, not individual agent responses",
    ],
    markdown=True,
    show_members_responses=True,
    enable_agentic_context=True,
    add_datetime_to_instructions=True,
    success_criteria="The team has provided a complete financial analysis with data, visualizations, risk assessment, and actionable investment recommendations supported by quantitative analysis and market research.",
    monitoring=True
)

if __name__ == "__main__":
    reasoning_finance_team.print_response("""Compare the tech sector giants (AAPL, GOOGL, MSFT) performance:
        1. Get current financial data for all three companies
        2. Analyze recent news affecting the tech sector
        3. Calculate comparative metrics and correlations
        4. Recommend portfolio allocation weights
 """,
        stream=True,
        show_full_reasoning=True,
        stream_intermediate_steps=True,
    )
