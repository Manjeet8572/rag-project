from langgraph.graph import StateGraph, END
from app.state import GraphState
from app.nodes import (
    query_analysis_node, 
    retrieval_node, 
    grading_node, 
    generation_node,
    rewrite_query_node
)

def should_continue(state: GraphState) -> str:
    """Decide karo aage kya karna hai"""
    if state["relevant_docs"]:
        return "generate"
    elif state["retry_count"] < state["max_retries"]:
        return "rewrite"
    else:
        return "generate"

def build_graph():
    workflow = StateGraph(GraphState)
    
    # Nodes add karo
    workflow.add_node("analyze", query_analysis_node)
    workflow.add_node("retrieve", retrieval_node)
    workflow.add_node("grade", grading_node)
    workflow.add_node("generate", generation_node)
    workflow.add_node("rewrite", rewrite_query_node)
    
    # Flow define karo
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "retrieve")
    workflow.add_edge("retrieve", "grade")
    
    # Conditional edge (self-corrective loop)
    workflow.add_conditional_edges(
        "grade",
        should_continue,
        {
            "generate": "generate",
            "rewrite": "rewrite"
        }
    )
    
    workflow.add_edge("rewrite", "retrieve")  # Loop back
    workflow.add_edge("generate", END)
    
    return workflow.compile()

# Global instance
rag_graph = build_graph()