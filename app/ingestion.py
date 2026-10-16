from hashlib import sha256
import os

from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()


def ingest_documents(data_dir="data", persist_dir="chroma_db", file_paths=None):
    """Markdown/text files load karke ChromaDB mein index karo."""

    os.makedirs(data_dir, exist_ok=True)

    # Koi particular file na di ho to data folder ki sabhi supported files lo
    if file_paths is None:
        file_paths = [
            os.path.join(data_dir, name)
            for name in os.listdir(data_dir)
            if name.lower().endswith((".md", ".txt"))
        ]

    documents = []
    for path in file_paths:
        if not path.lower().endswith((".md", ".txt")):
            continue

        loader = TextLoader(path, encoding="utf-8")
        documents.extend(loader.load())

    if not documents:
        raise ValueError("Index karne ke liye koi .md ya .txt document nahi mila.")

    print(f"📚 Loaded {len(documents)} documents")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = text_splitter.split_documents(documents)
    print(f"✂️ Created {len(chunks)} chunks")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )

    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
    )

    # Same file ko dobara bhejne par uske chunks ki pehchaan stable rahe
    ids = []
    for index, chunk in enumerate(chunks):
        source = chunk.metadata.get("source", "")
        unique_text = f"{source}|{index}|{chunk.page_content}"
        ids.append(sha256(unique_text.encode("utf-8")).hexdigest())

    vectorstore.add_documents(documents=chunks, ids=ids)
    print("💾 Documents ingested successfully!")
    return vectorstore


if __name__ == "__main__":
    ingest_documents()