import asyncio

import nest_asyncio
import streamlit as st
from agno.agent import Agent
from agno.memory.agent import AgentRun
from agno.tools.streamlit.components import check_password
from agno.utils.log import logger

from agents.trip_advisor import get_trip_advisor
from ui.css import CUSTOM_CSS
from ui.utils import (
    about_agno,
    add_message,
    display_tool_calls,
    example_inputs,
    initialize_agent_session_state,
    selected_model,
    session_selector,
    utilities_widget,
)

nest_asyncio.apply()

st.set_page_config(
    page_title="Trip Advisor: Your Travel Assistant",
    page_icon=":airplane:",
    layout="wide",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
agent_name = "trip_advisor"


async def header():
    st.markdown("<h1 class='heading'>Trip Advisor</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='subheading'>Your AI travel consultant for personalized destination recommendations, itinerary planning, and travel insights.</p>",
        unsafe_allow_html=True,
    )


async def body() -> None:
    ####################################################################
    # Initialize User and Session State
    ####################################################################
    user_id = st.sidebar.text_input(":technologist: Username", value="Traveler")

    ####################################################################
    # Model selector
    ####################################################################
    model_id = await selected_model()

    ####################################################################
    # Initialize Agent
    ####################################################################
    trip_advisor: Agent
    if (
        agent_name not in st.session_state
        or st.session_state[agent_name]["agent"] is None
        or st.session_state.get("selected_model") != model_id
    ):
        logger.info("---*--- Creating Trip Advisor Agent ---*---")
        trip_advisor = get_trip_advisor(user_id=user_id, model_id=model_id)
        st.session_state[agent_name]["agent"] = trip_advisor
        st.session_state["selected_model"] = model_id
    else:
        trip_advisor = st.session_state[agent_name]["agent"]

    ####################################################################
    # Load Agent Session from the database
    ####################################################################
    try:
        st.session_state[agent_name]["session_id"] = trip_advisor.load_session()
    except Exception:
        st.warning("Could not create Agent session, is the database running?")
        return

    ####################################################################
    # Load agent runs (i.e. chat history) from memory is messages is empty
    ####################################################################
    if trip_advisor.memory:
        agent_runs = trip_advisor.memory.runs
        if agent_runs is not None and len(agent_runs) > 0:  # type: ignore
            # If there are runs, load the messages
            logger.debug("Loading run history")
            # Clear existing messages
            st.session_state[agent_name]["messages"] = []
            # Loop through the runs and add the messages to the messages list
            for agent_run in agent_runs:
                if not isinstance(agent_run, AgentRun):
                    continue
                if agent_run.message is not None:
                    await add_message(agent_name, agent_run.message.role, str(agent_run.message.content))
                if agent_run.response is not None:
                    await add_message(
                        agent_name, "assistant", str(agent_run.response.content), agent_run.response.tools
                    )

    ####################################################################
    # Travel Planning Sidebar
    ####################################################################
    with st.sidebar:
        st.markdown("### :compass: Travel Planning Helper")
        
        # Quick destination input
        destination = st.text_input("Destination", placeholder="e.g., Tokyo, Japan")
        
        # Travel dates
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            end_date = st.date_input("End Date")
        
        # Travel preferences
        budget = st.selectbox("Budget Range", ["Budget ($)", "Mid-range ($$)", "Luxury ($$$)", "No preference"])
        travel_style = st.selectbox("Travel Style", ["Adventure", "Cultural", "Relaxation", "Business", "Family", "Romance", "Solo"])
        group_size = st.number_input("Group Size", min_value=1, max_value=20, value=2)
        
        # Quick action buttons
        if st.button("Plan My Trip"):
            if destination:
                travel_query = f"Plan a {travel_style.lower()} trip to {destination} for {group_size} people from {start_date} to {end_date} with a {budget.lower()} budget."
                await add_message(agent_name, "user", travel_query)
                st.rerun()
        
        if st.button("Get Destination Info"):
            if destination:
                info_query = f"Tell me about {destination} - what are the must-see attractions, best time to visit, local culture, and travel tips?"
                await add_message(agent_name, "user", info_query)
                st.rerun()

    ####################################################################
    # Get user input
    ####################################################################
    if prompt := st.chat_input("✈️ Ask me anything about travel - destinations, itineraries, tips, or recommendations!"):
        await add_message(agent_name, "user", prompt)

    ####################################################################
    # Show example inputs
    ####################################################################
    if len(st.session_state[agent_name]["messages"]) == 0:
        st.markdown("### :star: Try these travel queries:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🏖️ Beach Vacation"):
                example_query = "Plan a 7-day beach vacation for a couple with a mid-range budget. Suggest destinations with beautiful beaches, good food, and romantic activities."
                await add_message(agent_name, "user", example_query)
                st.rerun()
                
            if st.button("🏔️ Adventure Trip"):
                example_query = "I want to go on an adventure trip with hiking, outdoor activities, and stunning nature. Suggest destinations and create a 5-day itinerary."
                await add_message(agent_name, "user", example_query)
                st.rerun()
        
        with col2:
            if st.button("🏛️ Cultural Experience"):
                example_query = "Recommend a cultural destination rich in history, museums, and local traditions. I have 4 days and love art and architecture."
                await add_message(agent_name, "user", example_query)
                st.rerun()
                
            if st.button("👨‍👩‍👧‍👦 Family Trip"):
                example_query = "Plan a family-friendly trip for 2 adults and 2 kids (ages 8 and 12). We want activities for everyone and prefer destinations with good attractions for children."
                await add_message(agent_name, "user", example_query)
                st.rerun()
        
        with col3:
            if st.button("🍜 Food & Culture"):
                example_query = "I'm a foodie looking for the best culinary destinations. Suggest places with amazing local cuisine, food markets, and cooking experiences."
                await add_message(agent_name, "user", example_query)
                st.rerun()
                
            if st.button("💰 Budget Travel"):
                example_query = "Give me budget travel tips and suggest affordable destinations where I can have amazing experiences without spending too much money."
                await add_message(agent_name, "user", example_query)
                st.rerun()

    ####################################################################
    # Display agent messages
    ####################################################################
    for message in st.session_state[agent_name]["messages"]:
        if message["role"] in ["user", "assistant"]:
            _content = message["content"]
            if _content is not None:
                with st.chat_message(message["role"]):
                    # Display tool calls if they exist in the message
                    if "tool_calls" in message and message["tool_calls"]:
                        display_tool_calls(st.empty(), message["tool_calls"])
                    st.markdown(_content)

    ####################################################################
    # Generate response for user message
    ####################################################################
    last_message = st.session_state[agent_name]["messages"][-1] if st.session_state[agent_name]["messages"] else None
    if last_message and last_message.get("role") == "user":
        user_message = last_message["content"]
        logger.info(f"Responding to message: {user_message}")
        with st.chat_message("assistant"):
            # Create container for tool calls
            tool_calls_container = st.empty()
            resp_container = st.empty()
            with st.spinner(":thinking_face: Researching travel options..."):
                response = ""
                try:
                    # Run the agent and stream the response
                    run_response = await trip_advisor.arun(user_message, stream=True)
                    async for resp_chunk in run_response:
                        # Display tool calls if available
                        if resp_chunk.tools and len(resp_chunk.tools) > 0:
                            display_tool_calls(tool_calls_container, resp_chunk.tools)

                        # Display response
                        if resp_chunk.content is not None:
                            response += resp_chunk.content
                            resp_container.markdown(response)

                    # Add the response to the messages
                    if trip_advisor.run_response is not None:
                        await add_message(agent_name, "assistant", response, trip_advisor.run_response.tools)
                    else:
                        await add_message(agent_name, "assistant", response)
                except Exception as e:
                    logger.error(f"Error during agent run: {str(e)}", exc_info=True)
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    await add_message(agent_name, "assistant", error_message)
                    st.error(error_message)

    ####################################################################
    # Session selector
    ####################################################################
    await session_selector(agent_name, trip_advisor, get_trip_advisor, user_id, model_id)

    ####################################################################
    # About section
    ####################################################################
    await utilities_widget(agent_name, trip_advisor)


async def main():
    await initialize_agent_session_state(agent_name)
    await header()
    await body()
    await about_agno()


if __name__ == "__main__":
    if check_password():
        asyncio.run(main())