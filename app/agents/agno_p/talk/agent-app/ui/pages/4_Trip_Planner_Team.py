import asyncio

import nest_asyncio
import streamlit as st
from agno.team import Team
from agno.tools.streamlit.components import check_password
from agno.utils.log import logger

from teams.trip_planner import get_trip_planner_team
from ui.css import CUSTOM_CSS
from ui.utils import (
    about_agno,
    add_message,
    display_tool_calls,
    initialize_team_session_state,
    selected_model,
)

nest_asyncio.apply()

st.set_page_config(
    page_title="Trip Planner Team",
    page_icon=":luggage:",
    layout="wide",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
team_name = "trip_planner_team"


async def header():
    st.markdown("<h1 class='heading'>Trip Planner Team</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='subheading'>A specialized team of travel experts working together to create comprehensive trip plans.</p>",
        unsafe_allow_html=True,
    )


async def body() -> None:
    ####################################################################
    # Initialize User and Session State
    ####################################################################
    user_id = st.sidebar.text_input(":technologist: Username", value="Traveler")

    ####################################################################
    # Travel Planning Sidebar
    ####################################################################
    with st.sidebar:
        st.markdown("### :compass: Quick Trip Planner")
        
        # Destination and dates
        destination = st.text_input("Destination", placeholder="e.g., Paris, France")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            end_date = st.date_input("End Date")
        
        # Trip preferences
        trip_type = st.selectbox("Trip Type", [
            "Comprehensive Planning", 
            "Destination Research", 
            "Accommodation Focus", 
            "Itinerary Only", 
            "Budget Planning"
        ])
        
        travel_style = st.selectbox("Travel Style", [
            "Adventure", "Cultural", "Relaxation", "Business", 
            "Family", "Romance", "Solo", "Luxury", "Budget"
        ])
        
        group_size = st.number_input("Group Size", min_value=1, max_value=20, value=2)
        budget_range = st.selectbox("Budget Range", [
            "Budget ($)", "Mid-range ($$)", "Luxury ($$$)", "No preference"
        ])
        
        # Team coordination buttons
        if st.button("Plan Complete Trip"):
            if destination:
                comprehensive_query = f"""Plan a comprehensive {travel_style.lower()} trip to {destination} for {group_size} people from {start_date} to {end_date} with a {budget_range.lower()} budget.

Please coordinate your team to provide:
1. Destination research and cultural insights
2. Accommodation recommendations
3. Detailed day-by-day itinerary
4. Complete budget breakdown

I want a full travel plan that covers all aspects of the trip."""
                await add_message(team_name, "user", comprehensive_query)
                st.rerun()
        
        if st.button("Focus on Destination"):
            if destination:
                dest_query = f"Tell me everything I need to know about {destination} - attractions, culture, weather, safety, local tips, and best time to visit."
                await add_message(team_name, "user", dest_query)
                st.rerun()
        
        if st.button("Find Accommodations"):
            if destination:
                accom_query = f"Find the best accommodations in {destination} for {group_size} people with a {budget_range.lower()} budget. Include different options and booking recommendations."
                await add_message(team_name, "user", accom_query)
                st.rerun()

    ####################################################################
    # Model selector
    ####################################################################
    model_id = await selected_model()

    ####################################################################
    # Initialize Team
    ####################################################################
    team: Team
    if (
        team_name not in st.session_state
        or st.session_state[team_name]["team"] is None
        or st.session_state.get("selected_model") != model_id
    ):
        logger.info("---*--- Creating Trip Planner Team ---*---")
        team = get_trip_planner_team(user_id=user_id, model_id=model_id)
        st.session_state[team_name]["team"] = team
        st.session_state["selected_model"] = model_id
    else:
        team = st.session_state[team_name]["team"]

    ####################################################################
    # Load Team Session from the database
    ####################################################################
    try:
        st.session_state[team_name]["session_id"] = team.load_session()
    except Exception:
        st.warning("Could not create Team session, is the database running?")
        return

    ####################################################################
    # Get user input
    ####################################################################
    if prompt := st.chat_input("🌍 Ask our travel planning team anything - from destination research to complete trip planning!"):
        await add_message(team_name, "user", prompt)

    ####################################################################
    # Show example inputs
    ####################################################################
    if len(st.session_state[team_name]["messages"]) == 0:
        st.markdown("### :star: Try these team coordination examples:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🌟 Comprehensive Planning**")
            if st.button("Plan Japan Adventure"):
                example_query = """Plan a 10-day adventure trip to Japan for 2 people in spring. We love hiking, cultural experiences, and trying local food. Budget is mid-range.

Please coordinate your team to provide:
- Destination insights and cultural tips
- Accommodation recommendations in different cities
- Detailed itinerary with activities and transportation
- Complete budget breakdown"""
                await add_message(team_name, "user", example_query)
                st.rerun()
                
            if st.button("European Cities Tour"):
                example_query = """Plan a 2-week European cities tour visiting London, Paris, and Rome for a family of 4 (2 adults, 2 teens).

Team coordination needed:
- Research each destination's family attractions
- Find family-friendly accommodations
- Create an efficient itinerary with travel between cities
- Provide budget estimates for all aspects"""
                await add_message(team_name, "user", example_query)
                st.rerun()
        
        with col2:
            st.markdown("**🔍 Specialized Research**")
            if st.button("Iceland Deep Dive"):
                example_query = "I need comprehensive research on Iceland - best time to visit, must-see attractions, unique experiences, accommodation types, and budget considerations for a 7-day trip."
                await add_message(team_name, "user", example_query)
                st.rerun()
                
            if st.button("Luxury Maldives"):
                example_query = "Find the best luxury resorts in Maldives for a honeymoon. Compare options, amenities, and create a romantic itinerary with budget estimates."
                await add_message(team_name, "user", example_query)
                st.rerun()
        
        with col3:
            st.markdown("**💰 Budget-Focused Planning**")
            if st.button("Backpacker Southeast Asia"):
                example_query = "Plan a budget backpacking route through Thailand, Vietnam, and Cambodia for 3 weeks. Focus on budget accommodations, cheap eats, and free/low-cost activities."
                await add_message(team_name, "user", example_query)
                st.rerun()
                
            if st.button("Last-Minute Weekend"):
                example_query = "I need a last-minute weekend getaway within 3 hours of NYC. Find deals on accommodations and create a 2-day itinerary with budget estimates."
                await add_message(team_name, "user", example_query)
                st.rerun()

    ####################################################################
    # Team Member Info
    ####################################################################
    if len(st.session_state[team_name]["messages"]) == 0:
        st.markdown("---")
        st.markdown("### :busts_in_silhouette: Meet Your Trip Planning Team")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            **🌍 Destination Researcher**
            - Attraction & activity research
            - Cultural insights & customs
            - Weather & timing advice
            - Safety & practical info
            """)
        
        with col2:
            st.markdown("""
            **🏨 Accommodation Specialist**
            - Hotel & lodging recommendations
            - Location analysis
            - Booking strategies
            - Value comparisons
            """)
        
        with col3:
            st.markdown("""
            **📅 Itinerary Planner**
            - Day-by-day scheduling
            - Transportation coordination
            - Time optimization
            - Activity sequencing
            """)
        
        with col4:
            st.markdown("""
            **💰 Budget Advisor**
            - Cost breakdowns
            - Money-saving tips
            - Budget optimization
            - Price research
            """)

    ####################################################################
    # Display team messages
    ####################################################################
    for message in st.session_state[team_name]["messages"]:
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
    last_message = st.session_state[team_name]["messages"][-1] if st.session_state[team_name]["messages"] else None
    if last_message and last_message.get("role") == "user":
        user_message = last_message["content"]
        logger.info(f"Responding to message: {user_message}")
        with st.chat_message("assistant"):
            # Create container for tool calls
            tool_calls_container = st.empty()
            resp_container = st.empty()
            with st.spinner(":airplane: Coordinating travel planning team..."):
                response = ""
                try:
                    # Run the team and stream the response
                    run_response = await team.arun(user_message, stream=True)
                    async for resp_chunk in run_response:
                        # Display tool calls if available
                        if resp_chunk.tools and len(resp_chunk.tools) > 0:
                            display_tool_calls(tool_calls_container, resp_chunk.tools)

                        # Display response
                        if resp_chunk.content is not None:
                            response += resp_chunk.content
                            resp_container.markdown(response)

                    # Add the response to the messages
                    if team.run_response is not None:
                        await add_message(team_name, "assistant", response, team.run_response.tools)
                    else:
                        await add_message(team_name, "assistant", response)
                except Exception as e:
                    logger.error(f"Error during team run: {str(e)}", exc_info=True)
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    await add_message(team_name, "assistant", error_message)
                    st.error(error_message)


async def main():
    await initialize_team_session_state(team_name)
    await header()
    await body()
    await about_agno()


if __name__ == "__main__":
    if check_password():
        asyncio.run(main())