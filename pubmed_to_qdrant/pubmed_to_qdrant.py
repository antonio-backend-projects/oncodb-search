import os
import json
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from dotenv import load_dotenv

load_dotenv()

# Inizializza modello embedding
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Inizializza client Qdrant (default localhost)
qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
qdrant_api_key = os.getenv("QDRANT_API_KEY", None)
client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

COLLECTION_NAME = "pubmed_articles"

def create_collection_if_not_exists():
    try:
        client.get_collection(COLLECTION_NAME)
        print(f"Collection '{COLLECTION_NAME}' esiste già.")
    except:
        print(f"Creazione collection '{COLLECTION_NAME}'...")
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={"size": 384, "distance": "Cosine"},
        )

def load_articles(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_embedding(text):
    return model.encode(text).tolist()

def clean_pub_date(pub_date: str) -> str:
    # Rimuove trattini finali e spazi inutili
    if pub_date:
        pub_date = pub_date.strip()
        if pub_date.endswith("-"):
            pub_date = pub_date.rstrip("-").strip()
    return pub_date

def prepare_points(articles):
    points = []
    for art in articles:
        # Concateno titolo + abstract
        text = f"{art.get('title','')} {art.get('abstract','')}"
        embedding = generate_embedding(text)

        # Pulizia della data
        pub_date = clean_pub_date(art.get("pub_date", ""))

        payload = {
            "title": art.get("title", ""),
            "abstract": art.get("abstract", ""),
            "pmid": art.get("pmid", ""),
            "authors": art.get("authors", []),
            "pub_date": pub_date
        }

        # Usa pmid come int, fallback a id incrementale se pmid non è convertibile
        try:
            point_id = int(art.get("pmid"))
        except (ValueError, TypeError):
            # fallback a hash o id alternativo
            point_id = hash(art.get("pmid"))

        point = PointStruct(id=point_id, vector=embedding, payload=payload)
        points.append(point)
    return points

def upload_to_qdrant(points):
    print(f"Caricamento di {len(points)} punti su Qdrant...")
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i+batch_size]
        client.upsert(collection_name=COLLECTION_NAME, points=batch)
        print(f" - Caricati {i + len(batch)} / {len(points)}")

def main():
    create_collection_if_not_exists()

    articles = load_articles("pubmed_articles.json")  # Il tuo file JSON di articoli
    points = prepare_points(articles)
    upload_to_qdrant(points)
    print("✅ Upload completato.")

if __name__ == "__main__":
    main()
