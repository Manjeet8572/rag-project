from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from app.graph import rag_graph
from app.ingestion import ingest_documents
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="RAG Technical Assistant", version="1.0.0")


# Pehli baar app start hone par data folder ke documents index karo
@app.on_event("startup")
def startup_event():
    if not os.path.exists("chroma_db"):
        print("First time setup: Ingesting documents...")
        ingest_documents()
        print("Setup complete!")


# Request/response models
class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    retry_count: int


class FeedbackRequest(BaseModel):
    query: str
    answer: str
    rating: int  # 1 = thumbs up, -1 = thumbs down
    comment: Optional[str] = None


@app.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    """Sawaal ka jawab aur sources do."""
    try:
        print(f"\nQuestion: {request.question}")

        result = rag_graph.invoke({
            "question": request.question,
            "max_retries": 2,
        })

        sources = list(set(
            os.path.basename(doc.metadata.get("source", "unknown"))
            for doc in result["relevant_docs"]
        ))

        return QueryResponse(
            answer=result["generation"],
            sources=sources,
            retry_count=result["retry_count"],
        )

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest")
async def ingest_endpoint(file: UploadFile = File(...)):
    """Ek Markdown ya text file upload karke index karo."""
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)

    filename = os.path.basename(file.filename or "")

    if not filename.lower().endswith((".md", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Sirf .md ya .txt file upload karo",
        )

    try:
        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="File khaali hai",
            )

        file_path = os.path.join(data_dir, filename)

        with open(file_path, "wb") as output_file:
            output_file.write(content)

        await file.close()

        ingest_documents(file_paths=[file_path])

        return {
            "message": "Document ingested successfully",
            "file": filename,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
def list_documents():
    """Data folder mein maujood documents dikhao."""
    if not os.path.exists("data"):
        return {"documents": [], "count": 0}

    files = [
        name
        for name in os.listdir("data")
        if name.lower().endswith((".md", ".txt"))
    ]

    return {"documents": files, "count": len(files)}


@app.post("/feedback")
def feedback_endpoint(feedback: FeedbackRequest):
    """User ka feedback file mein save karo."""
    with open("feedback.txt", "a", encoding="utf-8") as f:
        f.write(
            f"{feedback.rating}|{feedback.query}|"
            f"{feedback.comment or ''}\n"
        )

    return {"message": "Feedback received, thank you!"}


@app.get("/")
def root():
    """Check karo ki API chal rahi hai."""
    return {
        "status": "running",
        "message": "RAG Technical Assistant API",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)