from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import Chroma
from app.state import GraphState
import os
from dotenv import load_dotenv

load_dotenv()

# Gemini LLM (FREE)
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0)

# Gemini Embeddings (ONLINE - kuch download nahi hota!)
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

def query_analysis_node(state: GraphState) -> GraphState:
    """User ke sawaal ko improve karo"""
    print("🔍 Analyzing query...")
    
    prompt = ChatPromptTemplate.from_template(
        """Rewrite the question to be more specific for technical documentation search.
        Keep it under 20 words.
        
        Question: {question}
        Rewritten:"""
    )
    
    chain = prompt | llm | StrOutputParser()
    state["rewritten_question"] = chain.invoke({"question": state["question"]}).strip()
    state["retry_count"] = 0
    return state

def retrieval_node(state: GraphState) -> GraphState:
    """Vector store se relevant chunks nikalo"""
    print("📚 Retrieving documents...")
    
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    
    docs = retriever.invoke(state["rewritten_question"])
    state["documents"] = docs
    print(f"   Found {len(docs)} documents")
    return state

def grading_node(state: GraphState) -> GraphState:
    """Check karo ki documents relevant hain kya"""
    print("⚖️  Grading documents...")
    
    prompt = ChatPromptTemplate.from_template(
        """Is this document relevant to the question? Answer only 'yes' or 'no'.
        
        Question: {question}
        Document: {document}
        
        Answer:"""
    )
    
    chain = prompt | llm | StrOutputParser()
    
    relevant_docs = []
    for doc in state["documents"]:
        result = chain.invoke({
            "question": state["question"],
            "document": doc.page_content[:500]
        })
        
        if "yes" in result.lower():
            relevant_docs.append(doc)
            print(f"   ✅ Relevant")
        else:
            print(f"   ❌ Irrelevant")
    
    state["relevant_docs"] = relevant_docs
    return state

def generation_node(state: GraphState) -> GraphState:
    """Answer banao with citations"""
    print("✍️  Generating answer...")
    
    if not state["relevant_docs"]:
        state["generation"] = "I don't have enough relevant information to answer this question."
        return state
    
    context_texts = []
    for i, doc in enumerate(state["relevant_docs"], 1):
        source = os.path.basename(doc.metadata.get("source", f"Doc {i}"))
        context_texts.append(f"[Source {i}: {source}]\n{doc.page_content}")
    
    context = "\n\n".join(context_texts)
    
    prompt = ChatPromptTemplate.from_template(
        """Answer based ONLY on the context. Cite sources using [Source X].
        
        Context:
        {context}
        
        Question: {question}
        
        Answer:"""
    )
    
    chain = prompt | llm | StrOutputParser()
    state["generation"] = chain.invoke({
        "context": context,
        "question": state["question"]
    })
    return state

def rewrite_query_node(state: GraphState) -> GraphState:
    """Query rewrite karo agar relevant docs nahi mile"""
    print("🔄 Rewriting query...")
    
    state["retry_count"] += 1
    
    prompt = ChatPromptTemplate.from_template(
        """Rewrite using different keywords or broader terms.
        Original: {question}
        Rewritten:"""
    )
    
    chain = prompt | llm | StrOutputParser()
    state["rewritten_question"] = chain.invoke({"question": state["question"]}).strip()
    return state