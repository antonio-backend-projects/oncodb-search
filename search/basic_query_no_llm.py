import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Carica variabili d'ambiente dal file .env
load_dotenv()
qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "pubmed_articles"  # cambia con il nome della tua collezione

# Inizializza il client Qdrant
client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

def list_points(limit=5):
    # Esegui scroll per ottenere i primi punti con payload
    points, next_page_offset = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=limit,
        with_payload=True
    )

    print(f"Punti trovati: {len(points)}\n")

    for point in points:
        print(f"ID: {point.id}")
        print("Payload:")
        if point.payload:
            for key, value in point.payload.items():
                print(f"  {key}: {value}")
        else:
            print("  Nessun payload disponibile")
        print("-" * 40)

if __name__ == "__main__":
    list_points()