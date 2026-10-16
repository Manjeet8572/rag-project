from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.graph import rag_graph
from app.ingestion import ingest_documents
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="RAG Technical Assistant", version="1.0.0")

# Startup pe ingest karo agar DB nahi hai
@app.on_event("startup")
def startup_event():
    if not os.path.exists("chroma_db"):
        print("🚀 First time setup: Ingesting documents...")
        ingest_documents()
        print("✅ Setup complete!")

# Request/Response models
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    retry_count: int

class FeedbackRequest(BaseModel):
    query: str
    answer: str
    rating: int  # 1 for thumbs up, -1 for thumbs down
    comment: Optional[str] = None

@app.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    """Main RAG endpoint - yahan sawaal pucho"""
    try:
        print(f"\n❓ Question: {request.question}")
        
        # Graph run karo
        result = rag_graph.invoke({
            "question": request.question,
            "max_retries": 2
        })
        
        # Sources extract karo
        sources = list(set([
            os.path.basename(doc.metadata.get("source", "unknown")) 
            for doc in result["relevant_docs"]
        ]))
        
        print(f"✅ Answer generated with {len(sources)} sources\n")
        
        return QueryResponse(
            answer=result["generation"],
            sources=sources,
            retry_count=result["retry_count"]
        )
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
def ingest_endpoint():
    """Naye documents ingest karo"""
    try:
        ingest_documents()
        return {"message": "Documents ingested successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
def list_documents():
    """Kya-kya indexed hai wo dikhao"""
    if not os.path.exists("data"):
        return {"documents": [], "count": 0}
    
    files = os.listdir("data")
    return {"documents": files, "count": len(files)}

@app.post("/feedback")
def feedback_endpoint(feedback: FeedbackRequest):
    """User feedback save karo"""
    # Simple file mein save karo
    with open("feedback.txt", "a", encoding="utf-8") as f:
        f.write(f"{feedback.rating}|{feedback.query}|{feedback.comment}\n")
    return {"message": "Feedback received, thank you!"}

@app.get("/")
def root():
    """Health check"""
    return {
        "status": "running",
        "message": "RAG Technical Assistant API",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)