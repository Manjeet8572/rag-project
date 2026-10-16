from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
import os
from dotenv import load_dotenv

load_dotenv()

def ingest_documents(data_dir="data", persist_dir="chroma_db"):
    """Documents load karo, split karo, embeddings banao (ONLINE)"""
    
    # 1. Load documents
    documents = []
    for file in os.listdir(data_dir):
        if file.endswith(".md"):
            loader = TextLoader(os.path.join(data_dir, file), encoding="utf-8")
            documents.extend(loader.load())
    
    print(f"📚 Loaded {len(documents)} documents")
    
    # 2. Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"✂️ Created {len(chunks)} chunks")
    
    # 3. Use Gemini embeddings (ONLINE - no download!)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # 4. Store in ChromaDB
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir
    )
    vectorstore.persist()
    print("💾 Documents ingested successfully!")
    return vectorstore

if __name__ == "__main__":
    ingest_documents()