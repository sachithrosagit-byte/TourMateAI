from langgraph.graph import StateGraph, START, END
from .state import PlannerState
from .agents import context_agent, intent_agent, discovery_agent, scheduler_agent, routing_agent

def create_planner_graph():
    """Builds and returns the compiled LangGraph for itinerary generation."""
    workflow = StateGraph(PlannerState)
    
    # Add nodes
    workflow.add_node("context", context_agent)
    workflow.add_node("intent", intent_agent)
    workflow.add_node("discovery", discovery_agent)
    workflow.add_node("scheduler", scheduler_agent)
    workflow.add_node("routing", routing_agent)
    
    # Define edges
    workflow.add_edge(START, "context")
    workflow.add_edge("context", "intent")
    workflow.add_edge("intent", "discovery")
    workflow.add_edge("discovery", "scheduler")
    workflow.add_edge("scheduler", "routing")
    workflow.add_edge("routing", END)
    
    return workflow.compile()

# Instantiate the graph
planner_graph = create_planner_graph()

def generate_itinerary(start_date: str, end_date: str, preferences: dict) -> list:
    """Convenience function to run the graph and return the generated items."""
    initial_state = {
        "start_date": start_date,
        "end_date": end_date,
        "preferences": preferences,
        "weather_context": {},
        "candidate_attractions": [],
        "itinerary_items": [],
        "messages": []
    }
    
    final_state = planner_graph.invoke(initial_state)
    return final_state.get("itinerary_items", [])
