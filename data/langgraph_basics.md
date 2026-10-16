# LangGraph Basics

LangGraph workflows are made of nodes and edges. A node is a function that reads the current state and returns updates. Edges decide which node runs next.

A StateGraph uses a shared state schema to pass information between nodes. For a RAG assistant, the state can contain the user's question, retrieved documents, the generated answer, and a retry count.

A conditional edge can check whether retrieved documents are relevant. If they are relevant, the graph proceeds to answer generation. If not, it can rewrite the question and try retrieval again, subject to a retry limit.