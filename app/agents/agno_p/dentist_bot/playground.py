from agno.playground import Playground
from .agent import clinic_agent

playground_app = Playground(agents=[clinic_agent])
app = playground_app.get_app()

if __name__ == "__main__":
    playground_app.serve("dentist_bot.playground:app", reload=True)
