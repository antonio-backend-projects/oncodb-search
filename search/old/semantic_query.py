import os
from dotenv import load_dotenv

from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

load_dotenv()
qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
# definizione vettorial store
vectorstore = QdrantVectorStore(
    client=client,
    collection_name="pubmed_articles",
    embedding=embedding_model,
)

# definizione retriever con with_payload True
retriever = vectorstore.as_retriever(search_kwargs={"k": 5, "with_payload": True})

# definizione modello linguistico LLM
llm = ChatOpenAI(openai_api_key=openai_api_key, temperature=0.2)

# definizione catena QA
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True,
)
def run_query(question: str):
    print(f"\n🧠 Domanda: {question}")
    result = qa_chain.invoke({"query": question})

    print("\n📋 Risposta generata:")
    print(result["result"])

    print("\n📚 Articoli correlati:\n")
    for doc in result["source_documents"]:
        print("DEBUG document:", doc)
        print("DEBUG metadata:", doc.metadata)
        
        meta = doc.metadata or {}
        title = meta.get("title", "Non disponibile")
        abstract = meta.get("abstract", "Non disponibile")
        pmid = meta.get("pmid", "Non disponibile")
        authors = meta.get("authors", "Non disponibile")
        pub_date = meta.get("pub_date", "Non disponibile")

        # Se authors è lista, convertila in stringa
        if isinstance(authors, list):
            authors = ", ".join(authors)

        print(f"- 📌 Titolo: {title}")
        print(f"  📝 Abstract: {abstract}")
        print(f"  🧾 PMID: {pmid}")
        print(f"  👩‍⚕️ Autori: {authors}")
        print(f"  📅 Data: {pub_date}\n")


if __name__ == "__main__":
    domanda = input("🤖 Inserisci la tua domanda (es. quali sono le nuove terapie per il cancro al colon?):\n> ")
    run_query(domanda)
