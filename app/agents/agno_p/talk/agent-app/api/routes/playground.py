from os import getenv

from agno.playground import Playground

from agents.sage import get_sage
from agents.scholar import get_scholar
from teams.finance_researcher import get_finance_researcher_team
from teams.multi_language import get_multi_language_team
from workspace.dev_resources import dev_fastapi

######################################################
## Router for the Playground Interface
######################################################

sage_agent = get_sage(debug_mode=True)
scholar_agent = get_scholar(debug_mode=True)
finance_researcher_team = get_finance_researcher_team(debug_mode=True)
multi_language_team = get_multi_language_team(debug_mode=True)

# Create a playground instance
playground = Playground(agents=[sage_agent, scholar_agent], teams=[finance_researcher_team, multi_language_team])

# Note: playground.serve() should not be called during module import
# as it conflicts with the running uvicorn server. The playground router
# is accessible via playground.get_async_router() below.

playground_router = playground.get_async_router()
