import os
from dotenv import load_dotenv
from langchain.vectorstores import Qdrant
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from qdrant_client import QdrantClient

# Carica variabili d’ambiente
load_dotenv()
qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Modello embedding HuggingFace (MiniLM)
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Client Qdrant
client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

# Costruzione vector store LangChain
vectorstore = Qdrant(
    client=client,
    collection_name="pubmed_articles",
    embeddings=embedding_model,
)

# LLM OpenAI
llm = ChatOpenAI(openai_api_key=openai_api_key, temperature=0.2)

# RetrievalQA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True
)

def run_query(question: str):
    print(f"\n🧠 Domanda: {question}")
    result = qa_chain(question)

    print("\n📋 Risposta generata:")
    print(result["result"])

    print("\n📚 Articoli correlati:")
    for doc in result["source_documents"]:
        payload = doc.metadata
        print(f"\n- 📌 Titolo: {payload.get('title')}")
        print(f"  📝 Abstract: {payload.get('abstract')[:300]}...")
        print(f"  🧾 PMID: {payload.get('pmid')}")
        print(f"  📅 Data: {payload.get('pub_date')}\n")

if __name__ == "__main__":
    domanda = input("🤖 Inserisci la tua domanda (es. quali sono le nuove terapie per il cancro al colon?):\n> ")
    run_query(domanda)
