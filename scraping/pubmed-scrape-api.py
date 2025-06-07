import requests
import time
import xml.etree.ElementTree as ET
import json
import os
from dotenv import load_dotenv
import argparse
import logging

load_dotenv()

MAX_RETRIES = 5
BATCH_SIZE = 100

# Logging
logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PubMedDownloader/1.0)"
}


def fetch_pubmed_ids(query, retmax=20000, api_key=None):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    pmids = []
    retstart = 0

    while retstart < retmax:
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": min(BATCH_SIZE, retmax - retstart),
            "retstart": retstart,
            "retmode": "json"
        }
        if api_key:
            params["api_key"] = api_key

        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                response = requests.get(url, params=params, headers=HEADERS)
                response.raise_for_status()
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    logging.error(f"Invalid JSON at retstart={retstart}. Response preview: {response.text[:500]}")
                    raise e

                batch_pmids = data["esearchresult"]["idlist"]
                if not batch_pmids:
                    logging.info("No more PMIDs found.")
                    return pmids

                pmids.extend(batch_pmids)
                retstart += len(batch_pmids)
                print(f"✅ Fetched {len(pmids)} PMIDs so far...")
                logging.info(f"Fetched {len(pmids)} PMIDs so far")
                time.sleep(0.4)
                break
            except Exception as e:
                retry_count += 1
                wait_time = min(60, 5 * (2 ** retry_count))
                logging.warning(f"Error fetching PMIDs ({retry_count}/{MAX_RETRIES}): {e}")
                print(f"⚠️ Retry {retry_count}/{MAX_RETRIES} in {wait_time}s...")
                time.sleep(wait_time)

        if retry_count >= MAX_RETRIES:
            logging.error(f"Max retries reached at retstart={retstart}")
            break

    return pmids


def fetch_pubmed_details(pmids, save_path="pubmed_articles.json", api_key=None):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    articles = []

    if os.path.exists(save_path):
        with open(save_path, "r", encoding="utf-8") as f:
            articles = json.load(f)
        already_fetched_pmids = set(a["pmid"] for a in articles)
    else:
        already_fetched_pmids = set()

    for i in range(0, len(pmids), BATCH_SIZE):
        batch_pmids = pmids[i:i + BATCH_SIZE]
        batch_pmids = [pmid for pmid in batch_pmids if pmid not in already_fetched_pmids]
        if not batch_pmids:
            continue

        params = {
            "db": "pubmed",
            "retmode": "xml",
            "id": ",".join(batch_pmids)
        }
        if api_key:
            params["api_key"] = api_key

        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                response = requests.get(url, params=params, headers=HEADERS)
                response.raise_for_status()
                try:
                    root = ET.fromstring(response.text)
                except ET.ParseError as e:
                    logging.error(f"XML parse error at batch {i}. Response: {response.text[:500]}")
                    raise e

                for article in root.findall(".//PubmedArticle"):
                    art = {}
                    medline = article.find("MedlineCitation")
                    article_data = medline.find("Article")

                    art["title"] = article_data.findtext("ArticleTitle") or ""

                    abstract_text = ""
                    abstract = article_data.find("Abstract")
                    if abstract is not None:
                        abstract_text = " ".join([t.text for t in abstract.findall("AbstractText") if t.text])
                    art["abstract"] = abstract_text

                    authors = []
                    author_list = article_data.find("AuthorList")
                    if author_list is not None:
                        for author in author_list.findall("Author"):
                            last = author.findtext("LastName") or ""
                            first = author.findtext("ForeName") or ""
                            full_name = (first + " " + last).strip()
                            if full_name:
                                authors.append(full_name)
                    art["authors"] = authors

                    pub_date = article_data.find("Journal/JournalIssue/PubDate")
                    year = pub_date.findtext("Year") or ""
                    month = pub_date.findtext("Month") or ""
                    day = pub_date.findtext("Day") or ""
                    art["pub_date"] = f"{year}-{month}-{day}"

                    art["pmid"] = medline.findtext("PMID")

                    articles.append(art)

                logging.info(f"Fetched batch {i // BATCH_SIZE + 1}. Total articles: {len(articles)}")
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(articles, f, ensure_ascii=False, indent=2)
                time.sleep(0.5)
                break
            except Exception as e:
                retry_count += 1
                wait_time = min(60, 5 * (2 ** retry_count))
                logging.warning(f"Error fetching details ({retry_count}/{MAX_RETRIES}): {e}")
                print(f"⚠️ Retry {retry_count}/{MAX_RETRIES} in {wait_time}s...")
                time.sleep(wait_time)

        if retry_count >= MAX_RETRIES:
            logging.error(f"Max retries reached at batch index {i}. Skipping batch.")
            continue

    return articles


def main():
    parser = argparse.ArgumentParser(description="Massive PubMed downloader")
    parser.add_argument("--query", default="cancer immunotherapy clinical trial", help="Search query")
    parser.add_argument("--retmax", type=int, default=20000, help="Max number of records to fetch")
    parser.add_argument("--output", default="pubmed_articles.json", help="Output file path")
    # parser.add_argument("--api_key", help="NCBI API key (optional)")

    args = parser.parse_args()

    api_key = os.getenv("NCBI_API_KEY")
    if not api_key:
        print(f"🔍 API key non trovata")
        api_key = None  # Normalizza stringa vuota in None

    print(f"🔍 Searching PubMed for: \"{args.query}\" (max {args.retmax} results)")
    logging.info(f"Started query: {args.query} with retmax={args.retmax}")

    pmids = fetch_pubmed_ids(args.query, retmax=args.retmax, api_key=api_key)
    print(f"📥 Fetched {len(pmids)} PMIDs. Getting article details...")

    articles = fetch_pubmed_details(pmids, save_path=args.output, api_key=api_key)
    print(f"✅ Done. Saved {len(articles)} articles to {args.output}")
    logging.info(f"Completed. Saved {len(articles)} articles.")


if __name__ == "__main__":
    main()
