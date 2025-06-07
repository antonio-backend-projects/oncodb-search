import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from langchain.schema import Document
from langchain.chat_models import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain
from langchain.embeddings import HuggingFaceEmbeddings  # o OpenAIEmbeddings
from langchain.vectorstores import Qdrant

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "pubmed_articles"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Usa modello embedding per trasformare testo in vettore
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def search_qdrant(question, limit=5):
    query_vector = embedding_model.embed_query(question)
    search_result = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=limit,
        with_payload=True
    )
    return search_result

def build_documents_from_payload(results):
    docs = []
    for point in results:
        payload = point.payload or {}
        content_parts = []
        if "title" in payload:
            content_parts.append(payload["title"])
        if "abstract" in payload:
            content_parts.append(payload["abstract"])
        content = "\n\n".join(content_parts).strip()
        if content:
            docs.append(Document(page_content=content, metadata=payload))
    return docs

def generate_answer(docs, question):
    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0)
    qa_chain = load_qa_chain(llm, chain_type="stuff")

    # Stampa di debug: mostra contenuti dei documenti prima di generare la risposta
    print(f"Trovati {len(docs)} documenti:")
    for i, doc in enumerate(docs, 1):
        print(f"\nDocumento {i} (prime 500 caratteri):")
        print(doc.page_content[:500] + "...\n")

    answer = qa_chain.run(input_documents=docs, question=question)
    return answer

if __name__ == "__main__":
    question = input("Inserisci la tua domanda:\n> ")
    results = search_qdrant(question)
    docs = build_documents_from_payload(results)

    if not docs:
        print("Nessun documento rilevante trovato.")
    else:
        answer = generate_answer(docs, question)
        print("\nRisposta generata:\n", answer)
