from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
import operator
import json
import logging

logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

@tool
def predict_churn(customer_email: str, recent_reviews: list | None = None) -> float:
    """Predict customer churn probability using LLM + heuristic analysis."""
    review_context = f"Recent reviews: {json.dumps(recent_reviews)}" if recent_reviews else "No recent reviews"
    
    prompt = f"""Analyze the following customer data and predict churn probability (0.0 to 1.0):
Customer: {customer_email}
{review_context}

Consider: review sentiment, booking frequency, time since last booking, rating trends.
Return only a number between 0.0 and 1.0."""

    try:
        response = llm.invoke([SystemMessage(content="You are a churn prediction analyst. Return only a number."), HumanMessage(content=prompt)])
        churn_score = float(response.content.strip())
        return max(0.0, min(1.0, churn_score))
    except Exception as e:
        logger.warning(f"Churn prediction failed, using heuristic: {e}")
        # Heuristic fallback
        base_score = 0.3
        if recent_reviews:
            avg_rating = sum(r.get("rating", 3) for r in recent_reviews) / len(recent_reviews)
            base_score += (3 - avg_rating) * 0.15
        return max(0.0, min(1.0, base_score))

@tool
def get_booking_recommendations(service_type: str, state: str, property_type: str = "residential") -> dict:
    """Get AI-powered booking recommendations based on customer profile."""
    recommendations = {
        "add_ons": [],
        "frequency": "one-time",
        "estimated_duration": 120,
    }
    
    if service_type in ["end-of-lease", "deep"]:
        recommendations["add_ons"] = ["carpet-clean", "window-clean", "oven-clean"]
        recommendations["estimated_duration"] = 240
    
    if property_type == "commercial":
        recommendations["frequency"] = "weekly"
        recommendations["add_ons"].append("sanitisation")
    
    if state in ["NSW", "VIC"]:
        recommendations["add_ons"].append("strata-compliance-check")
    
    return recommendations

@tool
def get_pricing_info(service_type: str, bedrooms: int = 1, bathrooms: int = 1, state: str = "NSW") -> dict:
    """Get transparent pricing breakdown with GST."""
    base_rates = {
        "regular": 89,
        "deep": 179,
        "end-of-lease": 229,
        "carpet": 149,
        "window": 119,
        "strata": 199,
    }
    
    base = base_rates.get(service_type, 89)
    bedroom_adj = max(0, bedrooms - 1) * 25
    bathroom_adj = max(0, bathrooms - 1) * 30
    subtotal = base + bedroom_adj + bathroom_adj
    gst = subtotal * 0.10
    total = subtotal + gst
    
    return {
        "base_price": base,
        "bedroom_adjustment": bedroom_adj,
        "bathroom_adjustment": bathroom_adj,
        "subtotal": round(subtotal, 2),
        "gst_10_percent": round(gst, 2),
        "total_incl_gst": round(total, 2),
        "currency": "AUD",
    }

# LangGraph state
class AgentState(TypedDict):
    messages: Annotated[Sequence, operator.add]
    tools_output: list
    final_response: str

# Graph nodes
def agent_node(state: AgentState) -> dict:
    """LLM decides which tools to call."""
    messages = state["messages"]
    tools = [predict_churn, get_booking_recommendations, get_pricing_info]
    llm_with_tools = llm.bind_tools(tools)
    response = llm_with_tools.invoke(messages)
    return {"messages": [response], "tools_output": response.tool_calls if response.tool_calls else []}

def tools_node(state: AgentState) -> dict:
    """Execute tool calls."""
    tools_map = {
        "predict_churn": predict_churn,
        "get_booking_recommendations": get_booking_recommendations,
        "get_pricing_info": get_pricing_info,
    }
    
    results = []
    for tool_call in state.get("tools_output", []):
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_fn = tools_map.get(tool_name)
        if tool_fn:
            try:
                result = tool_fn.invoke(tool_args)
                results.append({"tool": tool_name, "result": result})
            except Exception as e:
                results.append({"tool": tool_name, "error": str(e)})
    
    return {"tools_output": results}

def response_node(state: AgentState) -> dict:
    """Generate final response."""
    messages = state["messages"]
    tool_results = state.get("tools_output", [])
    
    if tool_results:
        context = "\n".join(json.dumps(r) for r in tool_results)
        messages.append(HumanMessage(content=f"Tool results: {context}. Summarize for the customer."))
    
    response = llm.invoke(messages)
    return {"final_response": response.content}

# Build graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tools_node)
workflow.add_node("response", response_node)

workflow.set_entry_point("agent")

def route_agent(state: AgentState) -> str:
    if state.get("tools_output"):
        return "tools"
    return "response"

workflow.add_conditional_edges("agent", route_agent, {"tools": "tools", "response": "response"})
workflow.add_edge("tools", "response")
workflow.add_edge("response", END)

graph = workflow.compile()
