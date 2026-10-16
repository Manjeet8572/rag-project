from typing import List, TypedDict
from langchain_core.documents import Document

class GraphState(TypedDict):
    """Ye dictionary graph ke har node ke beech ghoomti hai"""
    question: str           # User ka original sawaal
    rewritten_question: str # Improved sawaal
    documents: List[Document]  # Retrieved chunks (raw)
    relevant_docs: List[Document]  # Grading ke baad jo relevant hain
    generation: str         # Final answer
    retry_count: int        # Kitni baar retry kiya
    max_retries: int        # Maximum retry limit